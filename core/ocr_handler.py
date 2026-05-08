"""OCR processing for scanned PDF pages using Tesseract."""

import io

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class OCRHandler:
    """Handle OCR for scanned PDF pages."""

    def __init__(self, language: str = "eng"):
        self.language = language
        self.available = HAS_OCR

    def is_available(self) -> bool:
        """Check if OCR dependencies are installed."""
        if not self.available:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            from .logging_setup import get_logger
            get_logger().debug("Tesseract not available: %s", e)
            return False

    def ocr_image_bytes(self, image_bytes: bytes) -> str:
        """Perform OCR on image bytes."""
        if not self.is_available():
            return "[OCR not available - install tesseract-ocr]"
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang=self.language)
        return text.strip()

    def ocr_image_file(self, file_path: str) -> str:
        """Perform OCR on an image file."""
        if not self.is_available():
            return "[OCR not available - install tesseract-ocr]"
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang=self.language)
        return text.strip()

    def ocr_pdf_page(self, pdf_handler, page_num: int, dpi: int = 200) -> str:
        """OCR a specific PDF page by rendering it first.

        Args:
            pdf_handler: PDFHandler instance
            page_num: 0-indexed page number
            dpi: rendering resolution (higher = better OCR quality)
        """
        image_bytes = pdf_handler.get_page_image(page_num, dpi=dpi)
        if not image_bytes:
            return ""
        return self.ocr_image_bytes(image_bytes)

    def get_page_text_with_ocr(self, pdf_handler, page_num: int) -> str:
        """Get text from page, falling back to OCR if text extraction is empty.

        Tries native text extraction first (faster, more accurate for digital PDFs).
        Falls back to OCR if the page appears to be a scanned image.
        """
        text = pdf_handler.get_page_text(page_num)
        if text.strip() and len(text.strip()) > 20:
            return text
        # Likely a scanned page, use OCR
        return self.ocr_pdf_page(pdf_handler, page_num)
