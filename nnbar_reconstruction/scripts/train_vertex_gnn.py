#!/usr/bin/env python3
"""
NNBAR Vertex GNN Training

Train the Vertex GNN model to predict annihilation vertex position
from track candidates.

Usage:
    python train_vertex_gnn.py \\
        --train_data training_data/vertex_train.npz \\
        --val_data training_data/vertex_val.npz \\
        --save_dir models/vertex_gnn

Author: NNBAR Collaboration
Date: 2026-01-12
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Enable performance optimizations
torch.backends.cudnn.benchmark = True
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nnbar_reconstruction.vertex.gnn_model import (
    create_model,
    get_loss_function,
    LogCoshLoss,
)


class VertexDataset(Dataset):
    """Dataset for Vertex GNN training from NPZ files."""

    def __init__(self, npz_path: str):
        """Load training data from NPZ file."""
        data = np.load(npz_path)

        self.track_features = data['track_features']  # (N, C, 12)
        self.track_positions = data['track_positions']  # (N, C, 3)
        self.track_masks = data['track_masks']  # (N, C)
        self.truth_vertices = data['truth_vertices']  # (N, 3)
        self.n_tracks = data['n_tracks']  # (N,)

        print(f"[dataset] Loaded {len(self.truth_vertices)} samples from {npz_path}")
        print(f"  Max tracks per event: {self.track_masks.shape[1]}")
        print(f"  Mean tracks per event: {self.n_tracks.mean():.1f}")
        print(f"  Truth vertex mean: ({self.truth_vertices.mean(axis=0)})")

    def __len__(self):
        return len(self.truth_vertices)

    def __getitem__(self, idx):
        return {
            'track_features': self.track_features[idx].astype(np.float32),
            'track_positions': self.track_positions[idx].astype(np.float32),
            'track_mask': self.track_masks[idx],
            'truth_vertex': self.truth_vertices[idx].astype(np.float32),
        }


def collate_fn(batch):
    """Collate batch of samples."""
    return {
        'track_features': torch.from_numpy(np.stack([b['track_features'] for b in batch])),
        'track_positions': torch.from_numpy(np.stack([b['track_positions'] for b in batch])),
        'track_mask': torch.from_numpy(np.stack([b['track_mask'] for b in batch])),
        'truth_vertex': torch.from_numpy(np.stack([b['truth_vertex'] for b in batch])),
    }


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    loss_fn: nn.Module,
    device: torch.device,
    scaler=None,
) -> Tuple[float, float]:
    """Train for one epoch. Returns (loss, mean_error)."""
    model.train()
    total_loss = 0.0
    total_error = 0.0
    n_samples = 0

    for batch in loader:
        cand_feat = batch['track_features'].to(device)
        cand_vxyz = batch['track_positions'].to(device)
        cand_mask = batch['track_mask'].to(device)
        truth = batch['truth_vertex'].to(device)

        optimizer.zero_grad()

        with torch.cuda.amp.autocast(enabled=scaler is not None):
            output = model(cand_vxyz, cand_feat, cand_mask)
            pred = output['v_pred']
            loss = loss_fn(pred, truth)

        if scaler is not None:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()

        # Track metrics
        B = len(truth)
        total_loss += loss.item() * B
        n_samples += B

        # Mean Euclidean error
        with torch.no_grad():
            error = torch.sqrt(((pred - truth) ** 2).sum(dim=1)).mean()
            total_error += error.item() * B

    return total_loss / n_samples, total_error / n_samples


@torch.no_grad()
def eval_epoch(
    model: nn.Module,
    loader: DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> Tuple[float, float, float, float, float]:
    """Evaluate for one epoch. Returns (loss, mean_error, error_x, error_y, error_z)."""
    model.eval()
    total_loss = 0.0
    total_error = 0.0
    total_error_x = 0.0
    total_error_y = 0.0
    total_error_z = 0.0
    n_samples = 0

    for batch in loader:
        cand_feat = batch['track_features'].to(device)
        cand_vxyz = batch['track_positions'].to(device)
        cand_mask = batch['track_mask'].to(device)
        truth = batch['truth_vertex'].to(device)

        output = model(cand_vxyz, cand_feat, cand_mask)
        pred = output['v_pred']
        loss = loss_fn(pred, truth)

        B = len(truth)
        total_loss += loss.item() * B
        n_samples += B

        # Per-coordinate errors
        diff = (pred - truth).abs()
        total_error_x += diff[:, 0].mean().item() * B
        total_error_y += diff[:, 1].mean().item() * B
        total_error_z += diff[:, 2].mean().item() * B

        # Euclidean error
        error = torch.sqrt(((pred - truth) ** 2).sum(dim=1)).mean()
        total_error += error.item() * B

    return (
        total_loss / n_samples,
        total_error / n_samples,
        total_error_x / n_samples,
        total_error_y / n_samples,
        total_error_z / n_samples,
    )


def main():
    parser = argparse.ArgumentParser(description="Train NNBAR Vertex GNN")

    # Data
    parser.add_argument("--train_data", required=True, help="Training NPZ file")
    parser.add_argument("--val_data", default=None, help="Validation NPZ file")

    # Model
    parser.add_argument("--version", choices=['v1', 'v2'], default='v1', help="Model version")
    parser.add_argument("--hidden_dim", type=int, default=128, help="Hidden dimension")
    parser.add_argument("--n_layers", type=int, default=3, help="Number of layers")
    parser.add_argument("--n_heads", type=int, default=4, help="Number of attention heads")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")

    # Training
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=20, help="Early stopping patience")
    parser.add_argument("--loss", choices=['logcosh', 'huber', 'mse', 'l1'], default='logcosh')

    # Output
    parser.add_argument("--save_dir", required=True, help="Output directory")

    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[device] {device}")

    # Load data
    print("\n" + "=" * 60)
    print("Loading training data...")
    ds_train = VertexDataset(args.train_data)

    if len(ds_train) == 0:
        print("[fatal] No usable samples found")
        sys.exit(1)

    dl_train = DataLoader(
        ds_train,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=2,
        collate_fn=collate_fn,
        pin_memory=True,
    )

    # Validation data
    dl_val = None
    if args.val_data:
        print("\nLoading validation data...")
        ds_val = VertexDataset(args.val_data)
        if len(ds_val) > 0:
            dl_val = DataLoader(
                ds_val,
                batch_size=args.batch_size,
                shuffle=False,
                num_workers=2,
                collate_fn=collate_fn,
                pin_memory=True,
            )

    # Create model
    model = create_model(
        version=args.version,
        cand_in_dim=12,
        hidden_dim=args.hidden_dim,
        n_layers=args.n_layers,
        n_heads=args.n_heads,
        dropout=args.dropout,
    )
    model = model.to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n[model] NNBARVertexGNN {args.version} with {n_params:,} trainable parameters")

    # Loss function
    loss_fn = get_loss_function(args.loss)
    print(f"[loss] {args.loss}")

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.cuda.amp.GradScaler(enabled=torch.cuda.is_available())

    # Training
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    best_error = math.inf
    best_path = save_dir / "best.ckpt"
    patience_counter = 0

    print(f"\n{'=' * 60}")
    print(f"Training for {args.epochs} epochs")
    print(f"{'=' * 60}\n")

    history = {
        "train_loss": [], "train_error": [],
        "val_loss": [], "val_error": [],
        "val_error_x": [], "val_error_y": [], "val_error_z": [],
    }

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        train_loss, train_error = train_epoch(
            model, dl_train, optimizer, loss_fn, device, scaler
        )
        history["train_loss"].append(train_loss)
        history["train_error"].append(train_error)

        msg = f"[epoch {epoch:3d}/{args.epochs}] loss={train_loss:.4f}  err={train_error:.2f}cm"

        if dl_val is not None:
            val_loss, val_error, err_x, err_y, err_z = eval_epoch(
                model, dl_val, loss_fn, device
            )
            history["val_loss"].append(val_loss)
            history["val_error"].append(val_error)
            history["val_error_x"].append(err_x)
            history["val_error_y"].append(err_y)
            history["val_error_z"].append(err_z)

            msg += f"  val_err={val_error:.2f}cm (x={err_x:.2f}, y={err_y:.2f}, z={err_z:.2f})"
            metric = val_error
        else:
            metric = train_error

        scheduler.step()

        # Save best
        if metric < best_error - 0.01:  # 0.01 cm tolerance
            best_error = metric
            patience_counter = 0
            torch.save(
                {
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'config': {
                        'version': args.version,
                        'cand_in_dim': 12,
                        'hidden_dim': args.hidden_dim,
                        'n_layers': args.n_layers,
                        'n_heads': args.n_heads,
                        'dropout': args.dropout,
                    },
                    'val_error': val_error if dl_val else None,
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
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'config': {
                'version': args.version,
                'cand_in_dim': 12,
                'hidden_dim': args.hidden_dim,
                'n_layers': args.n_layers,
                'n_heads': args.n_heads,
                'dropout': args.dropout,
            },
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
    print(f"Best vertex error: {best_error:.2f} cm")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
