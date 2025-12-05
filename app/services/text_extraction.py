from pathlib import Path
from typing import Optional


def extract_text_from_file(path: Path) -> str:
    """
    Minimal text extractor for MVP.
    - If file extension in {'.txt', '.md'}: read as UTF-8 text.
    - Otherwise: return a stub string indicating that content is not parsed yet.
    """
    suffix = path.suffix.lower()
    
    if suffix in [".txt", ".md"]:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    # For unsupported file types
    return f"[[UNPARSED FILE: {path.name} – text extraction not implemented in MVP]]"

