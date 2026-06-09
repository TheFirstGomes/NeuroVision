"""
Fundoscopy Image Classifier for NeuroVision.

Three-tier classification pipeline:

  Tier 0 — CNN / EfficientNet-B4 (ONNX Runtime)
    Requires backend/models/fundoscopy_efficientnet_b4_v1.onnx.
    Fine-tuned on APTOS 2019. Covers DR grades 0–4 (normal → proliferative).
    Skipped when model file is absent or confidence < 0.60.

  Tier 1 — Claude Vision (claude-haiku-4-5)
    Requires ANTHROPIC_API_KEY in environment.
    Sends the fundoscopy image to Claude with a structured ophthalmology prompt
    and parses the JSON response into a ClassificationResult.
    Covers all conditions including glaucoma, DMRI, papiledema.

  Tier 2 — Feature-Based Fallback
    Pure Pillow/NumPy. Analyzes color histograms, channel statistics, and
    texture features to detect signs of RD, Glaucoma, DMRI, Papiledema, Normal.
    Used automatically when Tier 0 and Tier 1 are unavailable or fail.

Conditions covered by each tier:
  CNN      — Normal, RD leve/moderada/grave/proliferativa
  Vision   — Normal, RD, Glaucoma, DMRI, Papiledema (+ any edge case)
  Feature  — Normal, RD, Glaucoma, DMRI, Papiledema
"""
import io
import json
import base64
import structlog
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from PIL import Image, ImageFilter

from app.services.cnn_classifier import (
    CNNClassifier,
    CNNResult,
    CNN_CLASS_META,
    ModelNotAvailable,
    LowConfidence,
)
from app.services.optic_disc_detector import (
    OpticDiscDetector,
    OpticDiscResult,
    ModelNotAvailable as YOLOModelNotAvailable,
)

logger = structlog.get_logger(__name__)

_DEFAULT_CNN_MODEL = (
    Path(__file__).parent.parent.parent / "models" / "fundoscopy_efficientnet_b4_v1.onnx"
)
_DEFAULT_YOLO_MODEL = (
    Path(__file__).parent.parent.parent / "models" / "optic_disc_yolov8.onnx"
)

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ClassificationResult:
    condition: str
    condition_en: str
    confidence: float          # 0.0 – 1.0
    severity: str              # "normal" | "leve" | "moderado" | "grave" | "suspeito"
    neurological_flag: bool
    neurological_note: str
    features_detected: list[str]
    rag_query: str             # Pre-built query for RAG explanation
    related_structures: list[str]
    classifier_method: str = "feature_based"   # "claude_vision" | "feature_based"
    # Optic disc detection (populated when YOLO model is available)
    disc_detected:     bool           = False
    cup_disc_ratio:    Optional[float] = None   # vertical CDR — glaucoma marker
    glaucoma_risk:     Optional[str]   = None   # "normal" | "baixo" | "moderado" | "alto"
    disc_confidence:   float           = 0.0
    disclaimer: str = field(default=(
        "Resultado gerado por análise de imagem para fins educacionais. "
        "Não substitui avaliação clínica por oftalmologista."
    ))


# ── Claude Vision prompt ──────────────────────────────────────────────────────

_VISION_PROMPT = """\
You are an expert neuro-ophthalmologist analyzing a fundoscopy (fundus photograph) \
for an educational medical platform.

Analyze this retinal image carefully. Return ONLY a valid JSON object — \
no markdown fences, no explanation outside JSON — with this exact structure:

{
  "condition": "<Nome em português da condição identificada>",
  "condition_en": "<Condition name in English>",
  "confidence": <float 0.0–1.0>,
  "severity": "<one of: normal | leve | moderado | grave | suspeito>",
  "neurological_flag": <true or false>,
  "neurological_note": "<Neurological connection if present, else empty string>",
  "features_detected": ["<feature1>", "<feature2>"],
  "related_structures": ["<structureId1>", "<structureId2>"]
}

Conditions to consider:
- Fundo de Olho Normal
- Retinopatia Diabética (specify stage: não-proliferativa leve/moderada/grave or proliferativa)
- Suspeita de Glaucoma (cupping, pallor, RNFL defects)
- Degeneração Macular Relacionada à Idade — DMRI (dry/wet)
- Suspeita de Papiledema (disc swelling, blurred margins, flame hemorrhages)

For features_detected list observable findings: microaneurysms, hard exudates, \
soft exudates, flame hemorrhages, neovascularization, increased cup/disc ratio, \
disc pallor, drusen, geographic atrophy, subretinal fluid, disc swelling, \
blurred disc margins, macular edema, etc.

For related_structures use ONLY these exact IDs (pick the most relevant 1–3):
  retina, macula, disco_optico, nervo_optico, quiasma_optico, \
  corpo_geniculado_lateral, cortex_visual

This analysis is STRICTLY EDUCATIONAL. Be precise and educational."""


