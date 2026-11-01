from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv
import datetime
import random
import string

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Setup SQLAlchemy Database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DATABASE MODEL ---
class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String, unique=True, index=True)
    college = Column(String, index=True)
    category = Column(String)
    description = Column(Text)
    contact_email = Column(String, nullable=True)
    status = Column(String, default="Pending Review")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Create tables in Neon PostgreSQL
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="CampusShield API", version="1.0")

# Enable CORS so your Next.js frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC SCHEMAS ---
class ReportCreate(BaseModel):
    college: str
    category: str
    description: str
    contact_email: Optional[str] = None

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "CampusShield Backend is running securely!"}

@app.post("/api/reports", status_code=status.HTTP_201_CREATED)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    # Generate unique 11-character tracking ID like CS-A1B2C3D4
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    tracking_id = "CS-" + "".join(random.choices(chars, k=8))
    
    db_report = ReportModel(
        tracking_id=tracking_id,
        college=report.college,
        category=report.category,
        description=report.description,
        contact_email=report.contact_email
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return {
        "message": "Report submitted securely",
        "tracking_id": tracking_id,
        "status": db_report.status
    }

@app.get("/api/reports/{tracking_id}")
def get_report_status(tracking_id: str, db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.tracking_id == tracking_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Tracking ID not found")
    
    return {
        "tracking_id": report.tracking_id,
        "college": report.college,
        "category": report.category,
        "status": report.status,
        "created_at": report.created_at
    }