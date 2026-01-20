"""Metadata extraction utilities for various file types."""

import logging
import subprocess
import exifread
from PIL import Image
from typing import Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


def extract_exif_data(file_path: Path) -> Dict[str, Any]:
    """
    Extract EXIF data from image files.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Dictionary containing EXIF data (sanitized, no binary blobs)
    """
    exif_data = {}
    
    # Fields known to contain binary data - skip these entirely
    BINARY_FIELDS = {
        'JPEGThumbnail', 'TIFFThumbnail', 'Filename',
        'EXIF MakerNote', 'MakerNote', 'PrintImageMatching',
        'InteropOffset', 'ExifOffset', 'GPSInfo',
        'ApplicationNotes', 'UserComment'  # Can contain binary
    }
    
    def _sanitize_value(value: Any) -> str:
        """Sanitize a value to remove binary data and limit length."""
        try:
            value_str = str(value)
            
            # Check if string contains binary data (null bytes or lots of unprintable chars)
            if '\x00' in value_str or sum(1 for c in value_str if not c.isprintable()) > len(value_str) * 0.1:
                # More than 10% unprintable chars = binary data, skip it
                return None
            
            # Limit length to prevent huge text fields
            if len(value_str) > 500:
                value_str = value_str[:500] + "... (truncated)"
            
            return value_str
        except:
            return None
    
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
            for tag, value in tags.items():
                # Skip known binary fields
                if tag in BINARY_FIELDS:
                    continue
                
                # Sanitize and add value
                sanitized = _sanitize_value(value)
                if sanitized:
                    exif_data[tag] = sanitized
        
        # Also try PIL for additional metadata
        try:
            with Image.open(file_path) as img:
                if hasattr(img, '_getexif') and img._getexif():
                    pil_exif = img._getexif()
                    if pil_exif:
                        for tag_id, value in pil_exif.items():
                            tag_name = Image.ExifTags.TAGS.get(tag_id, tag_id)
                            
                            # Skip binary fields
                            if tag_name in BINARY_FIELDS or str(tag_name) in BINARY_FIELDS:
                                continue
                            
                            # Skip if already have this field from exifread
                            if tag_name in exif_data or f'PIL_{tag_name}' in exif_data:
                                continue
                            
                            # Sanitize and add
                            sanitized = _sanitize_value(value)
                            if sanitized:
                                exif_data[f'PIL_{tag_name}'] = sanitized
        except:
            pass
                
    except Exception as e:
        logger.debug(f"Could not extract EXIF from {file_path}: {e}")
    
    return exif_data


def extract_metadata_by_mime(file_path: Path, mime_type: str) -> Dict[str, Any]:
    """
    Extract metadata based on MIME type.
    
    Args:
        file_path: Path to the file
        mime_type: MIME type of the file
        
    Returns:
        Dictionary containing file-specific metadata
    """
    metadata = {}
    
    try:
        # Image files
        if mime_type.startswith('image/'):
            try:
                with Image.open(file_path) as img:
                    metadata['width'] = img.width
                    metadata['height'] = img.height
                    metadata['format'] = img.format
                    metadata['mode'] = img.mode
            except Exception as e:
                logger.debug(f"Could not extract image metadata from {file_path}: {e}")
        
        # PDF files
        elif mime_type == 'application/pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    metadata['pages'] = len(pdf.pages)
                    if pdf.metadata:
                        for key, value in pdf.metadata.items():
                            metadata[f'pdf_{key}'] = str(value)
            except Exception as e:
                logger.debug(f"Could not extract PDF metadata from {file_path}: {e}")
        
        # Text files
        elif mime_type.startswith('text/'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    metadata['lines'] = content.count('\n') + 1
                    metadata['characters'] = len(content)
            except Exception as e:
                logger.debug(f"Could not extract text metadata from {file_path}: {e}")
    
    except Exception as e:
        logger.debug(f"Error extracting metadata for {file_path}: {e}")
    
    return metadata


def run_binwalk(file_path: Path) -> str:
    """
    Run binwalk on a file to analyze embedded files and data.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Binwalk output as string (sanitized to remove binary data)
    """
    try:
        # Run binwalk with basic signature scan
        # Note: We use text=False to avoid decoding issues with binary output
        result = subprocess.run(
            ['binwalk', str(file_path)],
            capture_output=True,
            text=False,  # Capture as bytes to avoid encoding issues
            timeout=30  # 30 second timeout
        )
        
        if result.returncode == 0:
            # Decode output with error handling, replacing problematic bytes
            output = result.stdout.decode('utf-8', errors='replace')
            
            # Sanitize: Remove null bytes and control characters (except newlines/tabs)
            # Keep only printable ASCII and common whitespace
            sanitized = ''.join(
                char for char in output 
                if char.isprintable() or char in '\n\t\r'
            )
            
            # Limit output length to prevent token waste (first 2000 chars should be enough)
            if len(sanitized) > 2000:
                sanitized = sanitized[:2000] + "\n... (output truncated)"
            
            return sanitized
        else:
            # Also sanitize stderr
            stderr = result.stderr.decode('utf-8', errors='replace')
            stderr_clean = ''.join(
                char for char in stderr 
                if char.isprintable() or char in '\n\t\r'
            )
            logger.debug(f"Binwalk returned non-zero for {file_path}: {stderr_clean}")
            return f"Binwalk error: {stderr_clean}"
    
    except subprocess.TimeoutExpired:
        logger.warning(f"Binwalk timed out for {file_path}")
        return "Binwalk timeout"
    
    except FileNotFoundError:
        logger.debug("Binwalk not installed, skipping")
        return "Binwalk not available"
    
    except Exception as e:
        logger.debug(f"Error running binwalk on {file_path}: {e}")
        return f"Binwalk error: {str(e)}"
