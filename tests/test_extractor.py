import pytest
from pathlib import Path
from parser.extractor import extract_text_from_file

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "sample_resumes"

def test_extract_pdf():
    pdf_file = SAMPLES_DIR / "sample_john_doe_backend.pdf"
    assert pdf_file.exists(), "Sample PDF must exist"
    text = extract_text_from_file(str(pdf_file))
    assert len(text) > 100
    assert "John Doe" in text
    assert "john.doe@email.com" in text
    assert "Python" in text
    assert "PostgreSQL" in text

def test_extract_docx():
    docx_file = SAMPLES_DIR / "sample_sarah_connor_ai.docx"
    assert docx_file.exists(), "Sample DOCX must exist"
    text = extract_text_from_file(str(docx_file))
    assert len(text) > 100
    assert "Sarah Connor" in text
    assert "sarah.connor@ai-labs.org" in text
    assert "PyTorch" in text
    assert "Machine Learning" in text

def test_extract_invalid_format():
    with pytest.raises(ValueError) as exc:
        extract_text_from_file("invalid_file.xyz")
    assert "Unsupported file format" in str(exc.value)
