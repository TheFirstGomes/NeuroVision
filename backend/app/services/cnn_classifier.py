"""
CNNClassifier — EfficientNet-B4 ONNX Runtime inference for fundoscopy.

Produced by train/train_efficientnet.py + train/export_to_onnx.py.
Placed at: backend/models/fundoscopy_efficientnet_b4_v1.onnx

Returns CNNResult (class_name, confidence).
ClassifierService converts CNNResult → ClassificationResult.

Raises:
  ModelNotAvailable  — ONNX file absent or onnxruntime not installed
  LowConfidence      — softmax confidence below CONFIDENCE_THRESHOLD (0.60)
"""
import io
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import structlog
from PIL import Image

logger = structlog.get_logger(__name__)

# ImageNet normalization — must match train/train_efficientnet.py
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Class names in the order the model was trained (diagnosis 0-4 in APTOS)
CLASSES = ["normal", "dr_mild", "dr_moderate", "dr_severe", "dr_proliferative"]

# Metadata used by ClassifierService to build ClassificationResult
CNN_CLASS_META: dict[str, dict] = {
    "normal": {
        "condition":         "Fundo de Olho Normal",
        "condition_en":      "Normal Fundus",
        "severity":          "normal",
        "neurological_flag": False,
        "neurological_note": "",
        "features_detected": ["Sem achados patológicos identificados pela CNN"],
        "structures":        ["retina", "disco_optico", "macula"],
        "rag_query": (
            "Como é um fundo de olho normal e quais são os principais marcos "
            "anatômicos visíveis na fundoscopia?"
        ),
    },
    "dr_mild": {
        "condition":         "Retinopatia Diabética Não-Proliferativa Leve",
        "condition_en":      "Mild Non-Proliferative Diabetic Retinopathy",
        "severity":          "leve",
        "neurological_flag": True,
        "neurological_note": (
            "A RD é manifestação ocular de neuropatia diabética sistêmica. "
            "Microaneurismas indicam dano à microvasculatura retiniana por "
            "hiperglicemia crônica."
        ),
        "features_detected": ["Microaneurismas identificados pela CNN (APTOS grade 1)"],
        "structures":        ["retina", "macula"],
        "rag_query": (
            "O que é retinopatia diabética leve, como classificar sua gravidade "
            "e qual sua relação com neuropatia diabética?"
        ),
    },
    "dr_moderate": {
        "condition":         "Retinopatia Diabética Não-Proliferativa Moderada",
        "condition_en":      "Moderate Non-Proliferative Diabetic Retinopathy",
        "severity":          "moderado",
        "neurological_flag": True,
        "neurological_note": (
            "RD moderada indica progressão da microangiopatia. Exsudatos e "
            "hemorragias retinianas sinalizam comprometimento vascular crescente."
        ),
        "features_detected": [
            "Hemorragias retinianas e/ou exsudatos identificados pela CNN (APTOS grade 2)"
        ],
        "structures":        ["retina", "macula"],
        "rag_query": (
            "O que é retinopatia diabética moderada, quais são as indicações de "
            "tratamento e como prevenir a progressão?"
        ),
    },
    "dr_severe": {
        "condition":         "Retinopatia Diabética Não-Proliferativa Grave",
        "condition_en":      "Severe Non-Proliferative Diabetic Retinopathy",
        "severity":          "grave",
        "neurological_flag": True,
        "neurological_note": (
            "RD grave indica alto risco de progressão para a forma proliferativa "
            "com perda visual severa. Encaminhamento urgente ao retinologista."
        ),
        "features_detected": [
            "Múltiplas hemorragias e anomalias microvasculares (APTOS grade 3)"
        ],
        "structures":        ["retina", "macula"],
        "rag_query": (
            "O que é retinopatia diabética grave, quais são os critérios de "
            "encaminhamento urgente e as opções terapêuticas?"
        ),
    },
    "dr_proliferative": {
        "condition":         "Retinopatia Diabética Proliferativa",
        "condition_en":      "Proliferative Diabetic Retinopathy",
        "severity":          "grave",
        "neurological_flag": True,
        "neurological_note": (
            "Forma mais avançada de RD. Neovascularização indica isquemia retiniana "
            "grave com alto risco de hemorragia vítrea e descolamento de retina tracional."
        ),
        "features_detected": [
            "Neovascularização retiniana identificada pela CNN (APTOS grade 4)"
        ],
        "structures":        ["retina", "macula", "disco_optico"],
        "rag_query": (
            "O que é retinopatia diabética proliferativa, quais são as complicações "
            "graves e como tratar com fotocoagulação e injeções intravítreas?"
        ),
    },
}


