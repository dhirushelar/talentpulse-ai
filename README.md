# TalentPulse AI — Next-Gen Autonomous Resume Parser & Talent Analytics Platform

> **Transform unstructured resumes into structured, searchable talent intelligence using Python (spaCy, PDFPlumber), Flask, and PostgreSQL.**

![TalentPulse AI](https://img.shields.io/badge/TalentPulse-AI%20Resume%20Parser-indigo?style=for-the-badge&logo=python&logoColor=white)
![Build Status](https://img.shields.io/badge/Tests-7%20Passed-emerald?style=for-the-badge&logo=pytest&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue?style=for-the-badge&logo=postgresql&logoColor=white)

---

## 🚀 What is TalentPulse AI?

**TalentPulse AI** is an enterprise-grade AI resume parser and candidate intelligence system. It ingests resumes in **PDF**, **DOCX**, and **TXT** formats, extracts structural candidate details (Name, Contact, Categorized Competencies, Education Timeline, Work History, and Executive Summary), and indexes them into a high-performance relational database.

It features a **modern, animated Glassmorphic Web Dashboard** with Dark/Light mode, an AI-powered Job Description (JD) Fit Matcher (0–100% score), a side-by-side Candidate Comparison Matrix, and full CSV/JSON export tools.

---

## ✨ Advanced Features

### 1. 🧠 Intelligent Multi-Format Extraction Engine
- **PDFPlumber Layout Extraction:** Extracts clean, structured text, tabular data, and two-column layouts from PDF resumes without text scrambling.
- **DOCX Parser:** Extracts content from paragraphs and multi-column tables via `python-docx`.
- **spaCy Named Entity Recognition (NER):** High-accuracy extraction of candidate names (`PERSON`), locations (`GPE`), and organizations (`ORG`).
- **500+ Skill Taxonomy:** Automatically classifies detected skills into distinct domains:
  - *Programming Languages* (Python, Go, Rust, Java, TypeScript, SQL...)
  - *Frameworks & Libraries* (React, Next.js, FastAPI, Flask, Django, Spring Boot...)
  - *Databases & Storage* (PostgreSQL, MongoDB, Redis, Snowflake, Supabase...)
  - *Cloud & DevOps* (AWS, GCP, Docker, Kubernetes, Terraform, CI/CD...)
  - *AI & Data Science* (PyTorch, TensorFlow, spaCy, Scikit-learn, LLMs, NLP, Computer Vision...)
  - *Tools & Soft Skills* (Agile, Scrum, Leadership, System Design...)
- **Academic Credentials Profiler:** Detects degree levels (Ph.D., Master's, Bachelor's, Associate, Diploma), fields of study, universities, graduation years, and GPAs.
- **Experience Duration & Timeline:** Automatically parses roles, companies, and date ranges, calculating total years of professional experience.

### 2. ⚡ AI Job Description (JD) Fit Matcher
- Paste any job posting or requirements text.
- Automatically extracts required skills and computes an algorithmic **Candidate Fit Score (0–100%)**.
- Visually flags **Matched Skills** (green badges) vs **Missing Skills** (red badges).

### 3. ⚖️ Candidate Side-by-Side Comparison Matrix
- Select up to 3 candidates with interactive checkboxes.
- Launches a side-by-side comparison modal highlighting shared competencies, unique skills, years of experience, and degrees.

### 4. 🎨 Modern, Animated Glassmorphism UI
- **Dark / Light Theme Switcher:** Smooth transition with persistent preference storage.
- **Ambient Glowing Mesh:** Subtle keyframe-animated background glow.
- **Animated Multi-Stage Upload:** Real-time feedback for PDF reading, spaCy NER, and database indexing.
- **Celebratory Confetti:** Interactive celebratory particle physics upon batch processing.
- **Interactive Analytics:** Chart.js horizontal bar charts displaying skill distributions.

### 5. 🗄️ Database Architecture (PostgreSQL + Auto-Fallback)
- Full support for **PostgreSQL** with SQLAlchemy ORM.
- Automatic, zero-configuration fallback to local **SQLite** when a local PostgreSQL server is not yet provisioned.
- One-click `docker-compose.yml` to spin up a PostgreSQL instance.

---

## 📁 System Architecture

```
Automatic resume Phraser/
├── app.py                      # Flask REST API endpoints and web routes
├── config.py                   # Environment settings and database configuration
├── database.py                 # SQLAlchemy engine, session management, and fallback
├── models.py                   # Relational models: Candidate, Skill, Education, Experience
├── parser/
│   ├── __init__.py             # Package init
│   ├── extractor.py            # PDFPlumber & python-docx file readers
│   ├── nlp_parser.py           # spaCy NER + regex extraction algorithms
│   ├── skills_db.py            # Categorized skills taxonomy
│   └── degree_patterns.py      # Degree regex, majors, and GPA patterns
├── static/
│   ├── css/style.css           # Glassmorphism design system & keyframe animations
│   └── js/app.js               # Frontend controller (JD match, compare, charts, upload)
├── templates/
│   └── index.html              # Modern web application UI
├── sample_resumes/             # Realistic sample resumes (PDF and DOCX)
├── scripts/
│   ├── generate_sample_resumes.py # Generates test resumes via ReportLab & python-docx
│   └── seed_database.py           # Pre-seeds sample candidate profiles
├── tests/
│   ├── test_extractor.py       # Tests for PDF & DOCX text extraction
│   ├── test_nlp_parser.py      # Tests for NLP entity extraction
│   └── test_api.py             # Tests for REST API endpoints
├── docker-compose.yml          # PostgreSQL container definition
├── requirements.txt            # Python dependencies
└── .env.example                # Sample environment variables
```

---

## 🛠️ Installation & Setup

### 1. Activate Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies & spaCy Model
```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. PostgreSQL Configuration (Optional)
To use Docker PostgreSQL:
```powershell
docker compose up -d
```
*(If Docker/PostgreSQL is not running, the application will automatically connect to SQLite without any errors).*

### 4. Run the Application
```powershell
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser!

---

## 🧪 Automated Testing

Run the full test suite with:
```powershell
.\venv\Scripts\python.exe -m pytest -v
```

All 7 test suites verify:
- ✅ PDF text extraction via PDFPlumber
- ✅ DOCX text extraction via python-docx
- ✅ Exception handling on invalid formats
- ✅ Candidate entity extraction (Name, Contact, Skills, Education)
- ✅ API health check (`/api/status`)
- ✅ Upload, search, JD match, and delete workflows
- ✅ CSV & JSON export generation

---

## 📡 REST API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Upload one or more resumes (`resumes` multipart field) |
| `GET` | `/api/candidates` | Filter candidates (`query`, `skills`, `degree`, `status`, `min_exp`) |
| `GET` | `/api/candidates/<id>` | Full candidate details and raw extracted text |
| `PUT` | `/api/candidates/<id>/status`| Update recruitment pipeline stage (`New`, `Shortlisted`, etc.) |
| `PUT` | `/api/candidates/<id>/notes` | Update recruiter notes with instant auto-save |
| `POST` | `/api/match-jd` | AI Job Description fit scoring (0–100%) |
| `POST` | `/api/compare` | Candidate side-by-side comparison matrix |
| `GET` | `/api/export/csv` | Export candidates database to CSV format |
| `GET` | `/api/export/json` | Export candidates database to JSON format |
| `GET` | `/api/stats` | Analytics data for charts and KPI cards |
| `GET` | `/api/skills` | List all available skill taxonomy keywords |
| `DELETE` | `/api/candidates/<id>` | Delete candidate and remove stored resume |

---

## 📄 License
MIT License. Developed for automated talent acquisition and candidate intelligence.
