from __future__ import annotations

import hashlib
import io
from typing import Any

import pdfplumber


class PDFService:
    def extract(self, file_bytes: bytes, filename: str = "upload.pdf") -> dict[str, Any]:
        text_pages: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_pages.append(text)

        full_text = "\n\n".join(text_pages)
        # Derive a rough title from first non-empty line
        first_line = next((l.strip() for l in full_text.splitlines() if l.strip()), filename)
        doc_id = f"pdf:{hashlib.sha256(file_bytes).hexdigest()[:16]}"

        return {
            "id": doc_id,
            "title": first_line[:200],
            "abstract": full_text[:1000],
            "full_text": full_text,
            "published_date": None,
            "url": None,
            "doi": None,
            "source": "pdf",
            "authors": [],
            "categories": [],
            "embedding": None,
        }