# ── Exceptions ────────────────────────────────────────────────────────────────

class ModelNotAvailable(Exception):
    """ONNX model file is absent or onnxruntime is not installed."""


class LowConfidence(Exception):
    """Softmax confidence is below CONFIDENCE_THRESHOLD."""

    def __init__(self, confidence: float) -> None:
        self.confidence = confidence
        super().__init__(f"CNN confidence {confidence:.3f} below threshold")


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class CNNResult:
    class_name: str    # key into CNN_CLASS_META
    confidence: float  # softmax probability of the winning class


# ── Classifier ────────────────────────────────────────────────────────────────

class CNNClassifier:
    """
    ONNX Runtime wrapper for EfficientNet-B4 fundoscopy classification.

    Instantiate via CNNClassifier.load(path) — never directly.
    Covers DR grades 0-4 (normal → proliferative). Other fundus
    conditions (glaucoma, DMRI, papiledema) are handled by Tier 1/2.
    """

    CONFIDENCE_THRESHOLD: float = 0.60

    def __init__(self, session: object, model_path: Path) -> None:
        self._session    = session
        self._model_path = model_path

    @classmethod
    def load(cls, model_path: Path) -> "CNNClassifier":
        """
        Load the ONNX session from model_path.
        Raises ModelNotAvailable when file is missing or onnxruntime unavailable.
        """
        if not model_path.exists():
            raise ModelNotAvailable(f"ONNX model not found: {model_path}")

        try:
            import onnxruntime as ort
        except ImportError:
            raise ModelNotAvailable("onnxruntime is not installed")

        try:
            session = ort.InferenceSession(
                str(model_path),
                providers=["CPUExecutionProvider"],
            )
        except Exception as exc:
            raise ModelNotAvailable(f"Failed to load ONNX session: {exc}") from exc

        logger.info("cnn_classifier.loaded", path=str(model_path))
        return cls(session, model_path)

    def classify(self, image_data: bytes) -> CNNResult:
        """
        Run inference on raw image bytes.
        Raises LowConfidence when max softmax probability < CONFIDENCE_THRESHOLD.
        """
        tensor = _preprocess(image_data)
        logits = self._session.run(None, {"image": tensor})[0]   # (1, 5)
        probs  = _softmax(logits[0])
        idx    = int(np.argmax(probs))
        conf   = float(probs[idx])

        logger.info(
            "cnn_classifier.inference",
            class_name=CLASSES[idx],
            confidence=round(conf, 3),
            all_probs={c: round(float(p), 3) for c, p in zip(CLASSES, probs)},
        )

        if conf < self.CONFIDENCE_THRESHOLD:
            raise LowConfidence(conf)

        return CNNResult(class_name=CLASSES[idx], confidence=round(conf, 3))


# ── Helpers (module-level for testability) ────────────────────────────────────

def _preprocess(image_data: bytes) -> np.ndarray:
    """Resize to 512×512, normalize with ImageNet stats, return NCHW float32."""
    img = Image.open(io.BytesIO(image_data)).convert("RGB")
    img = img.resize((512, 512), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = (arr - _MEAN) / _STD
    return arr.transpose(2, 0, 1)[np.newaxis]   # (1, 3, 512, 512)


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp     = np.exp(shifted)
    return exp / exp.sum()
