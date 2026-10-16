"""
Pattern matching definitions and regex for extracting education records, degrees, and institutions.
"""

import re

# Standard degree titles and abbreviations
DEGREE_PATTERNS = [
    # Doctorate
    (r"\b(Ph\.?D\.?|Doctor of Philosophy|Doctorate)\b", "Doctor of Philosophy (Ph.D.)"),
    
    # Master's
    (r"\b(Master of Science|M\.?S\.?|MS in|Master of Technology|M\.?Tech\.?)\b", "Master of Science"),
    (r"\b(Master of Business Administration|M\.?B\.?A\.?)\b", "Master of Business Administration (MBA)"),
    (r"\b(Master of Computer Applications|M\.?C\.?A\.?)\b", "Master of Computer Applications (MCA)"),
    (r"\b(Master of Arts|M\.?A\.?)\b", "Master of Arts"),
    (r"\b(Master of Engineering|M\.?Eng\.?)\b", "Master of Engineering"),
    (r"\b(Master(?:'s)? Degree|Masters)\b", "Master's Degree"),

    # Bachelor's
    (r"\b(Bachelor of Technology|B\.?Tech\.?)\b", "Bachelor of Technology (B.Tech)"),
    (r"\b(Bachelor of Engineering|B\.?E\.?)\b", "Bachelor of Engineering (B.E.)"),
    (r"\b(Bachelor of Science|B\.?S\.?|B\.?Sc\.?)\b", "Bachelor of Science (B.S.)"),
    (r"\b(Bachelor of Arts|B\.?A\.?)\b", "Bachelor of Arts (B.A.)"),
    (r"\b(Bachelor of Computer Applications|B\.?C\.?A\.?)\b", "Bachelor of Computer Applications (BCA)"),
    (r"\b(Bachelor of Business Administration|B\.?B\.?A\.?)\b", "Bachelor of Business Administration (BBA)"),
    (r"\b(Bachelor of Commerce|B\.?Com\.?)\b", "Bachelor of Commerce (B.Com)"),
    (r"\b(Bachelor(?:'s)? Degree|Bachelors)\b", "Bachelor's Degree"),

    # Associate & Diploma
    (r"\b(Associate(?:'s)? Degree|A\.?A\.?|A\.?S\.?)\b", "Associate Degree"),
    (r"\b(Diploma in [A-Za-z\s]+|Post Graduate Diploma|PG Diploma)\b", "Diploma"),
]

# Common Fields of Study
MAJORS_LIST = [
    "Computer Science",
    "Computer Engineering",
    "Information Technology",
    "Software Engineering",
    "Data Science",
    "Artificial Intelligence",
    "Machine Learning",
    "Cyber Security",
    "Electrical Engineering",
    "Electronics and Communication",
    "Mechanical Engineering",
    "Civil Engineering",
    "Chemical Engineering",
    "Biotechnology",
    "Information Systems",
    "Business Administration",
    "Finance",
    "Marketing",
    "Economics",
    "Mathematics",
    "Statistics",
    "Physics",
]

# Patterns to match institutions
INSTITUTION_KEYWORDS = [
    "University", "Institute", "College", "School of", "Academy", "Polytechnic", "IIT", "NIT", "BITS"
]

# Regex for GPA / Grade (e.g. "GPA: 3.8/4.0", "CGPA 8.9", "3.9 GPA", "88%")
GPA_REGEX = re.compile(
    r"\b(?:(?:GPA|CGPA|Grade)[\s:]*([0-9]\.[0-9]{1,2}(?:\s*/\s*[0-9](?:\.0)?)?)|([0-9]\.[0-9]{1,2})\s*(?:GPA|CGPA)|([1-9][0-9](?:\.[0-9]+)?%))\b",
    re.IGNORECASE
)

# Regex for Years (e.g. 2018 - 2022, 2020 - Present, 2019)
YEAR_RANGE_REGEX = re.compile(
    r"\b(19\d{2}|20\d{2})\s*(?:[-–—to\s]+)\s*(19\d{2}|20\d{2}|Present|Current)\b",
    re.IGNORECASE
)
SINGLE_YEAR_REGEX = re.compile(r"\b(19\d{2}|20\d{2})\b")
