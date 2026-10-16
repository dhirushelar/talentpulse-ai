import os
import csv
import io
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_, desc, asc, func

from config import Config, BASE_DIR
from database import engine, SessionLocal, init_db, DB_DIALECT
from models import Candidate, CandidateSkill, CandidateEducation, CandidateExperience
from parser.extractor import extract_text_from_file
from parser.nlp_parser import ResumeParser
from parser.skills_db import SKILLS_DATABASE

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ResumeParserApp")

# Initialize Flask
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        res.headers["Access-Control-Allow-Private-Network"] = "true"
        return res

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# Initialize Database
init_db()

# Initialize Resume NLP Parser
resume_parser = ResumeParser(model_name=Config.SPACY_MODEL)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def calculate_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

# -------------------------------------------------------------
# Web Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    """Serves the main application dashboard."""
    return render_template("index.html", db_dialect=DB_DIALECT)

# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------
@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns application and database status."""
    return jsonify({
        "status": "online",
        "database_dialect": DB_DIALECT,
        "database_url": Config.SQLALCHEMY_DATABASE_URI.split("@")[-1] if "@" in Config.SQLALCHEMY_DATABASE_URI else Config.SQLALCHEMY_DATABASE_URI,
        "spacy_model": Config.SPACY_MODEL,
        "supported_formats": list(Config.ALLOWED_EXTENSIONS)
    })

@app.route("/api/upload", methods=["POST"])
def upload_resumes():
    """
    Handles single or batch resume uploads.
    Extracts text using PDFPlumber/Docx and extracts candidate details with spaCy/NLP.
    """
    if "resumes" not in request.files and "file" not in request.files:
        return jsonify({"error": "No file uploaded. Use field 'resumes' or 'file'."}), 400

    files = request.files.getlist("resumes") or request.files.getlist("file")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No selected files."}), 400

    results = []
    errors = []
    session = SessionLocal()

    try:
        for file in files:
            if not file or file.filename == "":
                continue

            if not allowed_file(file.filename):
                errors.append({"file": file.filename, "error": "File type not supported."})
                continue

            orig_filename = secure_filename(file.filename)
            file_bytes = file.read()
            file_hash = calculate_file_hash(file_bytes)
            file_ext = orig_filename.rsplit(".", 1)[1].lower()

            # Save file to disk with unique timestamp prefix
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp}_{orig_filename}"
            save_path = Config.UPLOAD_FOLDER / saved_filename
            with open(save_path, "wb") as f:
                f.write(file_bytes)

            try:
                # 1. Extract raw text from PDF/Docx
                raw_text = extract_text_from_file(str(save_path))
                if not raw_text.strip():
                    errors.append({"file": orig_filename, "error": "Extracted text was empty or unreadable."})
                    continue

                # 2. Extract structured candidate details with NLP
                parsed_data = resume_parser.parse(raw_text)

                # 3. Store in Database
                candidate = Candidate(
                    name=parsed_data.get("name"),
                    email=parsed_data.get("email"),
                    phone=parsed_data.get("phone"),
                    location=parsed_data.get("location"),
                    linkedin_url=parsed_data.get("linkedin_url"),
                    github_url=parsed_data.get("github_url"),
                    portfolio_url=parsed_data.get("portfolio_url"),
                    summary=parsed_data.get("summary"),
                    total_experience_years=parsed_data.get("total_experience_years", 0.0),
                    raw_text=raw_text,
                    file_name=orig_filename,
                    file_path=str(saved_filename),
                    file_hash=file_hash,
                    file_type=file_ext,
                    parsed_at=datetime.utcnow()
                )
                session.add(candidate)
                session.flush()  # Generate candidate ID

                # Add Skills
                for skill_info in parsed_data.get("skills", []):
                    skill_obj = CandidateSkill(
                        candidate_id=candidate.id,
                        skill_name=skill_info["name"],
                        category=skill_info.get("category", "General")
                    )
                    session.add(skill_obj)

                # Add Education
                for edu_info in parsed_data.get("education", []):
                    edu_obj = CandidateEducation(
                        candidate_id=candidate.id,
                        degree=edu_info.get("degree"),
                        field_of_study=edu_info.get("field_of_study"),
                        institution=edu_info.get("institution"),
                        start_year=edu_info.get("start_year"),
                        end_year=edu_info.get("end_year"),
                        grade=edu_info.get("grade")
                    )
                    session.add(edu_obj)

                # Add Experience
                for exp_info in parsed_data.get("experience", []):
                    exp_obj = CandidateExperience(
                        candidate_id=candidate.id,
                        job_title=exp_info.get("job_title"),
                        company=exp_info.get("company"),
                        location=exp_info.get("location"),
                        start_date=exp_info.get("start_date"),
                        end_date=exp_info.get("end_date"),
                        is_current=exp_info.get("is_current", False),
                        description=exp_info.get("description")
                    )
                    session.add(exp_obj)

                session.commit()
                results.append(candidate.to_dict())

            except Exception as e:
                session.rollback()
                logger.error(f"Error parsing file {orig_filename}: {e}", exc_info=True)
                errors.append({"file": orig_filename, "error": str(e)})

    finally:
        session.close()

    return jsonify({
        "success": len(results) > 0,
        "parsed_count": len(results),
        "error_count": len(errors),
        "candidates": results,
        "errors": errors
    }), (200 if results or not errors else 400)


@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    """
    Search and filter candidates in the database.
    Query parameters:
    - query: Full text / keyword search
    - skills: Comma-separated list of skills
    - degree: Filter by degree or education keyword
    - min_exp: Minimum years of experience (float)
    - sort_by: parsed_at, name, total_experience_years
    - order: asc, desc
    """
    session = SessionLocal()
    try:
        search_query = request.args.get("query", "").strip()
        skills_filter = request.args.get("skills", "").strip()
        degree_filter = request.args.get("degree", "").strip()
        status_filter = request.args.get("status", "").strip()
        min_exp = request.args.get("min_exp", type=float)
        sort_by = request.args.get("sort_by", "parsed_at")
        order = request.args.get("order", "desc")
        page = max(1, request.args.get("page", 1, type=int))
        per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))

        stmt = session.query(Candidate)

        # 1. Text Search Filter
        if search_query:
            wildcard = f"%{search_query}%"
            stmt = stmt.filter(
                or_(
                    Candidate.name.ilike(wildcard),
                    Candidate.email.ilike(wildcard),
                    Candidate.summary.ilike(wildcard),
                    Candidate.raw_text.ilike(wildcard),
                    Candidate.location.ilike(wildcard)
                )
            )

        # 2. Minimum Experience Filter
        if min_exp is not None:
            stmt = stmt.filter(Candidate.total_experience_years >= min_exp)

        # 3. Status Filter
        if status_filter:
            stmt = stmt.filter(Candidate.status.ilike(status_filter))

        # 4. Skills Filter (candidates matching all selected skills)
        if skills_filter:
            skills_list = [s.strip() for s in skills_filter.split(",") if s.strip()]
            for skill in skills_list:
                stmt = stmt.filter(
                    Candidate.skills.any(CandidateSkill.skill_name.ilike(f"%{skill}%"))
                )

        # 5. Degree Filter
        if degree_filter:
            stmt = stmt.filter(
                Candidate.education.any(
                    or_(
                        CandidateEducation.degree.ilike(f"%{degree_filter}%"),
                        CandidateEducation.field_of_study.ilike(f"%{degree_filter}%")
                    )
                )
            )

        # Sorting
        sort_column = getattr(Candidate, sort_by, Candidate.parsed_at)
        if order.lower() == "asc":
            stmt = stmt.order_by(asc(sort_column))
        else:
            stmt = stmt.order_by(desc(sort_column))

        total_count = stmt.count()
        candidates = stmt.offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "candidates": [c.to_dict() for c in candidates]
        })

    finally:
        session.close()


@app.route("/api/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id: int):
    """Fetches candidate profile details including raw text."""
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return jsonify({"error": "Candidate not found."}), 404
        return jsonify(candidate.to_dict(include_raw=True))
    finally:
        session.close()


@app.route("/api/candidates/<int:candidate_id>", methods=["PUT"])
def update_candidate(candidate_id: int):
    """Updates candidate profile information."""
    data = request.json or {}
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return jsonify({"error": "Candidate not found."}), 404

        if "name" in data:
            candidate.name = data["name"]
        if "email" in data:
            candidate.email = data["email"]
        if "phone" in data:
            candidate.phone = data["phone"]
        if "location" in data:
            candidate.location = data["location"]
        if "summary" in data:
            candidate.summary = data["summary"]
        if "total_experience_years" in data:
            candidate.total_experience_years = float(data["total_experience_years"])

        candidate.updated_at = datetime.utcnow()
        session.commit()
        return jsonify({"success": True, "candidate": candidate.to_dict()})
    finally:
        session.close()


@app.route("/api/candidates/<int:candidate_id>", methods=["DELETE"])
def delete_candidate(candidate_id: int):
    """Deletes candidate and their stored resume file."""
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return jsonify({"error": "Candidate not found."}), 404

        # Remove file from disk
        if candidate.file_path:
            full_file_path = Config.UPLOAD_FOLDER / candidate.file_path
            if full_file_path.exists():
                try:
                    os.remove(full_file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove file {full_file_path}: {e}")

        session.delete(candidate)
        session.commit()
        return jsonify({"success": True, "message": "Candidate deleted successfully."})
    finally:
        session.close()


@app.route("/api/candidates/<int:candidate_id>/download", methods=["GET"])
def download_resume(candidate_id: int):
    """Downloads or streams the original uploaded resume file."""
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate or not candidate.file_path:
            return jsonify({"error": "Resume file not found."}), 404

        return send_from_directory(
            Config.UPLOAD_FOLDER,
            candidate.file_path,
            as_attachment=True,
            download_name=candidate.file_name
        )
    finally:
        session.close()


@app.route("/api/stats", methods=["GET"])
def get_statistics():
    """Returns analytics data for dashboard charts and metrics."""
    session = SessionLocal()
    try:
        total_candidates = session.query(func.count(Candidate.id)).scalar() or 0

        # Top 10 most common skills
        top_skills = (
            session.query(CandidateSkill.skill_name, func.count(CandidateSkill.id).label("count"))
            .group_by(CandidateSkill.skill_name)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        # Education level breakdown
        edu_breakdown = (
            session.query(CandidateEducation.degree, func.count(CandidateEducation.id).label("count"))
            .filter(CandidateEducation.degree.isnot(None))
            .group_by(CandidateEducation.degree)
            .order_by(desc("count"))
            .limit(6)
            .all()
        )

        # Average experience
        avg_exp = session.query(func.avg(Candidate.total_experience_years)).scalar() or 0.0

        return jsonify({
            "total_candidates": total_candidates,
            "average_experience": round(float(avg_exp), 1),
            "top_skills": [{"name": s[0], "count": s[1]} for s in top_skills],
            "education_breakdown": [{"degree": e[0], "count": e[1]} for e in edu_breakdown]
        })
    finally:
        session.close()


@app.route("/api/skills", methods=["GET"])
def get_all_skills():
    """Returns list of all available taxonomy skills for search autocomplete."""
    return jsonify({
        "skills": sorted(list(SKILLS_DATABASE.keys()))
    })


@app.route("/api/candidates/<int:candidate_id>/status", methods=["PUT"])
def update_candidate_status(candidate_id: int):
    """Updates candidate recruitment status (New, Shortlisted, Interviewing, Rejected, Hired)."""
    data = request.json or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Status is required."}), 400

    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return jsonify({"error": "Candidate not found."}), 404

        candidate.status = new_status
        candidate.updated_at = datetime.utcnow()
        session.commit()
        return jsonify({"success": True, "status": candidate.status})
    finally:
        session.close()


@app.route("/api/candidates/<int:candidate_id>/notes", methods=["PUT"])
def update_candidate_notes(candidate_id: int):
    """Updates recruiter notes for a candidate."""
    data = request.json or {}
    notes = data.get("notes", "")

    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return jsonify({"error": "Candidate not found."}), 404

        candidate.notes = notes
        candidate.updated_at = datetime.utcnow()
        session.commit()
        return jsonify({"success": True, "notes": candidate.notes})
    finally:
        session.close()


@app.route("/api/match-jd", methods=["POST"])
def match_job_description():
    """
    Ranks all candidates against a Job Description or required skills list.
    Computes fit score (0-100%), matching skills, and missing skills.
    """
    data = request.json or {}
    jd_text = data.get("job_description", "").strip()
    required_skills = data.get("skills", [])

    # If no explicit skills list provided, extract skills from the job description using the parser
    if not required_skills and jd_text:
        extracted = resume_parser._extract_skills(jd_text)
        required_skills = [s["name"] for s in extracted]

    if not required_skills and not jd_text:
        return jsonify({"error": "Please provide a Job Description or list of required skills."}), 400

    # Ensure uniqueness
    target_skills_set = set(s.lower() for s in required_skills)
    total_target = len(target_skills_set) if target_skills_set else 1

    session = SessionLocal()
    try:
        candidates = session.query(Candidate).all()
        scored_candidates = []

        for c in candidates:
            cand_skills_map = {s.skill_name.lower(): s.skill_name for s in c.skills}
            
            matched = []
            missing = []

            for s_low in target_skills_set:
                if s_low in cand_skills_map:
                    matched.append(cand_skills_map[s_low])
                else:
                    # Case-preserving match
                    matched_orig = next((orig for orig in required_skills if orig.lower() == s_low), s_low)
                    missing.append(matched_orig)

            # Fit score calculation (Weighted: 85% skill overlap + 15% experience density)
            skill_score = (len(matched) / total_target) * 100
            exp_bonus = min(15.0, (c.total_experience_years or 0.0) * 2.5)
            composite_score = min(100.0, round((skill_score * 0.85) + exp_bonus, 1))

            c_dict = c.to_dict()
            c_dict["match_score"] = composite_score
            c_dict["matched_skills"] = sorted(matched)
            c_dict["missing_skills"] = sorted(missing)
            scored_candidates.append(c_dict)

        # Sort by match score descending
        scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)

        return jsonify({
            "target_skills": required_skills,
            "total_evaluated": len(scored_candidates),
            "candidates": scored_candidates
        })
    finally:
        session.close()


@app.route("/api/compare", methods=["POST"])
def compare_candidates():
    """Generates a side-by-side comparison matrix for selected candidate IDs."""
    data = request.json or {}
    candidate_ids = data.get("candidate_ids", [])
    if not candidate_ids or len(candidate_ids) < 2:
        return jsonify({"error": "Please select at least 2 candidates to compare."}), 400

    session = SessionLocal()
    try:
        candidates = session.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
        if not candidates:
            return jsonify({"error": "Candidates not found."}), 404

        all_skills_sets = [set(s.skill_name for s in c.skills) for c in candidates]
        common_skills = sorted(list(set.intersection(*all_skills_sets))) if all_skills_sets else []

        comparison_data = []
        for c in candidates:
            cand_skills = set(s.skill_name for s in c.skills)
            unique_skills = sorted(list(cand_skills - set(common_skills)))
            comparison_data.append({
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "location": c.location,
                "status": c.status,
                "total_experience_years": c.total_experience_years,
                "skills_count": len(c.skills),
                "common_skills": common_skills,
                "unique_skills": unique_skills,
                "top_education": c.education[0].to_dict() if c.education else None,
                "latest_role": c.experience[0].to_dict() if c.experience else None,
                "summary": c.summary
            })

        return jsonify({
            "candidates": comparison_data,
            "common_skills": common_skills
        })
    finally:
        session.close()


@app.route("/api/export/csv", methods=["GET"])
def export_candidates_csv():
    """Exports candidate database to CSV format."""
    session = SessionLocal()
    try:
        candidates = session.query(Candidate).order_by(desc(Candidate.parsed_at)).all()
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "Name", "Email", "Phone", "Location", "Status",
            "Experience (Years)", "Skills", "Highest Degree",
            "Field of Study", "Institution", "Parsed At"
        ])

        for c in candidates:
            highest_degree = c.education[0].degree if c.education else "N/A"
            field_study = c.education[0].field_of_study if c.education else "N/A"
            inst = c.education[0].institution if c.education else "N/A"
            skills_str = "; ".join([s.skill_name for s in c.skills])

            writer.writerow([
                c.id, c.name, c.email, c.phone, c.location, c.status,
                c.total_experience_years, skills_str, highest_degree,
                field_study, inst, c.parsed_at.strftime("%Y-%m-%d %H:%M") if c.parsed_at else ""
            ])

        output.seek(0)
        filename = f"candidates_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    finally:
        session.close()


@app.route("/api/export/json", methods=["GET"])
def export_candidates_json():
    """Exports complete candidate database to JSON format."""
    session = SessionLocal()
    try:
        candidates = session.query(Candidate).order_by(desc(Candidate.parsed_at)).all()
        return jsonify([c.to_dict(include_raw=False) for c in candidates])
    finally:
        session.close()


@app.route("/api/seed", methods=["GET", "POST"])
def seed_sample_candidates():
    """Seeds default sample candidates from sample_resumes into database."""
    samples_dir = BASE_DIR / "sample_resumes"
    session = SessionLocal()
    seeded = []
    try:
        for file_path in samples_dir.glob("*.*"):
            if file_path.suffix.lower() in [".pdf", ".docx"]:
                existing = session.query(Candidate).filter(Candidate.file_name == file_path.name).first()
                if existing:
                    continue
                raw_text = extract_text_from_file(str(file_path))
                if not raw_text.strip():
                    continue
                parsed_data = resume_parser.parse(raw_text)
                candidate = Candidate(
                    name=parsed_data.get("name", "Unknown"),
                    email=parsed_data.get("email", ""),
                    phone=parsed_data.get("phone", ""),
                    location=parsed_data.get("location", ""),
                    linkedin_url=parsed_data.get("linkedin_url"),
                    github_url=parsed_data.get("github_url"),
                    portfolio_url=parsed_data.get("portfolio_url"),
                    total_experience_years=parsed_data.get("total_experience_years", 0.0),
                    summary=parsed_data.get("summary", ""),
                    raw_text=raw_text,
                    file_name=file_path.name,
                    file_type=file_path.suffix.lower().replace(".", ""),
                    status="New"
                )
                session.add(candidate)
                session.flush()

                for s_dict in parsed_data.get("skills", []):
                    session.add(CandidateSkill(
                        candidate_id=candidate.id,
                        name=s_dict["name"],
                        category=s_dict.get("category", "General")
                    ))

                for e_dict in parsed_data.get("education", []):
                    session.add(CandidateEducation(
                        candidate_id=candidate.id,
                        degree=e_dict.get("degree", ""),
                        field_of_study=e_dict.get("field_of_study", ""),
                        institution=e_dict.get("institution", ""),
                        start_year=e_dict.get("start_year"),
                        end_year=e_dict.get("end_year"),
                        grade=e_dict.get("grade")
                    ))

                for x_dict in parsed_data.get("experience", []):
                    session.add(CandidateExperience(
                        candidate_id=candidate.id,
                        job_title=x_dict.get("job_title", ""),
                        company=x_dict.get("company", ""),
                        location=x_dict.get("location"),
                        start_date=x_dict.get("start_date"),
                        end_date=x_dict.get("end_date"),
                        description=x_dict.get("description", ""),
                        is_current=x_dict.get("is_current", False)
                    ))

                session.commit()
                seeded.append(candidate.name)

        return jsonify({
            "success": True,
            "message": f"Successfully loaded {len(seeded)} demo candidate profiles." if seeded else "Demo candidates already loaded in database.",
            "seeded": seeded
        })
    finally:
        session.close()



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
