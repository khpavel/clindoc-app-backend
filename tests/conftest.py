"""
Pytest configuration and fixtures for testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.db.session import Base, get_db
from app.models.user import User
from app.models.study import Study
from app.core.security import get_password_hash
from app.main import app


# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db: Session) -> User:
    """
    Create a test user.
    """
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db: Session) -> User:
    """
    Create another test user for testing access control.
    """
    user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_study(db: Session, test_user: User) -> Study:
    """
    Create a test study with the test_user as owner.
    """
    study = Study(
        code="TEST-001",
        title="Test Study",
        phase="Phase 1",
        owner_id=test_user.id
    )
    db.add(study)
    db.flush()
    
    # Create StudyMember with owner role
    from app.models.study_member import StudyMember
    study_member = StudyMember(
        user_id=test_user.id,
        study_id=study.id,
        role="owner"
    )
    db.add(study_member)
    db.commit()
    db.refresh(study)
    return study


@pytest.fixture
def client(db: Session):
    """
    Create a test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

