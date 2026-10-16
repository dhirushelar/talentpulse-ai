"""
File text extractor supporting PDF (via pdfplumber) and DOCX (via python-docx).
"""

import os
import re
import logging
from pathlib import Path
import pdfplumber
import docx

import pypdf

logger = logging.getLogger(__name__)

def clean_extracted_text(text: str) -> str:
    """Cleans up formatting quirks, odd unicode characters, and excess whitespace."""
    if not text:
        return ""
    # Remove null bytes to prevent database driver errors
    text = text.replace("\x00", "")
    # Normalize unicode spaces & dashes
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = text.replace("–", "-").replace("—", "-")
    # Replace multiple spaces with a single space, but preserve newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    # Remove excessive blank lines
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def extract_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using pdfplumber with automatic pypdf fallback."""
    extracted_pages = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text(layout=False) or ""
                if not page_text.strip():
                    page_text = page.extract_text(layout=True) or ""
                if page_text.strip():
                    extracted_pages.append(page_text)
        
        full_text = "\n\n".join(extracted_pages).strip()
        if full_text:
            return clean_extracted_text(full_text)
    except Exception as e:
        logger.warning(f"pdfplumber encountered issue on {file_path}: {e}. Trying pypdf fallback.")

    # Fallback to pypdf
    try:
        reader = pypdf.PdfReader(file_path)
        pypdf_pages = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                pypdf_pages.append(t)
        return clean_extracted_text("\n\n".join(pypdf_pages))
    except Exception as e:
        logger.error(f"Both pdfplumber and pypdf failed on {file_path}: {e}")
        raise ValueError(f"Unable to parse PDF: {str(e)}")


def extract_from_docx(file_path: str) -> str:
    """Extracts text from a DOCX file, including tables and headers."""
    try:
        doc = docx.Document(file_path)
        full_text = []

        # Extract paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())

        # Extract text from tables (often used in resumes for 2-column layouts)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    full_text.append(" | ".join(row_cells))

        return clean_extracted_text("\n".join(full_text))
    except Exception as e:
        logger.error(f"Error reading DOCX {file_path}: {e}")
        raise ValueError(f"Unable to parse DOCX: {str(e)}")


def extract_from_txt(file_path: str) -> str:
    """Extracts text from a plain text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return clean_extracted_text(f.read())
    except Exception as e:
        logger.error(f"Error reading TXT {file_path}: {e}")
        raise ValueError(f"Unable to parse text file: {str(e)}")


def extract_text_from_file(file_path: str) -> str:
    """
    Main extraction interface. Routes to the appropriate parser based on file extension.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_from_docx(file_path)
    elif ext in [".txt", ".text"]:
        return extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported formats are PDF, DOCX, TXT.")
