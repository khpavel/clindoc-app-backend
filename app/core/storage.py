import logging
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_storage_dir() -> Path:
    base = Path(settings.storage_dir)
    base.mkdir(parents=True, exist_ok=True)
    return base


def build_study_source_path(study_id: int, file_name: str) -> Path:
    base = get_storage_dir() / f"study_{study_id}"
    base.mkdir(parents=True, exist_ok=True)
    return base / file_name


def delete_file(storage_path: str) -> bool:
    """
    Delete a file from storage using its relative storage path.
    
    Args:
        storage_path: Relative path to the file (e.g., "study_1/protocol.pdf")
        
    Returns:
        True if file was deleted successfully, False if file doesn't exist or deletion failed
    """
    try:
        base_dir = get_storage_dir()
        file_path = base_dir / storage_path
        
        # Check if file exists
        if not file_path.exists():
            logger.warning(f"File not found for deletion: {storage_path}")
            return False
        
        # Delete the file
        file_path.unlink()
        logger.info(f"Successfully deleted file: {storage_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete file {storage_path}: {e}", exc_info=True)
        return False

