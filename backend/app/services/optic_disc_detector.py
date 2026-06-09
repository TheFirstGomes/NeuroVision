"""
OpticDiscDetector — YOLOv8 ONNX Runtime inference for optic disc/cup detection.

Produced by train/train_yolo.py from the REFUGE2 dataset.
Placed at: backend/models/optic_disc_yolov8.onnx

Detects:
  class 0 — optic disc  (entire disc region)
  class 1 — optic cup   (inner excavation)

Returns OpticDiscResult with:
  - disc_bbox / cup_bbox (xmin, ymin, xmax, ymax — pixel coordinates)
  - disc_confidence / cup_confidence
  - cup_disc_ratio  (vertical CDR — key glaucoma marker)
  - disc_crop_bytes (JPEG crop of disc region, ready for downstream analysis)

Raises:
  ModelNotAvailable — ONNX file absent or onnxruntime not installed
"""
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import structlog
from PIL import Image

logger = structlog.get_logger(__name__)

_DEFAULT_YOLO_MODEL = (
    Path(__file__).parent.parent.parent / "models" / "optic_disc_yolov8.onnx"
)
_YOLO_IMGSZ = 640


# ── Exceptions ────────────────────────────────────────────────────────────────

class ModelNotAvailable(Exception):
    pass


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class BBox:
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    confidence: float

    @property
    def width(self) -> int:
        return self.xmax - self.xmin

    @property
    def height(self) -> int:
        return self.ymax - self.ymin


@dataclass
class OpticDiscResult:
    disc_bbox:        Optional[BBox]
    cup_bbox:         Optional[BBox]
    cup_disc_ratio:   Optional[float]   # vertical CDR = cup_h / disc_h
    disc_crop_bytes:  Optional[bytes]   # JPEG crop of disc (with margin)
    disc_confidence:  float = 0.0
    cup_confidence:   float = 0.0

    @property
    def disc_detected(self) -> bool:
        return self.disc_bbox is not None

    @property
    def cup_detected(self) -> bool:
        return self.cup_bbox is not None

    def glaucoma_risk(self) -> str:
        if self.cup_disc_ratio is None:
            return "indeterminado"
        if self.cup_disc_ratio >= 0.80:
            return "alto"
        if self.cup_disc_ratio >= 0.65:
            return "moderado"
        if self.cup_disc_ratio >= 0.50:
            return "baixo"
        return "normal"


# ── Preprocessing ─────────────────────────────────────────────────────────────

