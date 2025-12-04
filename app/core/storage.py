from pathlib import Path
from app.core.config import settings


def get_storage_dir() -> Path:
    base = Path(settings.storage_dir)
    base.mkdir(parents=True, exist_ok=True)
    return base


def build_study_source_path(study_id: int, file_name: str) -> Path:
    base = get_storage_dir() / f"study_{study_id}"
    base.mkdir(parents=True, exist_ok=True)
    return base / file_name

