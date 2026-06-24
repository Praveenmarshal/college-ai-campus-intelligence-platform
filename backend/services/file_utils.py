"""
services/file_utils.py
File validation, path generation, and upload helpers.
Used by every upload endpoint across the platform.
"""

import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# MIME type → category mapping
MIME_CATEGORIES = {
    "application/pdf": "pdf",
    "application/vnd.ms-excel": "excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "text/csv": "csv",
    "text/plain": "csv",
    "image/png": "image",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/tiff": "image",
    "image/bmp": "image",
}

ALLOWED_EXTENSIONS = {
    "pdf", "xlsx", "xls", "csv", "png", "jpg", "jpeg", "tiff", "bmp",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def allowed_file(filename: str) -> bool:
    """Check whether a filename has an allowed extension."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_category(filename: str, mime_type: Optional[str] = None) -> str:
    """
    Determine the file category (pdf | excel | csv | image | resume).
    Checks MIME type first, falls back to extension.
    """
    if mime_type and mime_type in MIME_CATEGORIES:
        return MIME_CATEGORIES[mime_type]

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_map = {
        "pdf": "pdf",
        "xlsx": "excel",
        "xls": "excel",
        "csv": "csv",
        "txt": "csv",
        "png": "image",
        "jpg": "image",
        "jpeg": "image",
        "tiff": "image",
        "bmp": "image",
    }
    return ext_map.get(ext, "unknown")


def generate_safe_filename(original_name: str) -> str:
    """
    Generate a unique, safe filename.
    Format: <uuid4>_<sanitised-original>
    """
    ext = ""
    if "." in original_name:
        name_part, ext = original_name.rsplit(".", 1)
        ext = f".{ext.lower()}"

    unique_id = uuid.uuid4().hex[:12]
    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_") else "_"
        for c in original_name.rsplit(".", 1)[0]
    )[:40]

    return f"{unique_id}_{safe_name}{ext}"


def get_upload_path(base_folder: str, category: str, filename: str) -> Path:
    """
    Build the full filesystem path for a new upload.

    Args:
        base_folder: Root upload directory (e.g. "./uploads")
        category: Sub-category folder (e.g. "pdfs")
        filename: Safe filename

    Returns:
        Absolute Path object
    """
    category_dirs = {
        "pdf": "pdfs",
        "excel": "excels",
        "csv": "csvs",
        "image": "images",
        "resume": "resumes",
        "unknown": "misc",
    }
    subdir = category_dirs.get(category, "misc")
    path = Path(base_folder) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


def compute_md5(file_path: str | Path) -> str:
    """Compute the MD5 checksum of a file for deduplication."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def validate_upload(file) -> tuple[bool, str]:
    """
    Validate an uploaded file object (Flask FileStorage).

    Returns:
        (is_valid: bool, error_message: str)
    """
    if not file:
        return False, "No file provided"

    if not file.filename:
        return False, "Filename is missing"

    if not allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "unknown"
        return False, (
            f"File type '.{ext}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Check size by reading (stream position resets)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        mb = size / (1024 * 1024)
        return False, f"File too large ({mb:.1f} MB). Maximum is 50 MB."

    if size == 0:
        return False, "File is empty"

    return True, ""


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
