"""
train_yolo.py — Train YOLOv8n on optic disc/cup detection (REFUGE2 dataset).

Workflow:
  1. Run prepare_refuge_yolo.py first to convert masks to YOLO format
  2. Train YOLOv8n with early stopping (patience=10) on the prepared dataset
  3. Export best.pt to ONNX opset 17
  4. Copy ONNX + metadata to backend/models/

Expected runtime: ~15 min on GPU for 50 epochs with 400 training images.

CLI usage:
  python train_yolo.py \\
    --data C:/datasets/refuge2_yolo/optic_disc.yaml \\
    --output-dir C:/neurovision/train/yolo_output \\
    --epochs 50
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _install_ultralytics() -> None:
    import importlib.util
    if importlib.util.find_spec("ultralytics") is None:
        print("Installing ultralytics...")
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics"])


def train_and_export(
    data_yaml:  str,
    output_dir: Path,
    model_name: str = "yolov8n",
    epochs:     int = 50,
    imgsz:      int = 640,
    batch:      int = 16,
    patience:   int = 10,
    seed:       int = 42,
    copy_backend: bool = True,
) -> None:
    _install_ultralytics()
    from ultralytics import YOLO

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("YOLOv8 Optic Disc/Cup Detection Training")
    print(f"  data:    {data_yaml}")
    print(f"  model:   {model_name}  |  epochs: {epochs}  |  imgsz: {imgsz}  |  batch: {batch}")
    print("=" * 60)

    model   = YOLO(f"{model_name}.pt")
    results = model.train(
        data     = data_yaml,
        epochs   = epochs,
        imgsz    = imgsz,
        batch    = batch,
        patience = patience,
        seed     = seed,
        project  = str(output_dir),
        name     = "optic_disc_yolo",
        exist_ok = True,
        device   = 0,
        amp      = True,
        workers  = 4,
        verbose  = True,
    )

    best_pt = Path(results.save_dir) / "weights" / "best.pt"
    if not best_pt.exists():
        raise FileNotFoundError(f"best.pt not found at {best_pt}")
    print(f"\nBest checkpoint: {best_pt}")

    # Export to ONNX
    exp_model = YOLO(str(best_pt))
    exp_model.export(
        format   = "onnx",
        imgsz    = imgsz,
        opset    = 17,
        dynamic  = False,
        simplify = True,
    )
    onnx_src = best_pt.with_suffix(".onnx")
    if not onnx_src.exists():
        raise FileNotFoundError(f"ONNX export not found at {onnx_src}")

    onnx_dst = output_dir / "optic_disc_yolov8.onnx"
    shutil.copy2(onnx_src, onnx_dst)
    print(f"ONNX model: {onnx_dst}  ({onnx_dst.stat().st_size / 1e6:.1f} MB)")

    # Write metadata
    metrics  = getattr(results, "results_dict", {}) or {}
    metadata = {
        "model":      model_name,
        "task":       "optic_disc_cup_detection",
        "dataset":    "REFUGE2",
        "classes":    {"0": "optic_disc", "1": "optic_cup"},
        "imgsz":      imgsz,
        "map50":      round(float(metrics.get("metrics/mAP50(B)", 0.0)), 4),
        "map50_95":   round(float(metrics.get("metrics/mAP50-95(B)", 0.0)), 4),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sha256":     _sha256(onnx_dst),
        "onnx_opset": 17,
    }
    meta_path = output_dir / "yolo_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))

    if copy_backend:
        script_dir  = Path(__file__).parent
        backend_dir = script_dir.parent / "backend" / "models"
        backend_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(onnx_dst, backend_dir / onnx_dst.name)
        shutil.copy2(meta_path, backend_dir / meta_path.name)
        print(f"Copied to backend/models/")

    print(f"\nDone.  mAP50={metadata['map50']}  mAP50-95={metadata['map50_95']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv8 for optic disc detection")
    parser.add_argument("--data",       required=True, help="Path to optic_disc.yaml")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--model",      default="yolov8n")
    parser.add_argument("--epochs",     type=int, default=50)
    parser.add_argument("--imgsz",      type=int, default=640)
    parser.add_argument("--batch",      type=int, default=16)
    parser.add_argument("--patience",   type=int, default=10)
    parser.add_argument("--seed",       type=int, default=42)
    parser.add_argument("--no-copy-backend", action="store_true")
    args = parser.parse_args()

    train_and_export(
        data_yaml    = args.data,
        output_dir   = Path(args.output_dir),
        model_name   = args.model,
        epochs       = args.epochs,
        imgsz        = args.imgsz,
        batch        = args.batch,
        patience     = args.patience,
        seed         = args.seed,
        copy_backend = not args.no_copy_backend,
    )


if __name__ == "__main__":
    main()
