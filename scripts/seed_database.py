"""
Pre-populate the database with the generated sample resumes.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app
import io

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "sample_resumes"

def seed():
    print("Seeding sample resumes into the database...")
    with app.test_client() as client:
        for file_path in SAMPLES_DIR.glob("*.*"):
            if file_path.suffix.lower() in [".pdf", ".docx"]:
                with open(file_path, "rb") as f:
                    data = {
                        "resumes": (io.BytesIO(f.read()), file_path.name)
                    }
                    res = client.post("/api/upload", data=data, content_type="multipart/form-data")
                    if res.status_code == 200:
                        parsed = res.get_json()
                        print(f"Successfully parsed and stored: {file_path.name} (Candidate: {parsed['candidates'][0]['name']})")
                    else:
                        print(f"Failed to seed {file_path.name}: {res.get_json()}")

if __name__ == "__main__":
    seed()
