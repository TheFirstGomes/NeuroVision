"""
Genetic Algorithm hyperparameter search for EfficientNet-B4 fine-tuning.

Strategy:
  Each individual encodes (phase2_lr, weight_decay, batch_size, augmentation_intensity).
  Fitness = macro AUC on the validation set after a short 3-epoch probe using
  phase2-style full fine-tune (backbone already warm from phase 1 defaults).

  The GA runs for a configurable number of generations, then the best
  individual is printed and saved to ga_best_params.json for use in the
  full training run.

Usage:
  python ga_hyperparam_search.py --data-dir <path> --output-dir <path> \\
      --csv train_1.csv --image-subdir "train_images/train_images" \\
      --pop-size 12 --generations 5 --probe-epochs 3

  # Use best params in full train:
  python train_efficientnet.py --data-dir <path> --output-dir <path> ...
      # (edit Config manually or pass --phase2-lr etc. once wired)
"""

import os
import json
import random
import argparse
import time
import copy
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
import timm
import albumentations as A
from albumentations.pytorch import ToTensorV2
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score


# ── Gene space (log-uniform or uniform per param) ─────────────────────────────

GENE_SPACE = {
    # (min, max, scale)  scale="log" → sample in log space
    "phase2_lr":              (1e-5, 5e-4, "log"),
    "weight_decay":           (1e-5, 1e-2, "log"),
    "batch_size_idx":         (0, 2, "int"),   # index into [8, 16, 32]
    "augmentation_intensity": (0.5, 1.5, "linear"),
}
BATCH_SIZES = [8, 16, 32]


@dataclass
class Individual:
    phase2_lr:              float
    weight_decay:           float
    batch_size_idx:         int
    augmentation_intensity: float
    fitness:                float = -1.0

    @property
    def batch_size(self) -> int:
        return BATCH_SIZES[self.batch_size_idx]

    def to_dict(self) -> dict:
        return {
            "phase2_lr":              self.phase2_lr,
            "weight_decay":           self.weight_decay,
            "batch_size":             self.batch_size,
            "augmentation_intensity": self.augmentation_intensity,
            "val_auc":                round(self.fitness, 4),
        }


# ── Initialization ─────────────────────────────────────────────────────────────

def _rand_individual(rng: random.Random) -> Individual:
    lr = 10 ** rng.uniform(
        np.log10(GENE_SPACE["phase2_lr"][0]),
        np.log10(GENE_SPACE["phase2_lr"][1]),
    )
    wd = 10 ** rng.uniform(
        np.log10(GENE_SPACE["weight_decay"][0]),
        np.log10(GENE_SPACE["weight_decay"][1]),
    )
    bs_idx = rng.randint(0, 2)
    aug = rng.uniform(
        GENE_SPACE["augmentation_intensity"][0],
        GENE_SPACE["augmentation_intensity"][1],
    )
    return Individual(phase2_lr=lr, weight_decay=wd,
                      batch_size_idx=bs_idx, augmentation_intensity=aug)


# ── Augmentation (intensity-scaled) ───────────────────────────────────────────

def _train_transforms(image_size: int, intensity: float) -> A.Compose:
    i = intensity
    return A.Compose([
        A.Resize(image_size, image_size),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.ShiftScaleRotate(
            shift_limit=0.05 * i,
            scale_limit=0.10 * i,
            rotate_limit=int(20 * i),
            border_mode=0,
            p=0.5,
        ),
        A.OneOf([
            A.GaussNoise(std_range=(0.05 * i, 0.15 * i), p=1.0),
            A.GaussianBlur(blur_limit=3, p=1.0),
        ], p=0.20),
        A.RandomBrightnessContrast(
            brightness_limit=0.20 * i,
            contrast_limit=0.20 * i,
            p=0.40,
        ),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])


def _val_transforms(image_size: int) -> A.Compose:
    return A.Compose([
        A.Resize(image_size, image_size),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])


# ── Dataset (inline, no import from train script) ─────────────────────────────

