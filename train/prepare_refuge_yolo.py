"""
prepare_refuge_yolo.py — Convert REFUGE2 segmentation masks to YOLO bounding-box format.

REFUGE2 structure (one of the following patterns is auto-detected):
  Pattern A — REFUGE2 official:
    <root>/Training400/Images/*.jpg
    <root>/Training400/Disc_Cup_Masks/*.bmp
    <root>/Validation400/Images/*.jpg
    <root>/Validation400/Disc_Cup_Masks/*.bmp

  Pattern B — flat:
    <root>/images/*.png
    <root>/disc_masks/*.png
    <root>/cup_masks/*.png      (optional)

  Pattern C — train/val split:
    <root>/train/images/*.jpg
    <root>/train/masks/*.png
    <root>/val/images/*.jpg
    <root>/val/masks/*.png

Segmentation mask encoding:
  - Optic disc (OD): pixels with value > 0 (white/gray in REFUGE2 .bmp)
  - Optic cup  (OC): pixels with value == 0 inside the disc region
    (REFUGE2 uses a 3-class mask: 0=cup, 128=rim, 255=background — or binary)

YOLO output format:
  labels/<split>/<image_stem>.txt
    class cx cy w h   (all normalized 0–1, cx/cy = box center)
  class 0 = optic_disc
  class 1 = optic_cup  (if cup mask available)

CLI usage:
  python prepare_refuge_yolo.py --refuge-dir C:/datasets/refuge2 --output-dir C:/datasets/refuge2_yolo
"""
import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm


# ── Mask → bounding box ───────────────────────────────────────────────────────

def _mask_to_bbox(mask_bin: np.ndarray) -> tuple[float, float, float, float] | None:
    """
    Given a binary mask (uint8, 0 or 255), return YOLO normalized bbox:
    (cx, cy, w, h) — all in [0, 1] relative to image dimensions.
    Returns None if no foreground pixel found.
    """
    rows = np.any(mask_bin, axis=1)
    cols = np.any(mask_bin, axis=0)
    if not rows.any():
        return None

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    h, w = mask_bin.shape
    cx = (cmin + cmax) / 2.0 / w
    cy = (rmin + rmax) / 2.0 / h
    bw = (cmax - cmin) / w
    bh = (rmax - rmin) / h
    return cx, cy, bw, bh


def _parse_refuge2_mask(mask_path: Path) -> tuple[np.ndarray | None, np.ndarray | None]:
    """
    Parse a REFUGE2 segmentation mask file into (disc_mask, cup_mask).

    REFUGE2 .bmp encoding:
      0   = optic cup
      128 = optic rim (disc but not cup)
      255 = background

    Combined disc mask = (pixel < 255)
    Cup mask           = (pixel == 0)

    Handles both: single-channel and 3-channel (RGB) mask images.
    """
    mask = cv2.imread(str(mask_path), cv2.IMREAD_UNCHANGED)
    if mask is None:
        return None, None

    if len(mask.shape) == 3:
        # Use first channel (all channels identical in REFUGE2)
        mask = mask[:, :, 0]

    disc_mask = np.where(mask < 255, 255, 0).astype(np.uint8)
    cup_mask  = np.where(mask == 0,  255, 0).astype(np.uint8)

    # Fallback for binary masks (0/255 only → disc only)
    unique = np.unique(mask)
    if set(unique).issubset({0, 255}):
        disc_mask = np.where(mask == 0, 255, 0).astype(np.uint8)
        cup_mask  = None

    return disc_mask, cup_mask


# ── Structure detection ───────────────────────────────────────────────────────

def _detect_structure(root: Path) -> dict:
    """
    Auto-detect the dataset folder layout.
    Returns a dict with keys: splits → list of (image_dir, mask_dir) tuples.
    """
    # Pattern A — REFUGE2 official
    if (root / "Training400").exists():
        splits = {}
        for name, split in [("Training400", "train"), ("Validation400", "val"), ("Test400", "test")]:
            d = root / name
            if d.exists():
                img_dir  = d / "Images"
                mask_dir = d / "Disc_Cup_Masks"
                if not img_dir.exists():
                    img_dir = d / "images"
                if not mask_dir.exists():
                    mask_dir = d / "disc_masks"
                splits[split] = (img_dir, mask_dir)
        return splits

    # Pattern C — train/val subdirs
    if (root / "train").exists() or (root / "val").exists():
        splits = {}
        for split in ["train", "val", "test"]:
            d = root / split
            if not d.exists():
                continue
            img_dir  = d / "images"
            # Accept both "masks" and "mask" (REFUGE2 uses singular)
            mask_dir = d / "masks" if (d / "masks").exists() else d / "mask"
            if img_dir.exists():
                splits[split] = (img_dir, mask_dir)
        if splits:
            return splits

    # Pattern B — flat, single split → treat as train
    img_dir  = root / "images"
    mask_dir = root / "disc_masks" if (root / "disc_masks").exists() else root / "masks"
    if img_dir.exists():
        return {"train": (img_dir, mask_dir)}

    # Last resort — scan recursively for .jpg/.png images + .bmp masks
    images = list(root.rglob("*.jpg")) + list(root.rglob("*.png"))
    masks  = list(root.rglob("*.bmp"))
    if images and masks:
        return {"_raw": (None, None), "_images": images, "_masks": masks}

    return {}


