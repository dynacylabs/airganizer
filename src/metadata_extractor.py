"""Metadata extraction utilities for various file types."""

import json
import logging
import subprocess
import tempfile
import warnings
import exifread
from typing import Dict, Any, List, Tuple
from pathlib import Path

# Import PIL first so we can reference it in warning filters
from PIL import Image

# Suppress PIL warnings about large images and EXIF issues
warnings.filterwarnings('ignore', category=Image.DecompressionBombWarning)
warnings.filterwarnings('ignore', message='Truncated File Read')
warnings.filterwarnings('ignore', message='Possibly corrupted')
warnings.filterwarnings('ignore', message='Unexpected slice length')


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
        
        # Video files
        elif mime_type.startswith('video/'):
            video_metadata = extract_video_metadata(file_path)
            if video_metadata:
                metadata.update(video_metadata)
    
    except Exception as e:
        logger.debug(f"Error extracting metadata for {file_path}: {e}")
    
    return metadata


def extract_video_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from video files using ffprobe.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Dictionary containing video metadata (duration, resolution, codec, fps, etc.)
    """
    metadata = {}
    
    try:
        # Use ffprobe to extract video metadata
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # Extract format information
            if 'format' in data:
                fmt = data['format']
                if 'duration' in fmt:
                    try:
                        duration_sec = float(fmt['duration'])
                        metadata['duration_seconds'] = round(duration_sec, 2)
                        # Convert to human-readable format
                        hours = int(duration_sec // 3600)
                        minutes = int((duration_sec % 3600) // 60)
                        seconds = int(duration_sec % 60)
                        if hours > 0:
                            metadata['duration'] = f"{hours}h {minutes}m {seconds}s"
                        elif minutes > 0:
                            metadata['duration'] = f"{minutes}m {seconds}s"
                        else:
                            metadata['duration'] = f"{seconds}s"
                    except:
                        pass
                
                if 'bit_rate' in fmt:
                    try:
                        bitrate_kbps = int(fmt['bit_rate']) // 1000
                        metadata['bitrate_kbps'] = bitrate_kbps
                    except:
                        pass
                
                if 'size' in fmt:
                    try:
                        metadata['file_size_mb'] = round(int(fmt['size']) / (1024 * 1024), 2)
                    except:
                        pass
            
            # Extract video stream information
            video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
            if video_streams:
                video = video_streams[0]  # Use first video stream
                
                if 'codec_name' in video:
                    metadata['video_codec'] = video['codec_name']
                
                if 'width' in video and 'height' in video:
                    metadata['width'] = video['width']
                    metadata['height'] = video['height']
                    metadata['resolution'] = f"{video['width']}x{video['height']}"
                
                if 'avg_frame_rate' in video:
                    try:
                        # Parse fraction like "30000/1001" or "30/1"
                        fps_str = video['avg_frame_rate']
                        if '/' in fps_str:
                            num, den = fps_str.split('/')
                            fps = float(num) / float(den)
                            metadata['fps'] = round(fps, 2)
                    except:
                        pass
                
                if 'bit_rate' in video:
                    try:
                        video_bitrate_kbps = int(video['bit_rate']) // 1000
                        metadata['video_bitrate_kbps'] = video_bitrate_kbps
                    except:
                        pass
            
            # Extract audio stream information
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            if audio_streams:
                audio = audio_streams[0]  # Use first audio stream
                
                if 'codec_name' in audio:
                    metadata['audio_codec'] = audio['codec_name']
                
                if 'sample_rate' in audio:
                    metadata['audio_sample_rate'] = audio['sample_rate']
                
                if 'channels' in audio:
                    metadata['audio_channels'] = audio['channels']
        
        else:
            logger.debug(f"ffprobe returned non-zero for {file_path}: {result.stderr}")
    
    except FileNotFoundError:
        logger.debug("ffprobe not installed, skipping video metadata extraction")
    except subprocess.TimeoutExpired:
        logger.warning(f"ffprobe timed out for {file_path}")
    except Exception as e:
        logger.debug(f"Error extracting video metadata from {file_path}: {e}")
    
    return metadata


def extract_video_frames(file_path: Path, num_frames: int = 4) -> List[str]:
    """
    Extract frames from a video at evenly spaced intervals for AI analysis.
    Frames are extracted deterministically at fixed percentages of video duration.
    
    Args:
        file_path: Path to the video file
        num_frames: Number of frames to extract (default: 4)
        
    Returns:
        List of base64-encoded frame images (JPEG format)
    """
    frames = []
    
    try:
        # First get video duration
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            logger.debug(f"Could not get video duration for {file_path}")
            return frames
        
        data = json.loads(result.stdout)
        duration = float(data.get('format', {}).get('duration', 0))
        
        if duration <= 0:
            logger.debug(f"Invalid duration for {file_path}")
            return frames
        
        # Create temporary directory for frames
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract frames at evenly spaced intervals
            # For determinism: extract at 10%, 35%, 65%, 90% of duration
            # This avoids black frames at start/end and provides good coverage
            percentages = [10, 35, 65, 90] if num_frames == 4 else \
                         [10, 50, 90] if num_frames == 3 else \
                         [25, 75] if num_frames == 2 else \
                         [50] if num_frames == 1 else \
                         [i * (100 / (num_frames + 1)) for i in range(1, num_frames + 1)]
            
            for idx, percentage in enumerate(percentages[:num_frames]):
                timestamp = duration * (percentage / 100.0)
                frame_path = temp_path / f"frame_{idx:03d}.jpg"
                
                # Extract single frame at specific timestamp
                extract_result = subprocess.run(
                    [
                        'ffmpeg',
                        '-ss', str(timestamp),
                        '-i', str(file_path),
                        '-frames:v', '1',
                        '-q:v', '2',  # High quality JPEG
                        '-y',  # Overwrite output file
                        str(frame_path)
                    ],
                    capture_output=True,
                    timeout=30,
                    stderr=subprocess.DEVNULL  # Suppress ffmpeg output
                )
                
                if extract_result.returncode == 0 and frame_path.exists():
                    # Read and encode frame as base64
                    import base64
                    with open(frame_path, 'rb') as f:
                        frame_data = base64.b64encode(f.read()).decode('utf-8')
                        frames.append(frame_data)
                    logger.debug(f"Extracted frame at {timestamp:.2f}s ({percentage}%) for {file_path.name}")
                else:
                    logger.debug(f"Failed to extract frame at {timestamp:.2f}s for {file_path}")
        
        logger.debug(f"Extracted {len(frames)} frames from {file_path.name}")
    
    except FileNotFoundError:
        logger.debug("ffmpeg not installed, cannot extract video frames")
    except subprocess.TimeoutExpired:
        logger.warning(f"Frame extraction timed out for {file_path}")
    except Exception as e:
        logger.debug(f"Error extracting frames from {file_path}: {e}")
    
    return frames


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
