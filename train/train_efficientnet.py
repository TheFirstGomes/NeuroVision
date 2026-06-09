"""
EfficientNet-B4 fine-tuning on APTOS 2019 for fundoscopy DR classification.

Setup on Kaggle:
  1. Create a new notebook, enable GPU (T4 or P100 — Settings → Accelerator)
  2. Add dataset: aptos2019-blindness-detection  (Datasets → + Add Data)
  3. Upload this file and run, or paste content into a code cell

Expected runtime: ~35 min on T4 GPU.
Output: /kaggle/working/efficientnet_b4_aptos.pt

Next step: run export_to_onnx.py to produce the ONNX artifact for production.
"""
import os
import time
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

import timm
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, cohen_kappa_score, recall_score
from tqdm import tqdm


# ── Configuration ─────────────────────────────────────────────────────────────

@dataclass
class Config:
    data_dir:      str   = "/kaggle/input/aptos2019-blindness-detection"
    output_dir:    str   = "/kaggle/working"
    csv_file:      str   = "train.csv"          # CSV filename inside data_dir
    image_subdir:  str   = "train_images"       # image folder relative to data_dir
    model_name:    str   = "efficientnet_b4"
    num_classes:   int   = 5
    image_size:    int   = 512
    batch_size:    int   = 16
    num_workers:   int   = 4

    # Phase 1: frozen backbone, train head only
    phase1_epochs: int   = 5
    phase1_lr:     float = 1e-3

    # Phase 2: full fine-tune with cosine annealing
    phase2_epochs: int   = 15
    phase2_lr:     float = 5e-5
    phase2_min_lr: float = 1e-6

    weight_decay:  float = 1e-4
    val_split:     float = 0.20
    seed:          int   = 42


cfg = Config()

# Maps diagnosis integer (0-4) → internal class name used in production
LABEL_NAMES = [
    "normal",
    "dr_mild",
    "dr_moderate",
    "dr_severe",
    "dr_proliferative",
]


# ── Augmentation pipelines ────────────────────────────────────────────────────

def _train_transforms(image_size: int) -> A.Compose:
    return A.Compose([
        A.Resize(image_size, image_size),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.ShiftScaleRotate(
            shift_limit=0.05,
            scale_limit=0.10,
            rotate_limit=20,
            border_mode=0,
            p=0.5,
        ),
        A.OneOf([
            A.GaussNoise(std_range=(0.05, 0.15), p=1.0),
            A.GaussianBlur(blur_limit=3, p=1.0),
        ], p=0.20),
        A.RandomBrightnessContrast(
            brightness_limit=0.20,
            contrast_limit=0.20,
            p=0.40,
        ),
        A.HueSaturationValue(
            hue_shift_limit=10,
            sat_shift_limit=20,
            val_shift_limit=10,
            p=0.30,
        ),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
        ToTensorV2(),
    ])


def _val_transforms(image_size: int) -> A.Compose:
    return A.Compose([
        A.Resize(image_size, image_size),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
        ToTensorV2(),
    ])


# ── Dataset ───────────────────────────────────────────────────────────────────

class APTOSDataset(Dataset):
    def __init__(
        self,
        df: pd.DataFrame,
        image_dir: Path,
        transforms: A.Compose,
    ) -> None:
        self.df         = df.reset_index(drop=True)
        self.image_dir  = image_dir
        self.transforms = transforms

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row      = self.df.iloc[idx]
        img_path = self.image_dir / f"{row['id_code']}.png"
        img      = np.array(Image.open(img_path).convert("RGB"))
        img      = self.transforms(image=img)["image"]
        return img, int(row["diagnosis"])


def _weighted_sampler(labels: list[int], num_classes: int) -> WeightedRandomSampler:
    counts  = np.bincount(labels, minlength=num_classes).astype(np.float32)
    weights = 1.0 / (counts + 1e-8)
    sample_weights = torch.tensor([weights[lbl] for lbl in labels])
    return WeightedRandomSampler(
        sample_weights, num_samples=len(labels), replacement=True
    )


# ── Model helpers ─────────────────────────────────────────────────────────────

def build_model(cfg: Config, device: torch.device) -> nn.Module:
    model = timm.create_model(
        cfg.model_name,
        pretrained=True,
        num_classes=cfg.num_classes,
    )
    return model.to(device)


def freeze_backbone(model: nn.Module) -> None:
    for name, param in model.named_parameters():
        if "classifier" not in name:
            param.requires_grad = False


def unfreeze_all(model: nn.Module) -> None:
    for param in model.parameters():
        param.requires_grad = True


# ── Training / validation loops ───────────────────────────────────────────────