def _image_extensions() -> tuple[str, ...]:
    return (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


def _find_mask(image_stem: str, mask_dir: Path) -> Path | None:
    for ext in (".bmp", ".png", ".jpg", ".jpeg"):
        p = mask_dir / f"{image_stem}{ext}"
        if p.exists():
            return p
    # Case-insensitive search
    for p in mask_dir.iterdir():
        if p.stem.lower() == image_stem.lower():
            return p
    return None


# ── Main conversion ───────────────────────────────────────────────────────────

def convert_split(
    img_dir:    Path,
    mask_dir:   Path,
    out_img_dir: Path,
    out_lbl_dir: Path,
    min_disc_area_ratio: float = 0.001,
) -> dict:
    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_lbl_dir.mkdir(parents=True, exist_ok=True)

    images = [p for p in sorted(img_dir.iterdir()) if p.suffix.lower() in _image_extensions()]
    stats  = {"processed": 0, "no_mask": 0, "no_disc": 0, "with_cup": 0}

    for img_path in tqdm(images, desc=f"  {img_dir.parent.name}"):
        mask_path = _find_mask(img_path.stem, mask_dir)

        if mask_path is None:
            stats["no_mask"] += 1
            continue

        disc_mask, cup_mask = _parse_refuge2_mask(mask_path)

        if disc_mask is None or not disc_mask.any():
            stats["no_disc"] += 1
            continue

        h, w = disc_mask.shape
        if disc_mask.sum() / 255 < min_disc_area_ratio * h * w:
            stats["no_disc"] += 1
            continue

        disc_bbox = _mask_to_bbox(disc_mask)
        if disc_bbox is None:
            stats["no_disc"] += 1
            continue

        lines = [f"0 {disc_bbox[0]:.6f} {disc_bbox[1]:.6f} {disc_bbox[2]:.6f} {disc_bbox[3]:.6f}"]

        if cup_mask is not None and cup_mask.any():
            cup_bbox = _mask_to_bbox(cup_mask)
            if cup_bbox is not None:
                lines.append(f"1 {cup_bbox[0]:.6f} {cup_bbox[1]:.6f} {cup_bbox[2]:.6f} {cup_bbox[3]:.6f}")
                stats["with_cup"] += 1

        # Copy image
        dest_img = out_img_dir / img_path.name
        shutil.copy2(img_path, dest_img)

        # Write label
        (out_lbl_dir / f"{img_path.stem}.txt").write_text("\n".join(lines))
        stats["processed"] += 1

    return stats


def write_yaml(output_dir: Path, splits: list[str]) -> Path:
    lines = [
        f"path: {output_dir}",
        "train: images/train",
        "val:   images/val" if "val" in splits else "val: images/train",
        "",
        "nc: 2",
        "names:",
        "  0: optic_disc",
        "  1: optic_cup",
    ]
    yaml_path = output_dir / "optic_disc.yaml"
    yaml_path.write_text("\n".join(lines))
    return yaml_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert REFUGE2 masks to YOLO format")
    parser.add_argument("--refuge-dir",  required=True, help="REFUGE2 dataset root")
    parser.add_argument("--output-dir",  required=True, help="Output directory for YOLO dataset")
    parser.add_argument("--min-disc-area-ratio", type=float, default=0.001,
                        help="Min disc area as fraction of image area (filters noise)")
    args = parser.parse_args()

    root       = Path(args.refuge_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Detecting dataset structure in: {root}")
    structure = _detect_structure(root)

    if not structure:
        raise RuntimeError(
            f"Could not detect dataset structure in {root}. "
            "Expected images/ + masks/ or Training400/ folders."
        )

    print(f"Detected splits: {list(structure.keys())}")

    converted_splits = []
    for split, (img_dir, mask_dir) in structure.items():
        if img_dir is None or not img_dir.exists():
            print(f"  Skipping split '{split}' — image dir not found: {img_dir}")
            continue
        if not mask_dir.exists():
            print(f"  WARNING: mask dir not found: {mask_dir} — skipping {split}")
            continue

        print(f"\nConverting split: {split}")
        print(f"  images: {img_dir}")
        print(f"  masks:  {mask_dir}")

        stats = convert_split(
            img_dir, mask_dir,
            output_dir / "images" / split,
            output_dir / "labels" / split,
            min_disc_area_ratio=args.min_disc_area_ratio,
        )

        converted_splits.append(split)
        print(f"  processed={stats['processed']}  no_mask={stats['no_mask']}  "
              f"no_disc={stats['no_disc']}  with_cup={stats['with_cup']}")

    if not converted_splits:
        raise RuntimeError("No splits could be converted. Check dataset structure.")

    yaml_path = write_yaml(output_dir, converted_splits)
    print(f"\nYAML config written to: {yaml_path}")
    print(f"Dataset ready at: {output_dir}")
    print(f"\nNext step:\n  python train_yolo.py --data {yaml_path} --output-dir <output>")


if __name__ == "__main__":
    main()
