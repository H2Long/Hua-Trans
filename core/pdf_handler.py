"""PDF processing with PyMuPDF for text extraction and TOC parsing."""

import fitz  # PyMuPDF


class PDFHandler:
    """Handle PDF file operations: text extraction, TOC, rendering."""

    def __init__(self):
        self.doc: fitz.Document | None = None
        self.file_path: str = ""

    def open(self, file_path: str) -> bool:
        """Open a PDF file, closing any previously opened document."""
        self.close()
        try:
            self.doc = fitz.open(file_path)
            self.file_path = file_path
            return True
        except Exception as e:
            from .logging_setup import get_logger
            get_logger().warning("Failed to open PDF '%s': %s", file_path, e)
            self.doc = None
            return False

    def close(self):
        """Close the current PDF."""
        if self.doc:
            self.doc.close()
            self.doc = None

    @property
    def page_count(self) -> int:
        return len(self.doc) if self.doc else 0

    @property
    def title(self) -> str:
        if self.doc:
            return self.doc.metadata.get("title", "") or ""
        return ""

    def get_toc(self) -> list[dict]:
        """Extract table of contents (bookmarks).

        Returns list of {level, title, page, children}.
        """
        if not self.doc:
            return []
        toc = self.doc.get_toc(simple=False)
        result = []
        stack = [result]
        for level, title, page, *_ in toc:
            entry = {"level": level, "title": title, "page": page, "children": []}
            while len(stack) > level:
                stack.pop()
            stack[-1].append(entry)
            stack.append(entry["children"])
        return result

    def get_page_text(self, page_num: int) -> str:
        """Extract text from a specific page (0-indexed)."""
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return ""
        page = self.doc[page_num]
        return page.get_text("text")

    def get_page_text_blocks(self, page_num: int) -> list[dict]:
        """Extract text blocks with position information.

        Returns list of {text, bbox: (x0, y0, x1, y1), block_no}.
        """
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return []
        page = self.doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        result = []
        for block in blocks:
            if block["type"] == 0:  # Text block
                text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        text += span["text"]
                    text += "\n"
                # Use font size of the longest text span (more representative than max)
                best_size = 10
                best_len = 0
                for line in block["lines"]:
                    for span in line["spans"]:
                        if len(span["text"]) > best_len:
                            best_len = len(span["text"])
                            best_size = span["size"]
                orig_font_size = best_size

                result.append({
                    "text": text.strip(),
                    "bbox": block["bbox"],
                    "block_no": block["number"],
                    "font_size": orig_font_size,
                })
        return result

    def get_page_spans(self, page_num: int) -> list[dict]:
        """Extract individual text spans with position and style info.

        Returns list of {text, bbox: (x0,y0,x1,y1), font_size, font_name, block_no}.
        Useful for precise text replacement in overlay translation.
        """
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return []
        page = self.doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        spans = []
        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    if not text.strip():
                        continue
                    spans.append({
                        "text": text,
                        "bbox": span["bbox"],
                        "font_size": span["size"],
                        "font_name": span["font"],
                        "block_no": block["number"],
                    })
        return spans

    def get_page_image(self, page_num: int, dpi: int = 150) -> bytes | None:
        """Render a page as PNG image bytes."""
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return None
        page = self.doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")

    def get_full_text(self) -> str:
        """Extract text from all pages."""
        if not self.doc:
            return ""
        texts = []
        for i in range(len(self.doc)):
            text = self.get_page_text(i)
            if text.strip():
                texts.append(f"--- Page {i + 1} ---\n{text}")
        return "\n\n".join(texts)