# ── Condition metadata (used by feature-based tier) ──────────────────────────

CONDITION_META = {
    "normal": {
        "label": "Fundo de Olho Normal",
        "label_en": "Normal Fundus",
        "neurological": False,
        "neuro_note": "",
        "structures": ["retina", "disco_optico", "macula"],
        "rag_query": "Como é um fundo de olho normal e quais são os principais marcos anatômicos visíveis na fundoscopia?",
    },
    "retinopatia_diabetica": {
        "label": "Retinopatia Diabética",
        "label_en": "Diabetic Retinopathy",
        "neurological": True,
        "neuro_note": "A RD é manifestação ocular de neuropatia diabética sistêmica. Microaneurismas indicam dano à microvasculatura retiniana por hiperglicemia crônica.",
        "structures": ["retina", "macula"],
        "rag_query": "O que é retinopatia diabética, como classificar sua gravidade e qual sua relação com neuropatia diabética?",
    },
    "glaucoma": {
        "label": "Suspeita de Glaucoma",
        "label_en": "Glaucoma Suspect",
        "neurological": True,
        "neuro_note": "Glaucoma é neuropatia óptica progressiva com perda de células ganglionares da retina. O dano axonal no nervo óptico é irreversível.",
        "structures": ["nervo_optico", "disco_optico"],
        "rag_query": "O que é glaucoma, como a escavação óptica é avaliada e qual a relação com dano ao nervo óptico?",
    },
    "dmri": {
        "label": "Degeneração Macular (DMRI)",
        "label_en": "Age-Related Macular Degeneration",
        "neurological": True,
        "neuro_note": "A DMRI acomete a mácula, região de maior densidade de cones. Pesquisas recentes ligam DMRI a mecanismos neuroinflamatórios similares ao Alzheimer.",
        "structures": ["macula", "retina"],
        "rag_query": "O que é degeneração macular relacionada à idade, quais são os tipos seco e úmido e como tratar?",
    },
    "papiledema": {
        "label": "Suspeita de Papiledema",
        "label_en": "Papilledema Suspect",
        "neurological": True,
        "neuro_note": "Papiledema bilateral indica hipertensão intracraniana — emergência neurológica. O nervo óptico é circundado por espaço subaracnóideo conectado ao espaço intracraniano.",
        "structures": ["disco_optico", "nervo_optico"],
        "rag_query": "O que é papiledema, como diferenciá-lo de papilite e quais são as causas de hipertensão intracraniana?",
    },
}

SEVERITY_MAP = {
    "normal":                { (0.0, 1.0):  "normal" },
    "retinopatia_diabetica": { (0.0, 0.4): "leve", (0.4, 0.65): "moderado", (0.65, 1.0): "grave" },
    "glaucoma":              { (0.0, 0.5): "leve", (0.5, 0.75): "moderado", (0.75, 1.0): "grave" },
    "dmri":                  { (0.0, 0.5): "leve", (0.5, 0.75): "moderado", (0.75, 1.0): "grave" },
    "papiledema":            { (0.0, 0.5): "suspeito", (0.5, 1.0): "grave" },
}


# ── Feature extraction (Tier 2) ───────────────────────────────────────────────

