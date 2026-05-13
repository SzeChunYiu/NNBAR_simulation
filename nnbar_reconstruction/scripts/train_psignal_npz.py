#!/usr/bin/env python3
"""
NNBAR P-Signal Classifier Training (NPZ Format)

Train the P-Signal classifier using data prepared by prepare_training_data.py.

Usage:
    python train_psignal_npz.py \\
        --train_data training_data/psignal_train.npz \\
        --val_data training_data/psignal_val.npz \\
        --save_dir models/psignal

Author: NNBAR Collaboration
Date: 2026-01-12
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# Enable performance optimizations
torch.backends.cudnn.benchmark = True
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.vertex.psignal_model import (
    PointNetMini,
    TrackGNN,
    normalize_hits,
    HAS_TORCH_GEOMETRIC,
)


class NPZTrackDataset(Dataset):
    """Dataset for P-Signal training from NPZ files."""

    def __init__(self, npz_path: str, min_hits: int = 5):
        """Load training data from NPZ file."""
        data = np.load(npz_path, allow_pickle=True)

        self.hits_list = data['hits']
        self.labels = data['labels']
        self.metadata = json.loads(str(data['metadata']))

        # Filter by minimum hits
        self.samples = []
        for i, (hits, label) in enumerate(zip(self.hits_list, self.labels)):
            if len(hits) >= min_hits:
                # Normalize hits
                hits_norm = normalize_hits(hits.astype(np.float32), mode='center_rms')
                self.samples.append((hits_norm, float(label)))

        print(f"[dataset] Loaded {len(self.samples)} samples from {npz_path}")

        # Statistics
        labels = [y for _, y in self.samples]
        n_pos = sum(y > 0.5 for y in labels)
        n_neg = len(labels) - n_pos
        print(f"  Signal: {n_pos} ({n_pos/len(labels)*100:.1f}%)")
        print(f"  Background: {n_neg} ({n_neg/len(labels)*100:.1f}%)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def collate_pointnet(batch: List[Tuple[np.ndarray, float]]) -> dict:
    """Collate for PointNet: pad to max length."""
    B = len(batch)
    lens = [b[0].shape[0] for b in batch]
    Nmax = max(lens)

    X = torch.zeros(B, Nmax, 3, dtype=torch.float32)
    M = torch.zeros(B, Nmax, dtype=torch.bool)
    y = torch.zeros(B, dtype=torch.float32)

    for i, (H, label) in enumerate(batch):
        n = H.shape[0]
        X[i, :n] = torch.from_numpy(H)
        M[i, :n] = True
        y[i] = label

    return {"X": X, "M": M, "y": y}


def compute_class_weights(dataset: NPZTrackDataset) -> Optional[float]:
    """Compute positive class weight for imbalanced data."""
    labels = [y for _, y in dataset.samples]
    if not labels:
        return None

    labels = np.array(labels)
    n_pos = np.sum(labels > 0.5)
    n_neg = np.sum(labels <= 0.5)

    if n_pos == 0 or n_neg == 0:
        return None

    pos_weight = n_neg / n_pos
    print(f"[class weight] pos_weight={pos_weight:.2f}")
    return pos_weight


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    scaler=None,
    pos_weight: Optional[float] = None,
) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    n_samples = 0

    pw = torch.tensor([pos_weight], device=device) if pos_weight is not None else None

    for batch in loader:
        X = batch["X"].to(device)
        M = batch["M"].to(device)
        y = batch["y"].to(device)

        optimizer.zero_grad()
        with torch.cuda.amp.autocast(enabled=scaler is not None):
            logits = model(X, M)
            if pw is not None:
                loss = F.binary_cross_entropy_with_logits(
                    logits, y, pos_weight=pw.expand_as(logits)
                )
            else:
                loss = F.binary_cross_entropy_with_logits(logits, y)

        if scaler is not None:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        total_loss += loss.item() * len(y)
        n_samples += len(y)

    return total_loss / max(1, n_samples)


@torch.no_grad()
def eval_epoch(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> Tuple[float, float, float, float]:
    """Evaluate for one epoch. Returns loss, accuracy, precision, recall."""
    model.eval()
    total_loss = 0.0
    n_samples = 0
    all_probs = []
    all_labels = []

    for batch in loader:
        X = batch["X"].to(device)
        M = batch["M"].to(device)
        y = batch["y"].to(device)
        logits = model(X, M)

        loss = F.binary_cross_entropy_with_logits(logits, y)
        total_loss += loss.item() * len(y)
        n_samples += len(y)

        probs = torch.sigmoid(logits).cpu().numpy()
        all_probs.extend(probs)
        all_labels.extend(y.cpu().numpy())

    # Metrics at threshold 0.5
    all_probs = np.array(all_probs)
    all_labels = np.array(all_labels)
    preds = (all_probs > 0.5).astype(float)
    labels_binary = (all_labels > 0.5).astype(float)

    accuracy = (preds == labels_binary).mean()

    # Precision and recall for signal class
    tp = ((preds == 1) & (labels_binary == 1)).sum()
    fp = ((preds == 1) & (labels_binary == 0)).sum()
    fn = ((preds == 0) & (labels_binary == 1)).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    return total_loss / max(1, n_samples), accuracy, precision, recall


def main():
    parser = argparse.ArgumentParser(description="Train NNBAR P-Signal Classifier")

    # Data
    parser.add_argument("--train_data", required=True, help="Training NPZ file")
    parser.add_argument("--val_data", default=None, help="Validation NPZ file")
    parser.add_argument("--min_hits", type=int, default=5, help="Minimum hits per track")

    # Model
    parser.add_argument("--hidden", type=int, default=64, help="Hidden dimension")
    parser.add_argument("--emb", type=int, default=128, help="Embedding dimension")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")

    # Training
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=15, help="Early stopping patience")

    # Output
    parser.add_argument("--save_dir", required=True, help="Output directory")

    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[device] {device}")

    # Load data
    print("\n" + "=" * 60)
    print("Loading training data...")
    ds_train = NPZTrackDataset(args.train_data, min_hits=args.min_hits)

    if len(ds_train) == 0:
        print("[fatal] No usable tracks found")
        sys.exit(1)

    dl_train = DataLoader(
        ds_train,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=2,
        collate_fn=collate_pointnet,
        pin_memory=True,
    )

    # Validation data
    dl_val = None
    if args.val_data:
        print("\nLoading validation data...")
        ds_val = NPZTrackDataset(args.val_data, min_hits=args.min_hits)
        if len(ds_val) > 0:
            dl_val = DataLoader(
                ds_val,
                batch_size=args.batch_size,
                shuffle=False,
                num_workers=2,
                collate_fn=collate_pointnet,
                pin_memory=True,
            )

    # Create model
    model = PointNetMini(hidden=args.hidden, emb=args.emb, dropout=args.dropout)
    model = model.to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n[model] PointNetMini with {n_params:,} trainable parameters")

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.cuda.amp.GradScaler(enabled=torch.cuda.is_available())

    # Class weights
    pos_weight = compute_class_weights(ds_train)

    # Training
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    best_loss = math.inf
    best_path = save_dir / "best.ckpt"
    patience_counter = 0

    print(f"\n{'=' * 60}")
    print(f"Training for {args.epochs} epochs")
    print(f"{'=' * 60}\n")

    history = {"train_loss": [], "val_loss": [], "val_acc": [], "val_prec": [], "val_recall": []}

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        train_loss = train_epoch(model, dl_train, optimizer, device, scaler, pos_weight)
        history["train_loss"].append(train_loss)

        msg = f"[epoch {epoch:3d}/{args.epochs}] train_bce={train_loss:.4f}"

        if dl_val is not None:
            val_loss, val_acc, val_prec, val_recall = eval_epoch(model, dl_val, device)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)
            history["val_prec"].append(val_prec)
            history["val_recall"].append(val_recall)

            msg += f"  val_bce={val_loss:.4f}  acc={val_acc:.3f}  prec={val_prec:.3f}  rec={val_recall:.3f}"
            metric = val_loss
        else:
            metric = train_loss

        scheduler.step()

        # Save best
        if metric < best_loss - 1e-6:
            best_loss = metric
            patience_counter = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model": model.state_dict(),
                    "hidden": args.hidden,
                    "emb": args.emb,
                    "dropout": args.dropout,
                    "val_loss": val_loss if dl_val else None,
                    "val_acc": val_acc if dl_val else None,
                },
                best_path,
            )
            msg += " *"
        else:
            patience_counter += 1

        print(msg + f"  ({time.time() - t0:.1f}s)")

        # Early stopping
        if patience_counter >= args.patience:
            print(f"\n[early stopping] No improvement for {args.patience} epochs")
            break

    # Save final checkpoint
    torch.save(
        {
            "epoch": epoch,
            "model": model.state_dict(),
            "hidden": args.hidden,
            "emb": args.emb,
            "dropout": args.dropout,
        },
        save_dir / "last.ckpt",
    )

    # Save config and history
    with open(save_dir / "train_config.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    with open(save_dir / "history.json", "w") as f:
        json.dump(history, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Training complete!")
    print(f"Best checkpoint: {best_path}")
    print(f"Best val loss: {best_loss:.4f}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