def _preprocess(image_data: bytes) -> tuple[np.ndarray, int, int]:
    img = Image.open(io.BytesIO(image_data)).convert("RGB")
    orig_w, orig_h = img.size
    img = img.resize((_YOLO_IMGSZ, _YOLO_IMGSZ), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr.transpose(2, 0, 1)[np.newaxis], orig_w, orig_h   # (1,3,640,640)


def _postprocess(
    output:      np.ndarray,
    orig_w:      int,
    orig_h:      int,
    conf_thresh: float = 0.25,
) -> list[tuple[int, BBox]]:
    """
    Decode YOLOv8 ONNX output → list of (class_id, BBox).

    YOLOv8 with num_classes=2 exports shape (1, 6, 8400):
      6 = 4 bbox coords + 2 class scores.
    After removing batch dim: (6, 8400). We transpose to (8400, 6).
    Each row: [xc, yc, w, h, cls0_conf, cls1_conf].
    """
    preds = output[0]
    # Normalise to (N, 4+num_classes): rows = anchors, cols = coords+scores
    if preds.shape[0] < preds.shape[-1]:
        preds = preds.T

    results = []
    scale_x = orig_w / _YOLO_IMGSZ
    scale_y = orig_h / _YOLO_IMGSZ

    for row in preds:
        x_c, y_c, w, h = row[:4]
        class_scores   = row[4:]
        cls_id         = int(np.argmax(class_scores))
        conf           = float(class_scores[cls_id])

        if conf < conf_thresh:
            continue

        xmin = max(0, int((x_c - w / 2) * scale_x))
        ymin = max(0, int((y_c - h / 2) * scale_y))
        xmax = min(orig_w, int((x_c + w / 2) * scale_x))
        ymax = min(orig_h, int((y_c + h / 2) * scale_y))

        if xmax <= xmin or ymax <= ymin:
            continue

        results.append((cls_id, BBox(xmin, ymin, xmax, ymax, round(conf, 3))))

    return results


def _best_per_class(detections: list[tuple[int, BBox]]) -> dict[int, BBox]:
    by_class: dict[int, BBox] = {}
    for cls_id, bbox in detections:
        if cls_id not in by_class or bbox.confidence > by_class[cls_id].confidence:
            by_class[cls_id] = bbox
    return by_class


def _crop_disc(image_data: bytes, disc_bbox: BBox, margin: float = 0.15) -> bytes:
    img  = Image.open(io.BytesIO(image_data)).convert("RGB")
    w, h = img.size
    mx   = int(disc_bbox.width * margin)
    my   = int(disc_bbox.height * margin)
    crop = img.crop((
        max(0, disc_bbox.xmin - mx),
        max(0, disc_bbox.ymin - my),
        min(w, disc_bbox.xmax + mx),
        min(h, disc_bbox.ymax + my),
    ))
    buf = io.BytesIO()
    crop.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


# ── Main service ──────────────────────────────────────────────────────────────

class OpticDiscDetector:
    """
    YOLOv8-based optic disc and cup detector (ONNX Runtime).
    Instantiate via OpticDiscDetector.load().
    """

    CONF_THRESHOLD: float = 0.30

    def __init__(self, session: object, model_path: Path) -> None:
        self._session    = session
        self._model_path = model_path

    @classmethod
    def load(cls, model_path: Optional[Path] = None) -> "OpticDiscDetector":
        path = model_path or _DEFAULT_YOLO_MODEL
        if not path.exists():
            raise ModelNotAvailable(f"YOLO ONNX model not found: {path}")
        try:
            import onnxruntime as ort
        except ImportError:
            raise ModelNotAvailable("onnxruntime is not installed")
        try:
            session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        except Exception as exc:
            raise ModelNotAvailable(f"Failed to load YOLO ONNX: {exc}") from exc
        logger.info("optic_disc_detector.loaded", path=str(path))
        return cls(session, path)

    def detect(self, image_data: bytes) -> OpticDiscResult:
        tensor, orig_w, orig_h = _preprocess(image_data)
        input_name = self._session.get_inputs()[0].name
        outputs    = self._session.run(None, {input_name: tensor})

        raw   = _postprocess(outputs[0], orig_w, orig_h, conf_thresh=self.CONF_THRESHOLD)
        best  = _best_per_class(raw)

        disc_bbox = best.get(0)
        cup_bbox  = best.get(1)

        cdr = None
        if disc_bbox and cup_bbox and disc_bbox.height > 0:
            cdr = round(cup_bbox.height / disc_bbox.height, 3)

        disc_crop = _crop_disc(image_data, disc_bbox) if disc_bbox else None

        result = OpticDiscResult(
            disc_bbox       = disc_bbox,
            cup_bbox        = cup_bbox,
            cup_disc_ratio  = cdr,
            disc_crop_bytes = disc_crop,
            disc_confidence = disc_bbox.confidence if disc_bbox else 0.0,
            cup_confidence  = cup_bbox.confidence  if cup_bbox  else 0.0,
        )

        logger.info(
            "optic_disc_detector.result",
            disc_detected  = result.disc_detected,
            disc_conf      = result.disc_confidence,
            cup_detected   = result.cup_detected,
            cdr            = cdr,
            glaucoma_risk  = result.glaucoma_risk(),
        )

        return result