def _load_image(data: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img = img.resize((512, 512), Image.LANCZOS)
    return np.array(img, dtype=np.float32) / 255.0


def _extract_features(img: np.ndarray) -> dict:
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    h, w = img.shape[:2]
    cy, cx = h // 2, w // 2
    radius = min(h, w) // 6

    brightness    = float(np.mean(img))
    red_mean      = float(np.mean(r))
    green_mean    = float(np.mean(g))
    red_dominance = red_mean - (green_mean + float(np.mean(b))) / 2

    bright_mask      = (r > 0.85) & (g > 0.85) & (b > 0.85)
    bright_ratio     = float(np.mean(bright_mask))
    red_lesion_mask  = (r > 0.55) & (r > g * 1.35) & (r > b * 1.35)
    red_lesion_ratio = float(np.mean(red_lesion_mask))

    disc_region     = img[cy - radius:cy + radius, cx - radius:cx + radius]
    disc_brightness = float(np.mean(disc_region)) if disc_region.size > 0 else brightness
    disc_r          = float(np.mean(disc_region[:, :, 0])) if disc_region.size > 0 else red_mean
    cup_mask        = (disc_region[:, :, 0] > 0.88) & (disc_region[:, :, 1] > 0.88) if disc_region.size > 0 else np.array([False])
    cup_ratio       = float(np.mean(cup_mask))

    yellow_mask  = (r > 0.65) & (g > 0.55) & (b < 0.35) & (r > b * 1.8)
    yellow_ratio = float(np.mean(yellow_mask))

    pil_img = Image.fromarray((img * 255).astype(np.uint8))
    edges   = np.array(pil_img.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32) / 255.0
    disc_patch = edges[cy - radius:cy + radius, cx - radius:cx + radius]
    disc_edge_sharpness = float(np.mean(disc_patch)) if disc_patch.size > 0 else 0.0
    contrast = float(np.std(img))

    return {
        "brightness": brightness, "red_mean": red_mean, "green_mean": green_mean,
        "red_dominance": red_dominance, "bright_ratio": bright_ratio,
        "red_lesion_ratio": red_lesion_ratio, "disc_brightness": disc_brightness,
        "disc_r": disc_r, "cup_ratio": cup_ratio, "yellow_ratio": yellow_ratio,
        "disc_edge_sharpness": disc_edge_sharpness, "contrast": contrast,
    }


def _score_conditions(f: dict) -> dict[str, float]:
    scores = {"normal": 0.5, "retinopatia_diabetica": 0.0, "glaucoma": 0.0, "dmri": 0.0, "papiledema": 0.0}
    rd = 0.0
    if f["red_lesion_ratio"] > 0.04: rd += 0.35
    if f["red_lesion_ratio"] > 0.08: rd += 0.25
    if f["bright_ratio"] > 0.02:     rd += 0.20
    if f["bright_ratio"] > 0.05:     rd += 0.15
    if f["red_dominance"] > 0.08:    rd += 0.10
    scores["retinopatia_diabetica"] = min(rd, 1.0)

    gl = 0.0
    if f["cup_ratio"] > 0.25:        gl += 0.40
    if f["cup_ratio"] > 0.40:        gl += 0.30
    if f["disc_brightness"] > 0.70:  gl += 0.15
    if f["contrast"] > 0.18:         gl += 0.10
    scores["glaucoma"] = min(gl, 1.0)

    dm = 0.0
    if f["yellow_ratio"] > 0.04:     dm += 0.40
    if f["yellow_ratio"] > 0.08:     dm += 0.30
    if f["bright_ratio"] > 0.03:     dm += 0.15
    if f["brightness"] > 0.45:       dm += 0.10
    scores["dmri"] = min(dm, 1.0)

    pp = 0.0
    if f["disc_edge_sharpness"] < 0.06: pp += 0.35
    if f["disc_r"] > 0.65:             pp += 0.30
    if f["red_dominance"] > 0.06:      pp += 0.20
    scores["papiledema"] = min(pp, 1.0)

    max_path = max(scores["retinopatia_diabetica"], scores["glaucoma"], scores["dmri"], scores["papiledema"])
    scores["normal"] = max(0.0, 0.5 - max_path * 0.8)
    return scores


def _get_severity(condition: str, score: float) -> str:
    ranges = SEVERITY_MAP.get(condition, {})
    for (lo, hi), label in ranges.items():
        if lo <= score < hi:
            return label
    return list(ranges.values())[-1] if ranges else "indeterminado"


def _get_detected_features(features: dict, condition: str) -> list[str]:
    detected = []
    if features["red_lesion_ratio"] > 0.04:
        detected.append("Lesões hemorrágicas / microaneurismas detectados")
    if features["bright_ratio"] > 0.02:
        detected.append("Exsudatos brilhantes presentes")
    if features["cup_ratio"] > 0.25:
        detected.append(f"Escavação óptica aumentada (cup ratio ~{features['cup_ratio']:.0%})")
    if features["yellow_ratio"] > 0.04:
        detected.append("Depósitos amarelados compatíveis com drusas")
    if features["disc_edge_sharpness"] < 0.06 and condition == "papiledema":
        detected.append("Bordas do disco com baixa definição")
    if features["red_dominance"] > 0.08:
        detected.append("Hiperemia do disco óptico")
    return detected if detected else ["Sem achados patológicos evidentes"]


# ── Main service ──────────────────────────────────────────────────────────────

class ClassifierService:
    """
    Three-tier fundoscopy classifier.
    Tier 0: EfficientNet-B4 ONNX (if model file present — covers DR 0-4).
    Tier 1: Claude Vision API (if ANTHROPIC_API_KEY present — covers all conditions).
    Tier 2: Feature-based fallback (Pillow/NumPy — always available).
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        cnn_model_path: Optional[str] = None,
        yolo_model_path: Optional[str] = None,
    ) -> None:
        self._anthropic_key = anthropic_api_key or ""
        self._cnn:  Optional[CNNClassifier]    = None
        self._yolo: Optional[OpticDiscDetector] = None

        model_path = Path(cnn_model_path) if cnn_model_path else _DEFAULT_CNN_MODEL
        try:
            self._cnn = CNNClassifier.load(model_path)
            logger.info("classifier.cnn_enabled", path=str(model_path))
        except ModelNotAvailable as exc:
            logger.info("classifier.cnn_disabled", reason=str(exc))

        yolo_path = Path(yolo_model_path) if yolo_model_path else _DEFAULT_YOLO_MODEL
        try:
            self._yolo = OpticDiscDetector.load(yolo_path)
            logger.info("classifier.yolo_enabled", path=str(yolo_path))
        except YOLOModelNotAvailable as exc:
            logger.info("classifier.yolo_disabled", reason=str(exc))

        if self._anthropic_key:
            logger.info("classifier.vision_enabled", model="claude-haiku-4-5-20251001")
        else:
            logger.info("classifier.feature_based_mode", reason="ANTHROPIC_API_KEY not set")

    # ── Public ────────────────────────────────────────────────────────────────

    def classify(self, image_data: bytes) -> ClassificationResult:
        """
        Classify a fundoscopy image through the pipeline:
          Pre: YOLO optic disc detection (enriches result with CDR + glaucoma risk)
          Tier 0: EfficientNet-B4 CNN
          Tier 1: Claude Vision
          Tier 2: Feature-based fallback
        """
        logger.info("classifier.start", size_bytes=len(image_data))

        # Pre-step: YOLO optic disc/cup detection (optional, non-blocking)
        disc_result: Optional[OpticDiscResult] = None
        if self._yolo:
            try:
                disc_result = self._yolo.detect(image_data)
            except Exception as exc:
                logger.warning("classifier.yolo_failed", error=str(exc))

        # Tier 0: EfficientNet-B4 CNN
        if self._cnn:
            try:
                cnn_result = self._cnn.classify(image_data)
                result     = self._cnn_result_to_classification(cnn_result)
                logger.info(
                    "classifier.cnn_success",
                    condition=result.condition,
                    confidence=result.confidence,
                )
                return self._enrich_with_disc(result, disc_result)
            except LowConfidence as exc:
                logger.info(
                    "classifier.cnn_low_confidence",
                    confidence=exc.confidence,
                    next_tier="vision" if self._anthropic_key else "feature_based",
                )
            except Exception as exc:
                logger.warning(
                    "classifier.cnn_failed",
                    error=str(exc),
                    next_tier="vision" if self._anthropic_key else "feature_based",
                )

        # Tier 1: Claude Vision
        if self._anthropic_key:
            try:
                result = self._classify_with_vision(image_data)
                logger.info("classifier.vision_success", condition=result.condition, confidence=result.confidence)
                return self._enrich_with_disc(result, disc_result)
            except Exception as e:
                logger.warning("classifier.vision_failed", error=str(e), fallback="feature_based")

        # Tier 2: Feature-based fallback
        result = self._classify_feature_based(image_data)
        return self._enrich_with_disc(result, disc_result)

    # ── YOLO disc enrichment ─────────────────────────────────────────────────

    @staticmethod
    def _enrich_with_disc(
        result: ClassificationResult,
        disc: Optional[OpticDiscResult],
    ) -> ClassificationResult:
        """
        Attach YOLO disc detection data to any ClassificationResult.
        If CDR is high (>= 0.65) and the current condition is 'normal',
        adds a glaucoma suspicion note to features_detected.
        """
        if disc is None or not disc.disc_detected:
            return result

        result.disc_detected   = disc.disc_detected
        result.cup_disc_ratio  = disc.cup_disc_ratio
        result.glaucoma_risk   = disc.glaucoma_risk()
        result.disc_confidence = disc.disc_confidence

        # Elevate glaucoma suspicion when CDR is high but CNN said "normal"
        if (
            disc.cup_disc_ratio is not None
            and disc.cup_disc_ratio >= 0.65
            and "normal" in result.condition.lower()
        ):
            cdr_note = (
                f"YOLO detectou escavação óptica aumentada (CDR={disc.cup_disc_ratio:.2f}) "
                f"— risco de glaucoma: {disc.glaucoma_risk()}. "
                "Avaliação oftalmológica recomendada."
            )
            result.features_detected = [cdr_note] + result.features_detected
            result.neurological_flag = True
            if not result.neurological_note:
                result.neurological_note = (
                    "Escavação óptica aumentada detectada por visão computacional. "
                    "Glaucoma é neuropatia óptica progressiva e requer rastreamento periódico."
                )

        return result

    # ── Tier 0: CNN result → ClassificationResult ────────────────────────────

    def _cnn_result_to_classification(self, cnn_result: CNNResult) -> ClassificationResult:
        meta = CNN_CLASS_META[cnn_result.class_name]
        return ClassificationResult(
            condition=meta["condition"],
            condition_en=meta["condition_en"],
            confidence=cnn_result.confidence,
            severity=meta["severity"],
            neurological_flag=meta["neurological_flag"],
            neurological_note=meta["neurological_note"],
            features_detected=meta["features_detected"],
            rag_query=meta["rag_query"],
            related_structures=meta["structures"],
            classifier_method="efficientnet_b4_v1",
        )

    # ── Tier 1: Claude Vision ─────────────────────────────────────────────────

    def _classify_with_vision(self, image_data: bytes) -> ClassificationResult:
        import anthropic

        # Detect MIME type
        try:
            img_pil = Image.open(io.BytesIO(image_data))
            fmt = (img_pil.format or "JPEG").lower()
            mime = "image/png" if fmt == "png" else "image/jpeg"
        except Exception:
            mime = "image/jpeg"

        client   = anthropic.Anthropic(api_key=self._anthropic_key)
        b64_data = base64.standard_b64encode(image_data).decode("utf-8")

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": b64_data},
                    },
                    {"type": "text", "text": _VISION_PROMPT},
                ],
            }],
        )

        raw = message.content[0].text.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        return self._vision_response_to_result(data)

    def _vision_response_to_result(self, data: dict) -> ClassificationResult:
        """Map Claude's JSON response to ClassificationResult."""
        condition    = data.get("condition", "Indeterminado")
        condition_en = data.get("condition_en", "Undetermined")
        confidence   = max(0.0, min(1.0, float(data.get("confidence", 0.7))))
        severity     = data.get("severity", "indeterminado")
        neuro_flag   = bool(data.get("neurological_flag", False))
        neuro_note   = data.get("neurological_note", "")
        features     = data.get("features_detected", ["Análise por visão computacional"])
        structures   = data.get("related_structures", ["retina"])

        # Build RAG query from condition name
        rag_query = (
            f"Explique a {condition}: fisiopatologia, achados fundoscópicos, "
            f"correlação neurológica e abordagem clínica."
        )

        return ClassificationResult(
            condition=condition,
            condition_en=condition_en,
            confidence=round(confidence, 3),
            severity=severity,
            neurological_flag=neuro_flag,
            neurological_note=neuro_note,
            features_detected=features if features else ["Análise por visão computacional"],
            rag_query=rag_query,
            related_structures=structures if structures else ["retina"],
            classifier_method="claude_vision",
        )

    # ── Tier 2: Feature-based fallback ────────────────────────────────────────

    def _classify_feature_based(self, image_data: bytes) -> ClassificationResult:
        try:
            img = _load_image(image_data)
        except Exception as e:
            raise ValueError(f"Não foi possível processar a imagem: {e}")

        features = _extract_features(img)
        scores   = _score_conditions(features)

        top_condition = max(scores, key=lambda k: scores[k])
        top_score     = scores[top_condition]

        sorted_scores = sorted(scores.values(), reverse=True)
        margin        = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
        confidence    = min(0.95, 0.50 + margin * 1.5 + top_score * 0.2)

        meta     = CONDITION_META[top_condition]
        severity = _get_severity(top_condition, top_score)
        detected = _get_detected_features(features, top_condition)

        logger.info(
            "classifier.feature_result",
            condition=top_condition,
            confidence=round(confidence, 3),
            scores={k: round(v, 3) for k, v in scores.items()},
        )

        return ClassificationResult(
            condition=meta["label"],
            condition_en=meta["label_en"],
            confidence=round(confidence, 3),
            severity=severity,
            neurological_flag=meta["neurological"],
            neurological_note=meta["neuro_note"],
            features_detected=detected,
            rag_query=meta["rag_query"],
            related_structures=meta["structures"],
            classifier_method="feature_based",
        )