def train_epoch(
    model:     nn.Module,
    loader:    DataLoader,
    optimizer: optim.Optimizer,
    criterion: nn.Module,
    scaler:    Optional[object],
    device:    torch.device,
    use_amp:   bool,
) -> float:
    model.train()
    total_loss = 0.0

    for images, labels in tqdm(loader, desc="  train", leave=False):
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()

        if use_amp:
            with torch.amp.autocast("cuda"):
                loss = criterion(model(images), labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()

        total_loss += loss.item()

    return total_loss / len(loader)


@torch.no_grad()
def validate(
    model:       nn.Module,
    loader:      DataLoader,
    criterion:   nn.Module,
    device:      torch.device,
    use_amp:     bool,
    num_classes: int,
) -> dict:
    model.eval()
    all_logits, all_labels = [], []
    total_loss = 0.0

    for images, labels in tqdm(loader, desc="  val  ", leave=False):
        images, labels = images.to(device), labels.to(device)

        if use_amp:
            with torch.amp.autocast("cuda"):
                logits = model(images)
                loss   = criterion(logits, labels)
        else:
            logits = model(images)
            loss   = criterion(logits, labels)

        total_loss    += loss.item()
        all_logits.append(logits.cpu().float())
        all_labels.append(labels.cpu())

    logits_cat = torch.cat(all_logits)
    labels_np  = torch.cat(all_labels).numpy()
    probs      = torch.softmax(logits_cat, dim=1).numpy()
    preds      = np.argmax(probs, axis=1)

    try:
        auc = roc_auc_score(labels_np, probs, multi_class="ovr", average="macro")
    except ValueError:
        auc = 0.0

    f1  = f1_score(labels_np, preds, average="macro", zero_division=0)
    qwk = cohen_kappa_score(labels_np, preds, weights="quadratic")

    # Sensitivity for severe/proliferative grades — clinically critical (false negatives = blindness risk)
    severe_classes = [c for c in [3, 4] if c in labels_np]
    sens_severe = recall_score(labels_np, preds, labels=severe_classes, average="macro", zero_division=0)

    return {
        "loss":        total_loss / len(loader),
        "auc":         auc,
        "f1":          f1,
        "qwk":         qwk,
        "sens_severe": sens_severe,
    }


def _save_checkpoint(
    path: Path,
    model: nn.Module,
    metrics: dict,
    epoch: int,
    phase: int,
    cfg: Config,
) -> None:
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "val_auc":          round(metrics["auc"], 4),
            "val_f1":           round(metrics["f1"], 4),
            "val_qwk":          round(metrics["qwk"], 4),
            "val_sens_severe":  round(metrics["sens_severe"], 4),
            "epoch":            epoch,
            "phase":            phase,
            "trained_at":       datetime.now(timezone.utc).isoformat(),
            "label_map":        LABEL_NAMES,
            "model_name":       cfg.model_name,
            "num_classes":      cfg.num_classes,
            "image_size":       cfg.image_size,
        },
        path,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)

    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    scaler  = torch.amp.GradScaler("cuda") if use_amp else None

    print(f"Device:  {device}  |  AMP: {use_amp}")

    # ── Data preparation ──────────────────────────────────────────────────────
    data_dir  = Path(cfg.data_dir)
    image_dir = data_dir / cfg.image_subdir
    df        = pd.read_csv(data_dir / cfg.csv_file)

    train_df, val_df = train_test_split(
        df,
        test_size=cfg.val_split,
        stratify=df["diagnosis"],
        random_state=cfg.seed,
    )
    print(f"Train: {len(train_df)}  |  Val: {len(val_df)}")
    print(f"Class distribution (train):\n{train_df['diagnosis'].value_counts().sort_index()}\n")

    train_ds = APTOSDataset(train_df, image_dir, _train_transforms(cfg.image_size))
    val_ds   = APTOSDataset(val_df,   image_dir, _val_transforms(cfg.image_size))

    sampler = _weighted_sampler(train_df["diagnosis"].tolist(), cfg.num_classes)

    train_loader = DataLoader(
        train_ds,
        batch_size=cfg.batch_size,
        sampler=sampler,
        num_workers=cfg.num_workers,
        pin_memory=use_amp,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=cfg.batch_size * 2,
        shuffle=False,
        num_workers=cfg.num_workers,
        pin_memory=use_amp,
    )

    # Class-weighted loss for additional imbalance correction
    counts = np.bincount(df["diagnosis"].tolist(), minlength=cfg.num_classes)
    class_weights = torch.tensor(1.0 / (counts + 1e-8), dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    model    = build_model(cfg, device)
    output_path = Path(cfg.output_dir) / "efficientnet_b4_aptos.pt"
    best_qwk = -1.0

    # ── Phase 1: frozen backbone, train classifier head ───────────────────────
    print("=" * 60)
    print("Phase 1: Classifier head only (backbone frozen)")
    print("=" * 60)
    freeze_backbone(model)

    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=cfg.phase1_lr,
        weight_decay=cfg.weight_decay,
    )

    for epoch in range(1, cfg.phase1_epochs + 1):
        t0         = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, criterion, scaler, device, use_amp)
        metrics    = validate(model, val_loader, criterion, device, use_amp, cfg.num_classes)
        elapsed    = time.time() - t0

        print(
            f"  [{epoch:02d}/{cfg.phase1_epochs}]  "
            f"loss={train_loss:.4f}  val_loss={metrics['loss']:.4f}  "
            f"AUC={metrics['auc']:.4f}  QWK={metrics['qwk']:.4f}  "
            f"F1={metrics['f1']:.4f}  sens_severe={metrics['sens_severe']:.4f}  "
            f"({elapsed:.0f}s)"
        )

        if metrics["qwk"] > best_qwk:
            best_qwk = metrics["qwk"]
            _save_checkpoint(output_path, model, metrics, epoch, phase=1, cfg=cfg)
            print(f"    >> Best model saved (QWK={best_qwk:.4f}  AUC={metrics['auc']:.4f})")

    # ── Phase 2: full fine-tune with cosine LR annealing ─────────────────────
    print("\n" + "=" * 60)
    print("Phase 2: Full fine-tune (all layers, cosine LR)")
    print("=" * 60)
    unfreeze_all(model)

    optimizer = optim.AdamW(
        model.parameters(),
        lr=cfg.phase2_lr,
        weight_decay=cfg.weight_decay,
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=cfg.phase2_epochs,
        eta_min=cfg.phase2_min_lr,
    )

    for epoch in range(1, cfg.phase2_epochs + 1):
        t0         = time.time()
        train_loss = train_epoch(model, train_loader, optimizer, criterion, scaler, device, use_amp)
        metrics    = validate(model, val_loader, criterion, device, use_amp, cfg.num_classes)
        scheduler.step()
        elapsed    = time.time() - t0
        lr_now     = scheduler.get_last_lr()[0]

        print(
            f"  [{epoch:02d}/{cfg.phase2_epochs}]  "
            f"loss={train_loss:.4f}  val_loss={metrics['loss']:.4f}  "
            f"AUC={metrics['auc']:.4f}  QWK={metrics['qwk']:.4f}  "
            f"F1={metrics['f1']:.4f}  sens_severe={metrics['sens_severe']:.4f}  "
            f"lr={lr_now:.1e}  ({elapsed:.0f}s)"
        )

        if metrics["qwk"] > best_qwk:
            best_qwk = metrics["qwk"]
            _save_checkpoint(
                output_path, model, metrics,
                epoch=cfg.phase1_epochs + epoch, phase=2, cfg=cfg,
            )
            print(f"    >> Best model saved (QWK={best_qwk:.4f}  AUC={metrics['auc']:.4f})")

    print(f"\nTraining complete.")
    print(f"Best val QWK:        {best_qwk:.4f}  (primary metric)")
    print(f"Checkpoint:          {output_path}")
    print(f"\nNext step: python export_to_onnx.py --checkpoint {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train EfficientNet-B4 on APTOS 2019")
    parser.add_argument("--data-dir",     default=cfg.data_dir,    help="Path to APTOS dataset root")
    parser.add_argument("--output-dir",   default=cfg.output_dir,  help="Directory for checkpoint output")
    parser.add_argument("--csv",          default=cfg.csv_file,    help="CSV filename inside data-dir")
    parser.add_argument("--image-subdir", default=cfg.image_subdir,help="Image folder relative to data-dir")
    parser.add_argument("--batch-size",   type=int,   default=cfg.batch_size)
    parser.add_argument("--phase2-lr",   type=float, default=cfg.phase2_lr,  help="GA-optimized phase2 LR")
    parser.add_argument("--weight-decay", type=float, default=cfg.weight_decay, help="GA-optimized weight decay")
    args = parser.parse_args()
    cfg.data_dir     = args.data_dir
    cfg.output_dir   = args.output_dir
    cfg.csv_file     = args.csv
    cfg.image_subdir = args.image_subdir
    cfg.batch_size   = args.batch_size
    cfg.phase2_lr    = args.phase2_lr
    cfg.weight_decay = args.weight_decay
    main()
