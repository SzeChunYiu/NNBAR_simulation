#!/usr/bin/env python3
"""
NNBAR P-Signal Classifier Training

Train a track signal classifier to distinguish signal tracks (from annihilation)
from Compton scatters and background tracks.

Models available:
- PointNet (--model pointnet): Fast, simple, good for linear tracks
- GNN (--model gnn): Captures local geometry, better for complex tracks

Usage:
    python train_psignal.py \\
        --data_dir ./clustering_output/ \\
        --save_dir ./psignal_model/ \\
        --model pointnet --epochs 30

Author: NNBAR Collaboration
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd

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
    build_knn_graph,
    HAS_TORCH_GEOMETRIC,
)

# Optional torch_geometric
try:
    from torch_geometric.data import Data, Batch
except ImportError:
    pass


# ============================================================================
# Dataset
# ============================================================================

def discover_candidates(data_root: Path) -> List[Path]:
    """Find all candidates.parquet files under data_root."""
    data_root = Path(data_root).resolve()
    all_files = sorted(data_root.rglob("candidates.parquet"))

    if not all_files:
        # Also check for track files with different naming
        all_files = sorted(data_root.rglob("tracks*.parquet"))

    if not all_files:
        print(f"[warn] No candidates/tracks files found under {data_root}")
    else:
        print(f"[discover] Found {len(all_files)} file(s):")
        for p in all_files[:5]:
            print(f"    {p.relative_to(data_root)}")
        if len(all_files) > 5:
            print(f"    ... and {len(all_files) - 5} more")

    return all_files


def to_numpy_1d(v):
    """Convert to 1D numpy array."""
    if isinstance(v, np.ndarray):
        return v.astype(np.float32, copy=False)
    try:
        arr = np.asarray(v, dtype=np.float32)
        if arr.ndim == 0:
            if hasattr(v, "to_pylist"):
                return np.asarray(v.to_pylist(), dtype=np.float32)
            return None
        return arr
    except Exception:
        if hasattr(v, "to_pylist"):
            try:
                return np.asarray(v.to_pylist(), dtype=np.float32)
            except Exception:
                return None
        return None


def row_to_hits(row) -> Optional[np.ndarray]:
    """Extract hits (N, 3) from a DataFrame row."""
    # Try different column naming conventions
    key_sets = [
        ("hits_x", "hits_y", "hits_z"),
        ("x", "y", "z"),
        ("hit_x", "hit_y", "hit_z"),
    ]

    for keys in key_sets:
        if all(k in row for k in keys):
            hx = to_numpy_1d(row[keys[0]])
            hy = to_numpy_1d(row[keys[1]])
            hz = to_numpy_1d(row[keys[2]])

            if hx is None or hy is None or hz is None:
                continue

            n = min(len(hx), len(hy), len(hz))
            if n < 2:
                continue

            return np.stack([hx[:n], hy[:n], hz[:n]], axis=1)

    return None


class TrackDataset(Dataset):
    """Dataset for P-Signal training."""

    def __init__(
        self,
        data_root: Path,
        limit: Optional[int] = None,
        label_column: str = "frac_signal",
    ):
        """
        Args:
            data_root: Root directory with parquet files
            limit: Maximum number of samples
            label_column: Column name for signal fraction label
        """
        all_paths = discover_candidates(data_root)

        self.samples = []
        total_rows = 0
        rejected = {"no_label": 0, "bad_hits": 0}

        for path in all_paths:
            try:
                df = pd.read_parquet(path)
            except Exception as e:
                print(f"[warn] Failed to read {path}: {e}")
                continue

            total_rows += len(df)

            for _, row in df.iterrows():
                # Check for label
                if label_column not in row or pd.isna(row[label_column]):
                    rejected["no_label"] += 1
                    continue

                # Extract hits
                H = row_to_hits(row)
                if H is None:
                    rejected["bad_hits"] += 1
                    continue

                # Normalize
                H = normalize_hits(H, "center_rms")

                # Label
                y = float(row[label_column])

                self.samples.append((H, y))

        if limit is not None and len(self.samples) > limit:
            np.random.shuffle(self.samples)
            self.samples = self.samples[:limit]

        print(f"[dataset] usable={len(self.samples)} / scanned={total_rows}")
        if rejected["no_label"] > 0 or rejected["bad_hits"] > 0:
            print(f"[rejected] no_label={rejected['no_label']}, bad_hits={rejected['bad_hits']}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


# ============================================================================
# Collate Functions
# ============================================================================

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

    return {"X": X, "M": M, "y": y, "model_type": "pointnet"}


def collate_gnn(batch: List[Tuple[np.ndarray, float]], k_neighbors: int = 8) -> dict:
    """Collate for GNN: build graphs and batch."""
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError("torch_geometric required for GNN model")

    data_list = []
    labels = []

    for H, label in batch:
        edge_index = build_knn_graph(H, k=k_neighbors)
        data = Data(
            x=torch.from_numpy(H),
            edge_index=torch.from_numpy(edge_index),
        )
        data_list.append(data)
        labels.append(label)

    batched = Batch.from_data_list(data_list)
    batched.y = torch.tensor(labels, dtype=torch.float32)

    return {"data": batched, "y": batched.y, "model_type": "gnn"}


# ============================================================================
# Training
# ============================================================================

def compute_class_weights(dataset: TrackDataset) -> Optional[float]:
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
    print(f"[class balance] pos={n_pos}, neg={n_neg}, pos_weight={pos_weight:.2f}")
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
        if batch["model_type"] == "pointnet":
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
        else:
            data = batch["data"].to(device)
            y = batch["y"].to(device)

            optimizer.zero_grad()
            with torch.cuda.amp.autocast(enabled=scaler is not None):
                logits = model(data)
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
) -> Tuple[float, float]:
    """Evaluate for one epoch."""
    model.eval()
    total_loss = 0.0
    n_samples = 0
    all_probs = []
    all_labels = []

    for batch in loader:
        if batch["model_type"] == "pointnet":
            X = batch["X"].to(device)
            M = batch["M"].to(device)
            y = batch["y"].to(device)
            logits = model(X, M)
        else:
            data = batch["data"].to(device)
            y = batch["y"].to(device)
            logits = model(data)

        loss = F.binary_cross_entropy_with_logits(logits, y)
        total_loss += loss.item() * len(y)
        n_samples += len(y)

        probs = torch.sigmoid(logits).cpu().numpy()
        all_probs.extend(probs)
        all_labels.extend(y.cpu().numpy())

    # Accuracy at threshold 0.5
    all_probs = np.array(all_probs)
    all_labels = np.array(all_labels)
    preds = (all_probs > 0.5).astype(float)
    labels_binary = (all_labels > 0.5).astype(float)
    accuracy = (preds == labels_binary).mean()

    return total_loss / max(1, n_samples), accuracy


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Train NNBAR P-Signal Classifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Data
    parser.add_argument(
        "--data_dir", required=True,
        help="Root directory with candidates.parquet files"
    )
    parser.add_argument(
        "--val_dir", default=None,
        help="Optional validation data directory"
    )
    parser.add_argument(
        "--limit_train", type=int, default=None,
        help="Limit training samples"
    )
    parser.add_argument(
        "--limit_val", type=int, default=None,
        help="Limit validation samples"
    )
    parser.add_argument(
        "--label_column", default="frac_signal",
        help="Column name for signal fraction label"
    )

    # Model
    parser.add_argument(
        "--model", choices=["pointnet", "gnn"], default="pointnet",
        help="Model architecture"
    )
    parser.add_argument("--hidden", type=int, default=64, help="Hidden dimension")
    parser.add_argument("--emb", type=int, default=128, help="Embedding dimension")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")
    parser.add_argument("--n_layers", type=int, default=3, help="GNN layers (GNN only)")
    parser.add_argument("--k_neighbors", type=int, default=8, help="k-NN neighbors (GNN only)")

    # Training
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--num_workers", type=int, default=2)
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")

    # Output
    parser.add_argument("--save_dir", required=True, help="Output directory")

    args = parser.parse_args()

    # Check GNN availability
    if args.model == "gnn" and not HAS_TORCH_GEOMETRIC:
        print("[error] GNN model requires torch_geometric. Install with:")
        print("  pip install torch_geometric")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[device] {device}")
    print(f"[model] {args.model}")

    # Load data
    ds_train = TrackDataset(
        Path(args.data_dir),
        limit=args.limit_train,
        label_column=args.label_column,
    )

    if len(ds_train) == 0:
        print("[fatal] No usable tracks found")
        sys.exit(1)

    # Collate function
    if args.model == "pointnet":
        collate_fn = collate_pointnet
    else:
        collate_fn = lambda batch: collate_gnn(batch, k_neighbors=args.k_neighbors)

    dl_train = DataLoader(
        ds_train,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_fn,
        pin_memory=True,
    )

    # Validation data
    dl_val = None
    if args.val_dir:
        ds_val = TrackDataset(
            Path(args.val_dir),
            limit=args.limit_val,
            label_column=args.label_column,
        )
        if len(ds_val) > 0:
            dl_val = DataLoader(
                ds_val,
                batch_size=args.batch_size,
                shuffle=False,
                num_workers=args.num_workers,
                collate_fn=collate_fn,
                pin_memory=True,
            )

    # Create model
    if args.model == "pointnet":
        model = PointNetMini(hidden=args.hidden, emb=args.emb, dropout=args.dropout)
    else:
        model = TrackGNN(
            hidden=args.hidden,
            emb=args.emb,
            n_layers=args.n_layers,
            dropout=args.dropout,
        )

    model = model.to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[model] {n_params:,} trainable parameters")

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
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
    print(f"Training {args.model.upper()} for {args.epochs} epochs")
    print(f"{'=' * 60}\n")

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        train_loss = train_epoch(
            model, dl_train, optimizer, device, scaler, pos_weight
        )
        msg = f"[epoch {epoch:3d}/{args.epochs}] train_bce={train_loss:.4f}"

        if dl_val is not None:
            val_loss, val_acc = eval_epoch(model, dl_val, device)
            msg += f"  val_bce={val_loss:.4f}  val_acc={val_acc:.3f}"
            metric = val_loss
        else:
            metric = train_loss

        # Save best
        if metric < best_loss - 1e-6:
            best_loss = metric
            patience_counter = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model": model.state_dict(),
                    "model_type": args.model,
                    "hidden": args.hidden,
                    "emb": args.emb,
                    "n_layers": args.n_layers if args.model == "gnn" else None,
                    "k_neighbors": args.k_neighbors if args.model == "gnn" else None,
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
            "model_type": args.model,
            "hidden": args.hidden,
            "emb": args.emb,
            "n_layers": args.n_layers if args.model == "gnn" else None,
            "k_neighbors": args.k_neighbors if args.model == "gnn" else None,
        },
        save_dir / "last.ckpt",
    )

    # Save config
    with open(save_dir / "train_config.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    print(f"\n[done] best checkpoint: {best_path}")
    print(f"[done] best loss: {best_loss:.4f}")


if __name__ == "__main__":
    main()
