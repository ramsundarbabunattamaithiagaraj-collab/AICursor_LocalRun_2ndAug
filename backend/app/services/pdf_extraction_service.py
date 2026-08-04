"""Layout-aware PDF extraction for the RAG ingestion pipeline (Section 6).

Extracts and tags three content types from retail PDFs (catalogs, price
lists, planograms, invoices, flyers):
  - text   : product descriptions, policies, SKUs, brand/category copy
  - table  : price lists, size/variant matrices, promo grids (kept as
             structured rows/columns, not flattened)
  - image  : product photos, packaging shots, planogram diagrams, logos

OCR (pytesseract) is used as a fallback for scanned/image-only pages. All
optional/heavy dependencies degrade gracefully: if a package or external
binary (e.g. the Tesseract executable) is not installed, that capability is
skipped with a warning instead of crashing ingestion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedChunk:
    content: str
    content_type: str  # "text" | "table" | "image"
    page_number: int
    source_file: str
    metadata: dict = field(default_factory=dict)


class PdfExtractionService:
    """Extracts text, tables, and images from a PDF using PyMuPDF/pdfplumber,
    with an OCR fallback and graceful degradation when optional deps are missing.
    """

    def __init__(self) -> None:
        self._fitz = self._try_import_fitz()
        self._pdfplumber = self._try_import_pdfplumber()
        self._pytesseract, self._pil = self._try_import_ocr()

    @staticmethod
    def _try_import_fitz():
        try:
            import fitz  # PyMuPDF

            return fitz
        except ImportError:
            logger.warning("PyMuPDF (fitz) not installed - image extraction will be skipped.")
            return None

    @staticmethod
    def _try_import_pdfplumber():
        try:
            import pdfplumber

            return pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed - text/table extraction will be limited.")
            return None

    @staticmethod
    def _try_import_ocr():
        try:
            import pytesseract
            from PIL import Image

            return pytesseract, Image
        except ImportError:
            logger.warning("pytesseract/Pillow not installed - OCR fallback disabled.")
            return None, None

    def extract(self, file_path: str, image_output_dir: str | None = None) -> list[ExtractedChunk]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        chunks: list[ExtractedChunk] = []
        chunks.extend(self._extract_text_and_tables(path))
        chunks.extend(self._extract_images(path, image_output_dir))

        if not any(c.content_type == "text" for c in chunks):
            logger.info("No embedded text found in %s - attempting OCR fallback.", path.name)
            chunks.extend(self._ocr_fallback(path))

        logger.info(
            "Extracted %s chunks from %s (text=%s, table=%s, image=%s)",
            len(chunks),
            path.name,
            sum(1 for c in chunks if c.content_type == "text"),
            sum(1 for c in chunks if c.content_type == "table"),
            sum(1 for c in chunks if c.content_type == "image"),
        )
        return chunks

    def _extract_text_and_tables(self, path: Path) -> list[ExtractedChunk]:
        chunks: list[ExtractedChunk] = []
        if not self._pdfplumber:
            return chunks

        with self._pdfplumber.open(str(path)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    chunks.append(
                        ExtractedChunk(
                            content=text.strip(),
                            content_type="text",
                            page_number=page_number,
                            source_file=path.name,
                        )
                    )

                for table_index, table in enumerate(page.extract_tables() or []):
                    if not table:
                        continue
                    rendered = self._render_table(table)
                    chunks.append(
                        ExtractedChunk(
                            content=rendered,
                            content_type="table",
                            page_number=page_number,
                            source_file=path.name,
                            metadata={"table_index": table_index, "rows": table},
                        )
                    )
        return chunks

    @staticmethod
    def _render_table(table: list[list[str | None]]) -> str:
        """Renders a table as pipe-delimited rows so numeric fields stay
        queryable/structured rather than being flattened into prose."""
        lines = []
        for row in table:
            cells = [str(cell).strip() if cell is not None else "" for cell in row]
            lines.append(" | ".join(cells))
        return "\n".join(lines)

    def _extract_images(self, path: Path, output_dir: str | None) -> list[ExtractedChunk]:
        chunks: list[ExtractedChunk] = []
        if not self._fitz:
            return chunks

        out_dir = Path(output_dir) if output_dir else path.parent / "extracted_images"
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            doc = self._fitz.open(str(path))
        except Exception as exc:  # noqa: BLE001 - degrade gracefully on corrupt PDFs
            logger.error("Failed to open %s for image extraction: %s", path.name, exc)
            return chunks

        for page_index in range(len(doc)):
            page = doc[page_index]
            for image_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Skipping unreadable image on page %s: %s", page_index + 1, exc)
                    continue
                ext = base_image.get("ext", "png")
                image_path = out_dir / f"{path.stem}_p{page_index + 1}_{image_index}.{ext}"
                image_path.write_bytes(base_image["image"])

                caption = f"Image extracted from '{path.name}' page {page_index + 1} (product/planogram/logo asset)."
                chunks.append(
                    ExtractedChunk(
                        content=caption,
                        content_type="image",
                        page_number=page_index + 1,
                        source_file=path.name,
                        metadata={"image_path": str(image_path)},
                    )
                )
        doc.close()
        return chunks

    def _ocr_fallback(self, path: Path) -> list[ExtractedChunk]:
        chunks: list[ExtractedChunk] = []
        if not (self._fitz and self._pytesseract and self._pil):
            logger.warning("OCR fallback unavailable (missing fitz/pytesseract/Pillow); skipping.")
            return chunks

        try:
            doc = self._fitz.open(str(path))
            for page_index in range(len(doc)):
                page = doc[page_index]
                pix = page.get_pixmap(dpi=200)
                import io

                image = self._pil.open(io.BytesIO(pix.tobytes("png")))
                text = self._pytesseract.image_to_string(image)
                if text.strip():
                    chunks.append(
                        ExtractedChunk(
                            content=text.strip(),
                            content_type="text",
                            page_number=page_index + 1,
                            source_file=path.name,
                            metadata={"extraction_method": "ocr"},
                        )
                    )
            doc.close()
        except Exception as exc:  # noqa: BLE001 - OCR is best-effort
            logger.error("OCR fallback failed for %s: %s", path.name, exc)
        return chunks
