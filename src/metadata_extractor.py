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
        Dictionary containing EXIF data
    """
    exif_data = {}
    
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
            for tag, value in tags.items():
                # Skip thumbnails and makernotes
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                    try:
                        exif_data[tag] = str(value)
                    except:
                        pass
        
        # Also try PIL for additional metadata
        try:
            with Image.open(file_path) as img:
                if hasattr(img, '_getexif') and img._getexif():
                    pil_exif = img._getexif()
                    if pil_exif:
                        for tag_id, value in pil_exif.items():
                            try:
                                tag_name = Image.ExifTags.TAGS.get(tag_id, tag_id)
                                if tag_name not in exif_data:
                                    exif_data[f'PIL_{tag_name}'] = str(value)
                            except:
                                pass
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
        Binwalk output as string
    """
    try:
        # Run binwalk with basic signature scan
        result = subprocess.run(
            ['binwalk', str(file_path)],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            logger.debug(f"Binwalk returned non-zero for {file_path}: {result.stderr}")
            return f"Binwalk error: {result.stderr}"
    
    except subprocess.TimeoutExpired:
        logger.warning(f"Binwalk timed out for {file_path}")
        return "Binwalk timeout"
    
    except FileNotFoundError:
        logger.debug("Binwalk not installed, skipping")
        return "Binwalk not available"
    
    except Exception as e:
        logger.debug(f"Error running binwalk on {file_path}: {e}")
        return f"Binwalk error: {str(e)}"
