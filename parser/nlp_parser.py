"""
Core NLP Resume Parser
Extracts structured candidate details (Name, Contact Info, Skills, Education, Experience, Summary)
using spaCy, custom regex rules, and semantic pattern matching.
"""

import re
import logging
from typing import Dict, List, Any, Optional
import spacy
from spacy.tokens import Doc

from .skills_db import SKILLS_DATABASE, EXACT_CASE_SKILLS
from .degree_patterns import (
    DEGREE_PATTERNS, MAJORS_LIST, INSTITUTION_KEYWORDS,
    GPA_REGEX, YEAR_RANGE_REGEX, SINGLE_YEAR_REGEX
)

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Loads the spaCy language model."""
        try:
            self.nlp = spacy.load(model_name)
        except Exception as e:
            logger.warning(f"Could not load spaCy model '{model_name}': {e}. Attempting blank English pipeline.")
            try:
                self.nlp = spacy.blank("en")
            except Exception:
                self.nlp = None

    def parse(self, text: str) -> Dict[str, Any]:
        """Runs the complete extraction pipeline on raw resume text."""
        if not text or not text.strip():
            return {
                "name": None,
                "email": None,
                "phone": None,
                "location": None,
                "linkedin_url": None,
                "github_url": None,
                "portfolio_url": None,
                "summary": None,
                "total_experience_years": 0.0,
                "skills": [],
                "education": [],
                "experience": []
            }

        # 1. Section Segmentation
        sections = self._extract_sections(text)

        # 2. Extract Contact & Personal Details
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        links = self._extract_urls(text)
        name = self._extract_name(text, email)
        location = self._extract_location(text)

        # 3. Extract Summary
        summary = self._extract_summary(sections, text)

        # 4. Extract Skills
        skills = self._extract_skills(text)

        # 5. Extract Education
        education = self._extract_education(sections, text)

        # 6. Extract Experience
        experience, total_years = self._extract_experience(sections, text)

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "linkedin_url": links.get("linkedin"),
            "github_url": links.get("github"),
            "portfolio_url": links.get("portfolio"),
            "summary": summary,
            "total_experience_years": total_years,
            "skills": skills,
            "education": education,
            "experience": experience
        }

    # -------------------------------------------------------------
    # Section Segmentation
    # -------------------------------------------------------------
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Splits the resume text into logical sections based on common headings."""
        section_headers = {
            "summary": [r"summary", r"professional summary", r"executive summary", r"about me", r"objective", r"profile"],
            "skills": [r"skills", r"technical skills", r"core competencies", r"technologies", r"areas of expertise"],
            "experience": [r"experience", r"work experience", r"employment history", r"professional experience", r"work history"],
            "education": [r"education", r"academic background", r"academic qualifications", r"educational background"],
            "projects": [r"projects", r"personal projects", r"key projects", r"technical projects"],
            "certifications": [r"certifications", r"certificates", r"licenses & certifications", r"awards"]
        }

        # Build regex to find headers
        header_patterns = []
        for sec_name, titles in section_headers.items():
            for title in titles:
                pattern = rf"(?:^|\n)\s*(?:[#*\-_\s]*)(?P<{sec_name}_{len(header_patterns)}>{title})(?:[:\s\-_*]*)(?:\n|$)"
                header_patterns.append(pattern)

        combined_regex = re.compile("|".join(header_patterns), re.IGNORECASE | re.MULTILINE)
        matches = list(combined_regex.finditer(text))

        sections: Dict[str, str] = {}
        if not matches:
            return sections

        for i, match in enumerate(matches):
            group_name = next((k for k, v in match.groupdict().items() if v is not None), None)
            if not group_name:
                continue
            section_key = group_name.split("_")[0]
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sec_content = text[start_pos:end_pos].strip()
            sections[section_key] = sec_content

        return sections

    # -------------------------------------------------------------
    # Name Extraction
    # -------------------------------------------------------------
    def _extract_name(self, text: str, email: Optional[str] = None) -> Optional[str]:
        """Extracts the candidate's name from the header/first lines."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return None

        # Ignore lines that are obvious headers or contact lines
        noise_keywords = [
            "resume", "curriculum", "vitae", "cv", "page", "phone", "email",
            "contact", "github", "linkedin", "address", "portfolio", "http",
            "summary", "experience", "education", "profile"
        ]

        candidate_lines = []
        for line in lines[:8]:
            line_lower = line.lower()
            if any(k in line_lower for k in noise_keywords):
                continue
            if "@" in line or re.search(r"\d{5,}", line):
                continue
            if len(line.split()) > 5:
                continue
            candidate_lines.append(line)

        # Try spaCy NER on candidate lines individually first
        if self.nlp and candidate_lines:
            for line in candidate_lines[:4]:
                doc = self.nlp(line)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        cand = ent.text.strip().splitlines()[0].strip()
                        words = cand.split()
                        if 2 <= len(words) <= 4:
                            return cand.title()

            # Try overall header sample if individual lines didn't yield an entity
            header_sample = ". ".join(candidate_lines)
            doc = self.nlp(header_sample)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    cand = ent.text.strip().splitlines()[0].strip()
                    words = cand.split()
                    if 2 <= len(words) <= 4:
                        return cand.title()

        # Fallback heuristic: First clean title-cased line with 2-3 words
        for line in candidate_lines:
            words = line.split()
            if 2 <= len(words) <= 3:
                if all(w[0].isupper() and w.isalpha() for w in words):
                    return line.strip().title()

        # Fallback from email address if available (e.g. john.doe@email.com -> John Doe)
        if email:
            local_part = email.split("@")[0]
            parts = re.split(r"[._\-]", local_part)
            if len(parts) >= 2 and all(p.isalpha() for p in parts[:2]):
                return " ".join(parts[:2]).title()

        return candidate_lines[0] if candidate_lines else None

    # -------------------------------------------------------------
    # Contact Info Extraction
    # -------------------------------------------------------------
    def _extract_email(self, text: str) -> Optional[str]:
        """Extracts candidate email."""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extracts candidate phone number with support for international formats."""
        phone_patterns = [
            r"(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
            r"\+?\d{1,3}[\s-]?\d{5}[\s-]?\d{5}",
            r"\b\d{10}\b"
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Discard numbers that are years or zip codes
                for m in matches:
                    digits = re.sub(r"\D", "", m)
                    if 10 <= len(digits) <= 14:
                        return m.strip()
        return None

    def _extract_urls(self, text: str) -> Dict[str, Optional[str]]:
        """Extracts LinkedIn, GitHub, and Portfolio URLs."""
        urls = {"linkedin": None, "github": None, "portfolio": None}

        # LinkedIn
        li_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?", text, re.IGNORECASE)
        if li_match:
            url = li_match.group(0)
            urls["linkedin"] = url if url.startswith("http") else f"https://{url}"

        # GitHub
        gh_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+/?", text, re.IGNORECASE)
        if gh_match:
            url = gh_match.group(0)
            urls["github"] = url if url.startswith("http") else f"https://{url}"

        # Portfolio / Personal Website
        all_urls = re.findall(r"https?://(?:www\.)?[a-zA-Z0-9./\-_]+", text)
        for u in all_urls:
            u_lower = u.lower()
            if "linkedin.com" not in u_lower and "github.com" not in u_lower and not u_lower.endswith((".pdf", ".png", ".jpg")):
                urls["portfolio"] = u
                break

        return urls

    def _extract_location(self, text: str) -> Optional[str]:
        """Extracts candidate city/state/country from the header section or spaCy GPE/LOC."""
        top_lines = "\n".join(text.splitlines()[:12])
        if self.nlp:
            doc = self.nlp(top_lines)
            locations = [ent.text.strip() for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
            if locations:
                return ", ".join(dict.fromkeys(locations[:2]))

        # Common city, state regex heuristic (e.g. "Seattle, WA" or "San Francisco, CA")
        loc_match = re.search(r"\b([A-Z][a-zA-Z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)\b", top_lines)
        if loc_match:
            return loc_match.group(1).strip()
        return None

    # -------------------------------------------------------------
    # Summary Extraction
    # -------------------------------------------------------------
    def _extract_summary(self, sections: Dict[str, str], text: str) -> Optional[str]:
        """Extracts the professional summary or objective."""
        if "summary" in sections and sections["summary"]:
            lines = [l.strip() for l in sections["summary"].splitlines() if l.strip()]
            return " ".join(lines[:4])

        # If not explicitly marked by header, check early paragraph
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines[2:8]:
            if len(line) > 60 and not re.search(r"[@\d{5,}]", line) and not line.isupper():
                return line
        return None

    # -------------------------------------------------------------
    # Skills Extraction
    # -------------------------------------------------------------
    def _extract_skills(self, text: str) -> List[Dict[str, str]]:
        """
        Extracts skills using boundary-safe lookup against SKILLS_DATABASE,
        preventing false positives for single letters or short acronyms.
        """
        found_skills = {}

        for skill, category in SKILLS_DATABASE.items():
            if skill in EXACT_CASE_SKILLS:
                # Strict case and word boundary check
                pattern = rf"(?<![A-Za-z0-9_]){re.escape(skill)}(?![A-Za-z0-9_])"
                if re.search(pattern, text):
                    found_skills[skill] = category
            else:
                # Case-insensitive word boundary check
                pattern = rf"(?<![A-Za-z0-9_]){re.escape(skill)}(?![A-Za-z0-9_])"
                if re.search(pattern, text, re.IGNORECASE):
                    found_skills[skill] = category

        # Return as list of dicts: [{"name": "Python", "category": "Programming Languages"}]
        return [
            {"name": skill, "category": category}
            for skill, category in sorted(found_skills.items(), key=lambda x: (x[1], x[0]))
        ]

    # -------------------------------------------------------------
    # Education Extraction
    # -------------------------------------------------------------
    def _extract_education(self, sections: Dict[str, str], text: str) -> List[Dict[str, Any]]:
        """Extracts degrees, majors, universities, graduation years, and grades."""
        edu_text = sections.get("education", text)
        education_records = []
        lines = [line.strip() for line in edu_text.splitlines() if line.strip()]

        current_record = None

        for line in lines:
            # Check for Degree
            detected_degree = None
            for pattern, degree_label in DEGREE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    detected_degree = degree_label
                    break

            # Check for Institution
            detected_inst = None
            for keyword in INSTITUTION_KEYWORDS:
                if keyword.lower() in line.lower():
                    detected_inst = line
                    break

            # Check for Major
            detected_major = None
            for major in MAJORS_LIST:
                if re.search(rf"\b{re.escape(major)}\b", line, re.IGNORECASE):
                    detected_major = major
                    break

            # Check for Year Range or Graduation Year
            year_match = YEAR_RANGE_REGEX.search(line)
            start_year, end_year = None, None
            if year_match:
                start_year = year_match.group(1)
                end_year = year_match.group(2)
            else:
                single_year = SINGLE_YEAR_REGEX.search(line)
                if single_year:
                    end_year = single_year.group(1)

            # Check for Grade / GPA
            gpa_match = GPA_REGEX.search(line)
            grade = gpa_match.group(0) if gpa_match else None

            # If we detected a degree or institution, build/append record
            if detected_degree:
                if current_record and current_record.get("degree"):
                    education_records.append(current_record)
                current_record = {
                    "degree": detected_degree,
                    "field_of_study": detected_major,
                    "institution": detected_inst,
                    "start_year": start_year,
                    "end_year": end_year,
                    "grade": grade
                }
            elif current_record:
                # Supplement the existing record
                if detected_inst and not current_record.get("institution"):
                    current_record["institution"] = detected_inst
                if detected_major and not current_record.get("field_of_study"):
                    current_record["field_of_study"] = detected_major
                if end_year and not current_record.get("end_year"):
                    current_record["end_year"] = end_year
                    current_record["start_year"] = start_year
                if grade and not current_record.get("grade"):
                    current_record["grade"] = grade

        if current_record and current_record.get("degree"):
            education_records.append(current_record)

        # Fallback if no records found via line-by-line: full scan for degrees
        if not education_records:
            for pattern, degree_label in DEGREE_PATTERNS:
                match = re.search(pattern, edu_text, re.IGNORECASE)
                if match:
                    # Find nearby year
                    single_year = SINGLE_YEAR_REGEX.search(edu_text)
                    education_records.append({
                        "degree": degree_label,
                        "field_of_study": "Computer Science" if "computer" in edu_text.lower() else None,
                        "institution": None,
                        "start_year": None,
                        "end_year": single_year.group(1) if single_year else None,
                        "grade": None
                    })
                    break

        return education_records

    # -------------------------------------------------------------
    # Experience Extraction
    # -------------------------------------------------------------
    def _extract_experience(self, sections: Dict[str, str], text: str) -> tuple[List[Dict[str, Any]], float]:
        """Extracts work history, job titles, companies, dates, and calculates total experience."""
        exp_text = sections.get("experience", "")
        if not exp_text:
            exp_text = text

        experience_records = []
        total_years = 0.0

        # Regex for Job Titles
        job_title_pattern = re.compile(
            r"\b(Software Engineer|Frontend Developer|Backend Developer|Full Stack Developer|"
            r"DevOps Engineer|Data Scientist|Data Analyst|Machine Learning Engineer|"
            r"Product Manager|Project Manager|Engineering Manager|System Administrator|"
            r"Cloud Architect|QA Engineer|Security Analyst|Database Administrator|"
            r"Lead Developer|Senior [A-Za-z\s]+|Junior [A-Za-z\s]+|Intern|Technical Lead)\b",
            re.IGNORECASE
        )

        lines = [line.strip() for line in exp_text.splitlines() if line.strip()]
        current_exp = None
        years_found = []

        for line in lines:
            title_match = job_title_pattern.search(line)
            date_match = YEAR_RANGE_REGEX.search(line)

            if date_match:
                start_yr = int(date_match.group(1))
                end_str = date_match.group(2).lower()
                end_yr = 2026 if ("present" in end_str or "current" in end_str) else int(end_str)
                duration = max(0, end_yr - start_yr)
                years_found.append(duration)

            if title_match:
                if current_exp:
                    experience_records.append(current_exp)
                
                job_title = title_match.group(0).title()
                # If the line contains more words (e.g. "Software Engineer at Google"), extract company
                company = None
                if " at " in line:
                    company = line.split(" at ", 1)[1].strip()
                elif " - " in line:
                    parts = line.split(" - ")
                    if len(parts) > 1 and parts[0].strip().lower() != job_title.lower():
                        company = parts[0].strip()

                current_exp = {
                    "job_title": job_title,
                    "company": company,
                    "location": None,
                    "start_date": date_match.group(1) if date_match else None,
                    "end_date": date_match.group(2) if date_match else None,
                    "is_current": True if date_match and ("present" in date_match.group(2).lower() or "current" in date_match.group(2).lower()) else False,
                    "description": ""
                }
            elif current_exp and len(line) > 20:
                if not current_exp["description"]:
                    current_exp["description"] = line
                elif len(current_exp["description"]) < 300:
                    current_exp["description"] += " " + line

        if current_exp:
            experience_records.append(current_exp)

        total_years = float(sum(years_found))
        if total_years > 40:  # Sanity check against overlapping ranges
            total_years = 15.0

        return experience_records, total_years
