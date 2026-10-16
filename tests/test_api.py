import io
import pytest
from pathlib import Path
from app import app
from database import init_db

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "sample_resumes"

@pytest.fixture
def client():
    app.config["TESTING"] = True
    init_db()
    with app.test_client() as client:
        yield client

def test_api_status(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "online"
    assert "supported_formats" in data

def test_upload_and_query_flow(client):
    pdf_path = SAMPLES_DIR / "sample_john_doe_backend.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    # 1. Upload resume
    data = {
        "resumes": (io.BytesIO(file_bytes), "sample_john_doe_backend.pdf")
    }
    upload_res = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert upload_res.status_code == 200
    upload_data = upload_res.get_json()
    assert upload_data["parsed_count"] == 1
    candidate = upload_data["candidates"][0]
    candidate_id = candidate["id"]
    assert "John Doe" in candidate["name"]

    # 2. Get Candidates list with skill filter
    list_res = client.get("/api/candidates?skills=Python")
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert list_data["total"] >= 1

    # 3. Get single candidate profile
    detail_res = client.get(f"/api/candidates/{candidate_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.get_json()
    assert detail_data["email"] == "john.doe@email.com"
    assert "raw_text" in detail_data

    # 4. Check statistics
    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.get_json()
    assert stats_data["total_candidates"] >= 1

    # 5. Update Status & Notes
    status_res = client.put(f"/api/candidates/{candidate_id}/status", json={"status": "Shortlisted"})
    assert status_res.status_code == 200
    assert status_res.get_json()["status"] == "Shortlisted"

    notes_res = client.put(f"/api/candidates/{candidate_id}/notes", json={"notes": "Strong background in Flask & PostgreSQL"})
    assert notes_res.status_code == 200

    # 6. Test JD Fit Matcher
    jd_payload = {
        "job_description": "We are seeking a Senior Backend Engineer proficient in Python, Flask, and PostgreSQL."
    }
    jd_res = client.post("/api/match-jd", json=jd_payload)
    assert jd_res.status_code == 200
    jd_data = jd_res.get_json()
    assert jd_data["total_evaluated"] >= 1
    assert jd_data["candidates"][0]["match_score"] > 50

    # 7. Test Export CSV & JSON
    csv_res = client.get("/api/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.content_type

    json_res = client.get("/api/export/json")
    assert json_res.status_code == 200
    assert isinstance(json_res.get_json(), list)

    # 8. Clean up - Delete candidate
    del_res = client.delete(f"/api/candidates/{candidate_id}")
    assert del_res.status_code == 200
