# src/mymap/utils/image_helpers.py
from PySide6.QtGui import QImage, QPixmap
from PIL import Image
import io

def qimage_to_pil(qimage: QImage) -> Image.Image:
    """
    Convert QImage to PIL Image (RGB).
    Works for common formats. Returns a PIL.Image.Image.
    """
    qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
    width = qimage.width()
    height = qimage.height()

    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())
    arr = bytes(ptr)

    img = Image.frombuffer("RGBA", (width, height), arr, "raw", "RGBA", 0, 1)
    return img.convert("RGB")

def qpixmap_to_pil(qpixmap: QPixmap) -> Image.Image:
    return qimage_to_pil(qpixmap.toImage())
