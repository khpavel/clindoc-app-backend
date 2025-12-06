from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403
from app.models.study import Study
from app.models.study_member import StudyMember
from app.models.user import User
from app.schemas.study import StudyCreate, StudyRead
from app.schemas.study_member import StudyMemberRead, StudyMemberAddPayload, StudyMemberMeResponse
from app.services.study_members import get_user_study_role

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
        owner_id=current_user.id,
        status=study_in.status,
        indication=study_in.indication,
        sponsor_name=study_in.sponsor_name,
    )
    db.add(study)
    db.flush()  # Flush to get study.id
    
    # Create StudyMember with role "owner" for the current user
    study_member = StudyMember(
        user_id=current_user.id,
        study_id=study.id,
        role="owner",
    )
    db.add(study_member)
    db.commit()
    db.refresh(study)
    return study


@router.get("/studies", response_model=List[StudyRead])
def list_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all studies where the current user is a member.
    """
    # Get all studies where user is a member
    studies = (
        db.query(Study)
        .join(StudyMember)
        .filter(StudyMember.user_id == current_user.id)
        .order_by(Study.id)
        .all()
    )
    return studies


@router.get("/studies/{study_id}", response_model=StudyRead)
def get_study(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Get a specific study by ID.
    
    Only members of the study can view it.
    Returns 404 if study doesn't exist.
    Returns 403 if user is not a member of the study.
    """
    return study


@router.get(
    "/studies/{study_id}/members",
    response_model=List[StudyMemberRead]
)
def list_study_members(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Получить список участников исследования.
    
    Только участники исследования (StudyMember) или глобальные администраторы
    могут видеть список участников.
    """
    # Проверка, что исследование существует
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Проверка доступа: текущий пользователь должен быть участником исследования
    # TODO: Добавить проверку на глобального администратора, когда такая роль будет реализована
    user_role = get_user_study_role(db, current_user.id, study_id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You must be a member of this study to view its members"
        )
    
    # Выборка всех StudyMember с данным study_id
    members = (
        db.query(StudyMember)
        .filter(StudyMember.study_id == study_id)
        .order_by(StudyMember.created_at)
        .all()
    )
    
    # Загружаем данные пользователей для каждого участника
    for member in members:
        if not member.user:
            member.user = db.query(User).filter(User.id == member.user_id).first()
    
    return members


@router.get(
    "/studies/{study_id}/members/me",
    response_model=StudyMemberMeResponse,
)
def get_my_study_membership(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Возвращает membership текущего пользователя в заданном исследовании.

    404 - если исследование не существует.
    403 - если пользователь не является участником данного исследования.
    """
    # 1. Проверяем, что study существует
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )

    # 2. Ищем membership текущего пользователя в этом исследовании
    membership = (
        db.query(StudyMember)
        .options(joinedload(StudyMember.user))
        .filter(
            StudyMember.study_id == study_id,
            StudyMember.user_id == current_user.id,
        )
        .first()
    )

    if not membership:
        # Пользователь не участник исследования
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: user is not a member of this study",
        )

    return membership


@router.post(
    "/studies/{study_id}/members/{user_id}",
    response_model=StudyMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_study_member_by_user_id(
    study_id: int,
    user_id: int,
    payload: StudyMemberAddPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Добавить участника к исследованию по user_id из path.
    
    Только владелец исследования (owner) или глобальный администратор может добавлять участников.
    Не допускается добавление одного и того же пользователя дважды.
    
    Примечание: Этот эндпоинт заменяет старый POST /studies/{study_id}/members (с user_id в body).
    Старый интерфейс больше не поддерживается.
    """
    # Проверка, что исследование существует
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Проверка, что пользователь с user_id существует
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Определить роль current_user в этом исследовании
    user_role = get_user_study_role(db, current_user.id, study_id)
    
    # Проверка прав: только owner или admin может добавлять участников
    # TODO: Добавить проверку на глобального администратора, когда такая роль будет реализована
    if not user_role or user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only study owners can add members"
        )
    
    # Проверка, нет ли уже записи StudyMember с такой парой (study_id, user_id)
    existing_member = (
        db.query(StudyMember)
        .filter(
            StudyMember.study_id == study_id,
            StudyMember.user_id == user_id
        )
        .first()
    )
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user already in study"
        )
    
    # Проверка: запрещаем менять существующего owner через этот эндпоинт
    # Если уже есть owner, не позволяем добавлять нового (смена owner - отдельная задача)
    if payload.role == "owner":
        existing_owner = (
            db.query(StudyMember)
            .filter(
                StudyMember.study_id == study_id,
                StudyMember.role == "owner"
            )
            .first()
        )
        if existing_owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change study owner through this endpoint"
            )
    
    # Создание новой записи StudyMember
    study_member = StudyMember(
        study_id=study_id,
        user_id=user_id,
        role=payload.role,
    )
    db.add(study_member)
    db.commit()
    db.refresh(study_member)
    
    # Загружаем данные пользователя для ответа
    study_member.user = target_user
    
    return study_member


@router.delete(
    "/studies/{study_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_study_member(
    study_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Удалить участника исследования.
    
    Только владелец исследования (owner) может удалять участников.
    Нельзя удалить самого себя как единственного owner, если других owners нет.
    """
    # Найти StudyMember по user_id (member_id в пути - это user_id) и study_id
    member = db.query(StudyMember).filter(
        StudyMember.user_id == member_id,
        StudyMember.study_id == study_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Определить роль текущего пользователя в этом исследовании
    user_role = get_user_study_role(db, current_user.id, study_id)
    
    # Проверка прав: только owner может удалять участников
    # TODO: Добавить проверку на глобального администратора, когда такая роль будет реализована
    if not user_role or user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only study owners can remove members"
        )
    
    # Проверка: нельзя удалить самого себя как единственного owner
    if member.role == "owner" and member.user_id == current_user.id:
        # Проверить, есть ли другие owners для этого исследования
        other_owners_count = (
            db.query(StudyMember)
            .filter(
                StudyMember.study_id == study_id,
                StudyMember.role == "owner",
                StudyMember.user_id != member_id
            )
            .count()
        )
        
        if other_owners_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner of the study"
            )
    
    # Удалить запись
    db.delete(member)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