class APTOSDataset(torch.utils.data.Dataset):
    def __init__(self, df, image_dir, transforms):
        self.df         = df.reset_index(drop=True)
        self.image_dir  = Path(image_dir)
        self.transforms = transforms

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row      = self.df.iloc[idx]
        img      = np.array(Image.open(self.image_dir / f"{row['id_code']}.png").convert("RGB"))
        img      = self.transforms(image=img)["image"]
        return img, int(row["diagnosis"])


# ── Fitness evaluation ─────────────────────────────────────────────────────────

def evaluate_individual(
    ind:         Individual,
    train_df:    pd.DataFrame,
    val_df:      pd.DataFrame,
    image_dir:   Path,
    device:      torch.device,
    num_classes: int,
    image_size:  int,
    probe_epochs: int,
    base_model:  nn.Module,      # pre-trained phase-1 weights, eval to avoid mutation
) -> float:
    """Run a short probe and return macro AUC (higher = better fitness)."""

    model = copy.deepcopy(base_model).to(device)
    for param in model.parameters():
        param.requires_grad = True

    counts = np.bincount(train_df["diagnosis"].tolist(), minlength=num_classes)
    class_weights = torch.tensor(1.0 / (counts + 1e-8), dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = optim.AdamW(
        model.parameters(),
        lr=ind.phase2_lr,
        weight_decay=ind.weight_decay,
    )

    train_ds = APTOSDataset(train_df, image_dir, _train_transforms(image_size, ind.augmentation_intensity))
    val_ds   = APTOSDataset(val_df,   image_dir, _val_transforms(image_size))

    labels_list = train_df["diagnosis"].tolist()
    w = torch.tensor(
        [1.0 / (counts[l] + 1e-8) for l in labels_list]
    )
    sampler = WeightedRandomSampler(w, num_samples=len(labels_list), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=ind.batch_size, sampler=sampler,
                              num_workers=2, pin_memory=device.type == "cuda")
    val_loader   = DataLoader(val_ds, batch_size=ind.batch_size * 2, shuffle=False,
                              num_workers=2, pin_memory=device.type == "cuda")

    use_amp = device.type == "cuda"
    scaler  = torch.amp.GradScaler("cuda") if use_amp else None

    model.train()
    for _ in range(probe_epochs):
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            if use_amp:
                with torch.amp.autocast("cuda"):
                    loss = criterion(model(images), labels)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                criterion(model(images), labels).backward()
                optimizer.step()

    model.eval()
    all_logits, all_labels = [], []
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            if use_amp:
                with torch.amp.autocast("cuda"):
                    logits = model(images)
            else:
                logits = model(images)
            all_logits.append(logits.cpu().float())
            all_labels.append(labels)

    probs     = torch.softmax(torch.cat(all_logits), dim=1).numpy()
    labels_np = torch.cat(all_labels).numpy()

    try:
        auc = roc_auc_score(labels_np, probs, multi_class="ovr", average="macro")
    except ValueError:
        auc = 0.0

    del model
    torch.cuda.empty_cache()
    return float(auc)


# ── Genetic operators ─────────────────────────────────────────────────────────

def _crossover(p1: Individual, p2: Individual, rng: random.Random) -> Individual:
    """Uniform crossover: each gene inherited independently from one parent."""
    return Individual(
        phase2_lr=              p1.phase2_lr if rng.random() < 0.5 else p2.phase2_lr,
        weight_decay=           p1.weight_decay if rng.random() < 0.5 else p2.weight_decay,
        batch_size_idx=         p1.batch_size_idx if rng.random() < 0.5 else p2.batch_size_idx,
        augmentation_intensity= p1.augmentation_intensity if rng.random() < 0.5 else p2.augmentation_intensity,
    )


def _mutate(ind: Individual, rng: random.Random, mutation_rate: float = 0.25) -> Individual:
    """Each gene is independently perturbed with probability mutation_rate."""
    lr  = ind.phase2_lr
    wd  = ind.weight_decay
    bs  = ind.batch_size_idx
    aug = ind.augmentation_intensity

    if rng.random() < mutation_rate:
        # Multiplicative perturbation in log space: ×[0.5, 2.0]
        lr = float(np.clip(lr * (10 ** rng.uniform(-0.3, 0.3)),
                           GENE_SPACE["phase2_lr"][0], GENE_SPACE["phase2_lr"][1]))

    if rng.random() < mutation_rate:
        wd = float(np.clip(wd * (10 ** rng.uniform(-0.5, 0.5)),
                           GENE_SPACE["weight_decay"][0], GENE_SPACE["weight_decay"][1]))

    if rng.random() < mutation_rate:
        bs = rng.randint(0, 2)

    if rng.random() < mutation_rate:
        aug = float(np.clip(aug + rng.gauss(0, 0.15),
                            GENE_SPACE["augmentation_intensity"][0],
                            GENE_SPACE["augmentation_intensity"][1]))

    return Individual(phase2_lr=lr, weight_decay=wd,
                      batch_size_idx=bs, augmentation_intensity=aug)


def _tournament_select(population: list[Individual], k: int = 3,
                        rng: random.Random = None) -> Individual:
    """Tournament selection: pick k individuals at random, return the fittest."""
    candidates = rng.choices(population, k=k)
    return max(candidates, key=lambda x: x.fitness)


# ── Main GA loop ───────────────────────────────────────────────────────────────

def run_ga(
    data_dir:     Path,
    image_dir:    Path,
    csv_path:     Path,
    output_dir:   Path,
    pop_size:     int,
    generations:  int,
    probe_epochs: int,
    elitism:      int,
    seed:         int,
    image_size:   int,
    num_classes:  int,
) -> Individual:
    rng = random.Random(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}  |  Population: {pop_size}  |  Generations: {generations}")
    print(f"Probe epochs per individual: {probe_epochs}")

    df = pd.read_csv(csv_path)
    train_df, val_df = train_test_split(
        df, test_size=0.20, stratify=df["diagnosis"], random_state=seed
    )
    print(f"Train: {len(train_df)}  |  Val: {len(val_df)}\n")

    # Build a base model (phase 1 already warmed: frozen backbone, 1 epoch head)
    print("Building base model (phase 1 warm-up, 1 epoch)...")
    base_model = timm.create_model("efficientnet_b4", pretrained=True, num_classes=num_classes)
    base_model = base_model.to(device)

    # Quick phase-1 warm-up so backbone features are not random
    for name, param in base_model.named_parameters():
        if "classifier" not in name:
            param.requires_grad = False

    counts = np.bincount(train_df["diagnosis"].tolist(), minlength=num_classes)
    class_weights = torch.tensor(1.0 / (counts + 1e-8), dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    head_optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, base_model.parameters()),
        lr=1e-3,
    )
    warm_ds = APTOSDataset(train_df, image_dir, _train_transforms(image_size, 1.0))
    labels_list = train_df["diagnosis"].tolist()
    w_warm = torch.tensor([1.0 / (counts[l] + 1e-8) for l in labels_list])
    warm_sampler = WeightedRandomSampler(w_warm, num_samples=len(labels_list), replacement=True)
    warm_loader = DataLoader(warm_ds, batch_size=16, sampler=warm_sampler, num_workers=2)
    use_amp = device.type == "cuda"
    scaler  = torch.amp.GradScaler("cuda") if use_amp else None

    base_model.train()
    for images, labels in warm_loader:
        images, labels = images.to(device), labels.to(device)
        head_optimizer.zero_grad()
        if use_amp:
            with torch.amp.autocast("cuda"):
                loss = criterion(base_model(images), labels)
            scaler.scale(loss).backward()
            scaler.step(head_optimizer)
            scaler.update()
        else:
            criterion(base_model(images), labels).backward()
            head_optimizer.step()

    base_model.eval()
    print("Base model warmed up.\n")

    # Initialise population
    population = [_rand_individual(rng) for _ in range(pop_size)]

    best_ever: Optional[Individual] = None
    history = []

    for gen in range(1, generations + 1):
        print(f"=== Generation {gen}/{generations} ===")
        t_gen = time.time()

        # Evaluate unevaluated individuals
        for i, ind in enumerate(population):
            if ind.fitness < 0:
                t0 = time.time()
                ind.fitness = evaluate_individual(
                    ind, train_df, val_df, image_dir,
                    device, num_classes, image_size, probe_epochs, base_model,
                )
                elapsed = time.time() - t0
                print(
                    f"  [{i+1:02d}/{pop_size}]  "
                    f"lr={ind.phase2_lr:.2e}  wd={ind.weight_decay:.2e}  "
                    f"bs={ind.batch_size}  aug={ind.augmentation_intensity:.2f}  "
                    f"AUC={ind.fitness:.4f}  ({elapsed:.0f}s)"
                )

        population.sort(key=lambda x: x.fitness, reverse=True)
        best = population[0]

        if best_ever is None or best.fitness > best_ever.fitness:
            best_ever = copy.deepcopy(best)

        gen_time = time.time() - t_gen
        print(
            f"\n  Gen {gen} best: AUC={best.fitness:.4f}  "
            f"lr={best.phase2_lr:.2e}  wd={best.weight_decay:.2e}  "
            f"bs={best.batch_size}  aug={best.augmentation_intensity:.2f}  "
            f"(gen time: {gen_time:.0f}s)\n"
        )
        history.append({"generation": gen, "best_auc": round(best.fitness, 4),
                         **best.to_dict()})

        if gen == generations:
            break

        # Next generation: elitism + crossover + mutation
        next_pop = population[:elitism]  # keep elite unchanged

        while len(next_pop) < pop_size:
            p1 = _tournament_select(population, k=3, rng=rng)
            p2 = _tournament_select(population, k=3, rng=rng)
            child = _crossover(p1, p2, rng)
            child = _mutate(child, rng)
            next_pop.append(child)

        population = next_pop

    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "ga_best_params.json"
    result = {
        "best_individual": best_ever.to_dict(),
        "search_config": {
            "pop_size":    pop_size,
            "generations": generations,
            "probe_epochs": probe_epochs,
            "seed":        seed,
        },
        "history": history,
    }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*60}")
    print(f"GA complete. Best individual found:")
    print(f"  val_auc:              {best_ever.fitness:.4f}")
    print(f"  phase2_lr:            {best_ever.phase2_lr:.2e}")
    print(f"  weight_decay:         {best_ever.weight_decay:.2e}")
    print(f"  batch_size:           {best_ever.batch_size}")
    print(f"  augmentation_intensity: {best_ever.augmentation_intensity:.2f}")
    print(f"\nResults saved to: {out_path}")
    print(f"\nTo use in full training, edit train_efficientnet.py Config with these values,")
    print(f"or pass: --phase2-lr {best_ever.phase2_lr:.2e} --weight-decay {best_ever.weight_decay:.2e} "
          f"--batch-size {best_ever.batch_size}")

    return best_ever


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GA hyperparameter search for EfficientNet-B4")
    parser.add_argument("--data-dir",     required=True,    help="Path to APTOS dataset root")
    parser.add_argument("--output-dir",   required=True,    help="Directory for ga_best_params.json")
    parser.add_argument("--csv",          default="train_1.csv")
    parser.add_argument("--image-subdir", default="train_images/train_images")
    parser.add_argument("--pop-size",     type=int, default=12,  help="Population size")
    parser.add_argument("--generations",  type=int, default=5,   help="Number of generations")
    parser.add_argument("--probe-epochs", type=int, default=3,   help="Epochs per fitness probe")
    parser.add_argument("--elitism",      type=int, default=2,   help="Elite individuals to keep unchanged")
    parser.add_argument("--seed",         type=int, default=42)
    parser.add_argument("--image-size",   type=int, default=380, help="Smaller size speeds up search")
    parser.add_argument("--num-classes",  type=int, default=5)
    args = parser.parse_args()

    data_dir  = Path(args.data_dir)
    run_ga(
        data_dir=data_dir,
        image_dir=data_dir / args.image_subdir,
        csv_path=data_dir / args.csv,
        output_dir=Path(args.output_dir),
        pop_size=args.pop_size,
        generations=args.generations,
        probe_epochs=args.probe_epochs,
        elitism=args.elitism,
        seed=args.seed,
        image_size=args.image_size,
        num_classes=args.num_classes,
    )
