from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_current_active_user
from app.models.study import Study
from app.models.user import User
from app.schemas.study import StudyCreate, StudyRead

router = APIRouter()


@router.post("/studies", response_model=StudyRead)
def create_study(
    study_in: StudyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
def list_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    studies = db.query(Study).order_by(Study.id).all()
    return studies

