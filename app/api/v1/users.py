"""
User profile endpoints.

Usage:
- GET /api/v1/users/me → get current user profile
- PATCH /api/v1/users/me → update current user profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserMe, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current user's profile.
    
    Returns the authenticated user's information including ui_language.
    """
    return current_user


@router.patch("/me", response_model=UserMe)
def update_current_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update the current user's profile.
    
    Allows updating username, full_name, email, and ui_language.
    Only provided fields will be updated.
    
    Validates:
    - ui_language must be "ru" or "en" if provided (validated by Pydantic)
    - username must be unique if changed
    - email must be unique if changed
    """
    # Update ui_language if provided (validation handled by Pydantic)
    if user_update.ui_language is not None:
        current_user.ui_language = user_update.ui_language
    
    # Update username if provided
    if user_update.username is not None:
        # Check if username is already taken by another user
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_update.username
    
    # Update full_name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    # Update email if provided
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        current_user.email = user_update.email
    
    db.commit()
    db.refresh(current_user)
    return current_user

