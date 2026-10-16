import pytest
from pathlib import Path
from parser.extractor import extract_text_from_file
from parser.nlp_parser import ResumeParser

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "sample_resumes"

@pytest.fixture(scope="module")
def parser():
    return ResumeParser()

def test_parse_backend_resume(parser):
    pdf_file = SAMPLES_DIR / "sample_john_doe_backend.pdf"
    text = extract_text_from_file(str(pdf_file))
    result = parser.parse(text)

    # Name
    assert result["name"] is not None
    assert "John Doe" in result["name"]

    # Contact Info
    assert result["email"] == "john.doe@email.com"
    assert "555" in result["phone"]

    # Skills
    skill_names = [s["name"] for s in result["skills"]]
    assert "Python" in skill_names
    assert "Flask" in skill_names
    assert "PostgreSQL" in skill_names
    assert "Docker" in skill_names
    assert "AWS" in skill_names

    # Education
    assert len(result["education"]) > 0
    edu = result["education"][0]
    assert "Bachelor" in edu["degree"]

    # Experience
    assert result["total_experience_years"] >= 3.0

def test_parse_ai_resume(parser):
    docx_file = SAMPLES_DIR / "sample_sarah_connor_ai.docx"
    text = extract_text_from_file(str(docx_file))
    result = parser.parse(text)

    # Name
    assert result["name"] is not None
    assert "Sarah" in result["name"]

    # Contact Info
    assert result["email"] == "sarah.connor@ai-labs.org"

    # Skills
    skill_names = [s["name"] for s in result["skills"]]
    assert "PyTorch" in skill_names
    assert "spaCy" in skill_names
    assert "NLP" in skill_names
    assert "Machine Learning" in skill_names

    # Education
    assert len(result["education"]) > 0
    edu = result["education"][0]
    assert "Master" in edu["degree"]
