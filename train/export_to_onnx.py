"""
Export EfficientNet-B4 PyTorch checkpoint to ONNX format.

Usage:
    python export_to_onnx.py \\
        --checkpoint /kaggle/working/efficientnet_b4_aptos.pt \\
        --output     /kaggle/working/fundoscopy_efficientnet_b4_v1.onnx

After export, copy the .onnx file to neurovision/backend/models/:
    cp fundoscopy_efficientnet_b4_v1.onnx <project>/neurovision/backend/models/

The script also writes model_metadata.json next to the .onnx file.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import timm


def export(checkpoint_path: str, output_path: str) -> None:
    ckpt_path = Path(checkpoint_path)
    out_path  = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Load checkpoint ───────────────────────────────────────────────────────
    print(f"Loading checkpoint: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)

    val_auc    = ckpt.get("val_auc")
    val_f1     = ckpt.get("val_f1")
    trained_at = ckpt.get("trained_at")
    label_map  = ckpt.get("label_map", [])
    model_name = ckpt.get("model_name", "efficientnet_b4")
    num_classes = ckpt.get("num_classes", 5)
    image_size  = ckpt.get("image_size", 512)

    print(f"  model_name={model_name}  num_classes={num_classes}")
    print(f"  val_auc={val_auc}  val_f1={val_f1}  trained_at={trained_at}")

    # ── Rebuild model ─────────────────────────────────────────────────────────
    model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    # ── Export ────────────────────────────────────────────────────────────────
    dummy = torch.randn(1, 3, image_size, image_size)

    print(f"\nExporting to ONNX (opset 17, legacy exporter)...")
    torch.onnx.export(
        model,
        dummy,
        str(out_path),
        opset_version=17,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={
            "image":  {0: "batch_size"},
            "logits": {0: "batch_size"},
        },
        dynamo=False,  # use legacy exporter — stable on Windows cp1252 terminals
    )
    print(f"  Saved: {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")

    # ── Validate: PyTorch vs ONNX output consistency ──────────────────────────
    try:
        import onnxruntime as ort
    except ImportError:
        print("\nWARNING: onnxruntime not installed — skipping validation.")
        print("Install with: pip install onnxruntime")
    else:
        print("\nValidating PyTorch ↔ ONNX consistency...")
        session = ort.InferenceSession(
            str(out_path), providers=["CPUExecutionProvider"]
        )

        with torch.no_grad():
            pt_out = model(dummy).numpy()

        ort_out  = session.run(None, {"image": dummy.numpy()})[0]
        max_diff = float(np.abs(pt_out - ort_out).max())

        if max_diff >= 1e-4:
            print(f"  ERROR: max diff = {max_diff:.2e} exceeds threshold 1e-4")
            sys.exit(1)

        print(f"  max |PT - ONNX| = {max_diff:.2e}  ✓")

    # ── SHA-256 ───────────────────────────────────────────────────────────────
    with open(out_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    # ── model_metadata.json ───────────────────────────────────────────────────
    metadata = {
        "model_name":   "fundoscopy_efficientnet_b4_v1",
        "version":      "1.0.0",
        "architecture": model_name,
        "dataset":      "APTOS 2019 (Kaggle: aptos2019-blindness-detection)",
        "classes":      label_map or [
            "normal", "dr_mild", "dr_moderate", "dr_severe", "dr_proliferative"
        ],
        "input_shape":  [1, 3, image_size, image_size],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std":  [0.229, 0.224, 0.225],
        },
        "confidence_threshold": 0.60,
        "val_auc":    val_auc,
        "val_f1":     val_f1,
        "trained_at": trained_at,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "sha256":      sha256,
        "onnx_opset":  17,
        "onnx_max_diff_from_pytorch": round(max_diff, 10) if "max_diff" in dir() else None,
    }

    metadata_path = out_path.parent / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSHA-256:  {sha256}")
    print(f"Metadata: {metadata_path}")
    print(f"\nDone. Copy both files to neurovision/backend/models/:")
    print(f"  {out_path.name}")
    print(f"  model_metadata.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export EfficientNet-B4 checkpoint to ONNX"
    )
    parser.add_argument(
        "--checkpoint",
        default="/kaggle/working/efficientnet_b4_aptos.pt",
        help="Path to trained PyTorch checkpoint (.pt)",
    )
    parser.add_argument(
        "--output",
        default="/kaggle/working/fundoscopy_efficientnet_b4_v1.onnx",
        help="Output path for the ONNX file",
    )
    args = parser.parse_args()
    export(args.checkpoint, args.output)
