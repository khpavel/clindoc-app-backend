from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.study import Study
from app.schemas.study import StudyCreate, StudyRead

router = APIRouter()


@router.post("/studies", response_model=StudyRead)
def create_study(study_in: StudyCreate, db: Session = Depends(get_db)):
    existing = db.query(Study).filter(Study.code == study_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Study with this code already exists")

    study = Study(
        code=study_in.code,
        title=study_in.title,
        phase=study_in.phase,
    )
    db.add(study)
    db.commit()
    db.refresh(study)
    return study


@router.get("/studies", response_model=List[StudyRead])
def list_studies(db: Session = Depends(get_db)):
    studies = db.query(Study).order_by(Study.id).all()
    return studies

