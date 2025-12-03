"""
Image utility functions for validation and file handling.
"""
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def validate_image_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate image file.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        # Try to open with PIL
        with Image.open(file_path) as img:
            img.verify()
        
        # Reopen for format check (verify closes the file)
        with Image.open(file_path) as img:
            format_name = img.format
            if format_name not in ['PNG', 'JPEG', 'JPG', 'WEBP']:
                return False, f"Unsupported image format: {format_name}"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def save_uploaded_file(uploaded_file, temp_dir: Optional[str] = None) -> str:
    """
    Save uploaded file to temporary location.
    
    Args:
        uploaded_file: FastAPI UploadFile
        temp_dir: Temporary directory (uses system temp if None)
        
    Returns:
        Path to saved file
    """
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
    
    temp_path = Path(temp_dir) / f"upload_{os.urandom(8).hex()}.tmp"
    
    with open(temp_path, "wb") as f:
        content = uploaded_file.file.read()
        f.write(content)
    
    # Reset file pointer
    uploaded_file.file.seek(0)
    
    return str(temp_path)


def cleanup_file(file_path: str) -> None:
    """
    Clean up temporary file.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")

