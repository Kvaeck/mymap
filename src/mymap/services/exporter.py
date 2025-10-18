# src/mymap/services/exporter.py
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib
import json

from ..services.license_manager import LicenseManager

class ExportError(Exception):
    pass

def document_hash_bytes(doc_bytes: bytes) -> str:
    """Return SHA256 hex digest for document bytes (used to identify document)."""
    h = hashlib.sha256()
    h.update(doc_bytes)
    return h.hexdigest()

class ExportService:
    """
    ExportService that:
    - Enforces student per-document export limit (2)
    - Persists export counts using LicenseManager persistence
    - Applies watermark (text + optional logo image)
    """

    def __init__(self, license_manager: LicenseManager, student_export_limit: int = 2):
        self.license = license_manager
        self.student_export_limit = student_export_limit

    def _ensure_allowed(self, doc_hash: str):
        if self.license.is_full():
            return
        cnt = self.license.get_export_count(doc_hash)
        if cnt >= self.student_export_limit:
            raise ExportError(f"Student edition: export limit reached for this document ({self.student_export_limit}).")

    def _apply_watermark(self, img: Image.Image, watermark_text: str = "Made by PePik", logo_path: Optional[Path] = None) -> Image.Image:
        """
        Applies a semi-translucent watermark text in the bottom-right corner and optional small logo to bottom-left.
        Returns an RGB image.
        """
        # Ensure RGBA for compositing
        base = img.convert("RGBA")
        w, h = base.size
        overlay = Image.new("RGBA", base.size, (255,255,255,0))
        draw = ImageDraw.Draw(overlay)

        # Text size proportional to image width
        font_size = max(12, w // 45)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        text = watermark_text
        text_w, text_h = draw.textsize(text, font=font)
        padding = int(0.02 * w)
        text_pos = (w - text_w - padding, h - text_h - padding)

        # Semi-transparent white text with subtle shadow for readability
        shadow_pos = (text_pos[0]+1, text_pos[1]+1)
        draw.text(shadow_pos, text, font=font, fill=(0,0,0,90))
        draw.text(text_pos, text, font=font, fill=(255,255,255,150))

        # Logo if provided: place bottom-left scaled to ~8% width
        if logo_path and Path(logo_path).exists():
            try:
                logo = Image.open(logo_path).convert("RGBA")
                max_logo_w = int(w * 0.08)
                ratio = max_logo_w / logo.width
                new_size = (max_logo_w, max(1, int(logo.height * ratio)))
                logo = logo.resize(new_size, Image.LANCZOS)
                logo_pos = (padding, h - logo.height - padding)
                overlay.paste(logo, logo_pos, logo)
            except Exception:
                pass

        composed = Image.alpha_composite(base, overlay).convert("RGB")
        return composed

    def export_pil_image(self, pil_image: Image.Image, out_path: Path, doc_bytes: bytes, fmt: Optional[str] = None, watermark_logo: Optional[Path] = None):
        """
        Export PIL image to out_path. doc_bytes is the serialized document bytes (JSON dump)
        used to compute per-document hash.
        """
        out_path = Path(out_path)
        fmt = (fmt or out_path.suffix.lstrip(".")).lower() or "jpg"

        doc_hash = document_hash_bytes(doc_bytes)
        self._ensure_allowed(doc_hash)

        img = pil_image
        if not self.license.is_full():
            img = self._apply_watermark(img, watermark_text="Made by PePik", logo_path=watermark_logo)

        if fmt in ("jpg", "jpeg"):
            img.save(out_path, format="JPEG", quality=95)
        elif fmt == "png":
            img.save(out_path, format="PNG")
        elif fmt == "pdf":
            img.save(out_path, format="PDF")
        elif fmt in ("ppt", "pptx"):
            # leave for full edition; placeholder exception
            raise ExportError("PPTX export not implemented in this client stub. Implement using python-pptx in Full edition.")
        else:
            raise ExportError(f"Unsupported format: {fmt}")

        # increment the persisted export counter for the document
        if not self.license.is_full():
            self.license.increment_export_count(doc_hash)
