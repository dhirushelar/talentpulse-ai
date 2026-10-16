from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(64), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    github_url = Column(String(512), nullable=True)
    portfolio_url = Column(String(512), nullable=True)
    
    summary = Column(Text, nullable=True)
    total_experience_years = Column(Float, default=0.0)
    raw_text = Column(Text, nullable=True)
    
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)
    file_type = Column(String(32), nullable=False)
    status = Column(String(32), default="New", index=True)  # New, Shortlisted, Interviewing, Rejected, Hired
    notes = Column(Text, nullable=True)
    
    parsed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan", lazy="joined")
    education = relationship("CandidateEducation", back_populates="candidate", cascade="all, delete-orphan", lazy="joined")
    experience = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan", lazy="joined")

    def to_dict(self, include_raw=False):
        data = {
            "id": self.id,
            "name": self.name or "Unknown Candidate",
            "email": self.email or "N/A",
            "phone": self.phone or "N/A",
            "location": self.location or "N/A",
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "portfolio_url": self.portfolio_url,
            "summary": self.summary or "",
            "total_experience_years": round(self.total_experience_years, 1) if self.total_experience_years else 0.0,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "status": self.status or "New",
            "notes": self.notes or "",
            "parsed_at": self.parsed_at.strftime("%Y-%m-%d %H:%M:%S") if self.parsed_at else None,
            "skills": [s.to_dict() for s in self.skills],
            "skills_list": [s.skill_name for s in self.skills],
            "education": [e.to_dict() for e in self.education],
            "experience": [exp.to_dict() for exp in self.experience]
        }
        if include_raw:
            data["raw_text"] = self.raw_text
        return data


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(128), nullable=False, index=True)
    category = Column(String(64), default="General", index=True)

    candidate = relationship("Candidate", back_populates="skills")

    __table_args__ = (
        Index("ix_candidate_skill_unique", "candidate_id", "skill_name", unique=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.skill_name,
            "category": self.category
        }


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=True)
    start_year = Column(String(32), nullable=True)
    end_year = Column(String(32), nullable=True)
    grade = Column(String(64), nullable=True)

    candidate = relationship("Candidate", back_populates="education")

    def to_dict(self):
        return {
            "id": self.id,
            "degree": self.degree,
            "field_of_study": self.field_of_study,
            "institution": self.institution,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "grade": self.grade
        }


class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    start_date = Column(String(64), nullable=True)
    end_date = Column(String(64), nullable=True)
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="experience")

    def to_dict(self):
        return {
            "id": self.id,
            "job_title": self.job_title,
            "company": self.company,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_current": self.is_current,
            "description": self.description
        }
