from __future__ import annotations

import pytest

from app.services.pdf_extraction_service import PdfExtractionService


class TestPdfExtractionService:
    def test_extract_raises_on_missing_file(self):
        service = PdfExtractionService()
        with pytest.raises(FileNotFoundError):
            service.extract("does_not_exist.pdf")

    def test_render_table_formats_rows_as_pipe_delimited(self):
        table = [["SKU", "Price"], ["APP-001", "19.99"], [None, "20"]]
        rendered = PdfExtractionService._render_table(table)
        assert "SKU | Price" in rendered
        assert "APP-001 | 19.99" in rendered
        assert " | 20" in rendered

    def test_degrades_gracefully_without_optional_dependencies(self, monkeypatch):
        service = PdfExtractionService()
        monkeypatch.setattr(service, "_pdfplumber", None)
        monkeypatch.setattr(service, "_fitz", None)
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            fake_pdf = Path(tmp) / "empty.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 fake")
            chunks = service.extract(str(fake_pdf))
            assert chunks == []
