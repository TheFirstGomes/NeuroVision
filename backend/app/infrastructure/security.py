"""
Upload security utilities for NeuroVision.
Magic byte validation and filename sanitization — no external deps required.
"""
import os
import re

from fastapi import HTTPException, status

import structlog

logger = structlog.get_logger(__name__)

# ── Magic byte signatures ─────────────────────────────────────────────────────

_IMAGE_SIGNATURES: list[bytes] = [
    b"\xff\xd8\xff",   # JPEG
    b"\x89PNG",        # PNG
]

_PDF_SIGNATURE = b"%PDF-"

# ── Validators ────────────────────────────────────────────────────────────────


def validate_image(data: bytes, filename: str = "") -> None:
    """
    Verify that `data` is a real image by checking magic bytes.
    Raises HTTP 422 if the bytes don't match JPEG or PNG.
    """
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo de imagem vazio.",
        )

    for sig in _IMAGE_SIGNATURES:
        if data[: len(sig)] == sig:
            return

    logger.warning("security.invalid_image_magic", filename=filename, first_bytes=data[:8].hex())
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Formato de imagem inválido. Envie um arquivo JPEG ou PNG real.",
    )


def validate_pdf(data: bytes, filename: str = "") -> None:
    """
    Verify that `data` is a real PDF by checking the %PDF- header.
    Raises HTTP 422 on mismatch.
    """
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo PDF vazio.",
        )

    if data[:5] != _PDF_SIGNATURE:
        logger.warning("security.invalid_pdf_magic", filename=filename, first_bytes=data[:8].hex())
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo não é um PDF válido (assinatura incorreta).",
        )


def sanitize_filename(filename: str) -> str:
    """
    Strip path traversal components and replace non-safe characters.
    Returns a safe filename truncated to 200 characters.
    """
    name = os.path.basename(filename)
    # Keep only word chars, dashes, underscores, dots and spaces
    name = re.sub(r"[^\w\-_\. ]", "_", name)
    name = name.strip()
    return name[:200] or "upload"
