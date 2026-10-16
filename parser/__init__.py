"""
Resume Parser Package
Extracts text from PDFs and DOCX files and extracts structured candidate details using spaCy and rule-based NLP.
"""

from .extractor import extract_text_from_file
from .nlp_parser import ResumeParser

__all__ = ["extract_text_from_file", "ResumeParser"]
