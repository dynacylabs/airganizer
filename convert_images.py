#!/usr/bin/env python3
"""
Script to convert all image files to a uniform format (JPEG).
Uses Pillow to convert while preserving EXIF metadata.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm

try:
    from PIL import Image
    from PIL import UnidentifiedImageError
    # Increase decompression bomb limit for large legitimate images
    Image.MAX_IMAGE_PIXELS = None  # Disable limit (or set to larger value like 500000000)
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("ERROR: PIL/Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)

try:
    import pillow_heif
    # Register HEIF opener with Pillow
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

try:
    import imageio.v3 as iio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False


def identify_with_binwalk(file_path):
    """
    Use binwalk to identify file signatures.
    Returns a more specific type if found, None otherwise.
    """
    try:
        result = subprocess.run(
            ['binwalk', '-B', str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            output = result.stdout.lower()
            if 'zip archive' in output or 'pk\x03\x04' in output:
                return 'application/zip'
            elif 'gzip' in output:
                return 'application/gzip'
            elif 'jpeg image' in output:
                return 'image/jpeg'
            elif 'png image' in output:
                return 'image/png'
            elif 'pdf document' in output:
                return 'application/pdf'
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None


def identify_with_file_command(file_path):
    """
    Use the file command with MIME type detection.
    """
    try:
        result = subprocess.run(
            ['file', '--mime-type', '-b', str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            mime_type = result.stdout.strip()
            if mime_type and mime_type != 'application/octet-stream':
                return mime_type
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None


def identify_by_extension(file_path):
    """
    Fallback: identify by file extension.
    """
    extension_map = {
        # Archives
        '.zip': 'application/zip',
        '.gz': 'application/gzip',
        '.tar': 'application/x-tar',
        '.7z': 'application/x-7z-compressed',
        '.rar': 'application/x-rar',
        '.arc': 'application/x-archive',
        
        # Documents
        '.pdf': 'application/pdf',
        
        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.webp': 'image/webp',
        '.heic': 'image/heic',
        '.heif': 'image/heif',
        '.heics': 'image/heic-sequence',
        '.heifs': 'image/heif-sequence',
        '.avci': 'image/heic',
        '.avcs': 'image/heic-sequence',
        '.ico': 'image/vnd.microsoft.icon',
        '.svg': 'image/svg+xml',
        '.svgz': 'image/svg+xml',
        '.psd': 'image/vnd.adobe.photoshop',
        '.psb': 'image/vnd.adobe.photoshop',
        '.xcf': 'image/x-xcf',
        '.tga': 'image/x-tga',
        '.dds': 'image/vnd.ms-dds',
        '.jp2': 'image/jp2',
        '.jpx': 'image/jpx',
        '.j2k': 'image/j2k',
        '.jpm': 'image/jpm',
        '.tn': 'image/x-thumbnail',
        '.raw': 'image/x-raw',
        '.cr2': 'image/x-canon-cr2',
        '.nef': 'image/x-nikon-nef',
        '.arw': 'image/x-sony-arw',
        '.dng': 'image/x-adobe-dng',
        
        # Videos
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.m4v': 'video/x-m4v',
        '.3gp': 'video/3gpp',
        '.3g2': 'video/3gpp2',
        '.mpg': 'video/mpeg',
        '.mpeg': 'video/mpeg',
        
        # Audio
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/x-wav',
        '.m4a': 'audio/x-m4a',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac',
        '.wma': 'audio/x-ms-wma',
        
        # Databases
        '.db': 'application/vnd.sqlite3',
        '.sqlite': 'application/vnd.sqlite3',
        '.sqlite3': 'application/vnd.sqlite3',
        
        # Executables
        '.exe': 'application/vnd.microsoft.portable-executable',
        '.dll': 'application/x-sharedlib',
        '.so': 'application/x-sharedlib',
        '.dylib': 'application/x-sharedlib',
        '.jar': 'application/java-archive',
        '.class': 'application/x-java-applet',
        '.apk': 'application/vnd.android.package-archive',
        '.deb': 'application/x-debian-package',
        '.rpm': 'application/x-rpm',
        '.dmg': 'application/x-apple-diskimage',
        '.iso': 'application/x-iso9660-image',
        
        # Apple proprietary
        '.itl': 'application/x-itunes-library',
        '.itdb': 'application/x-itunes-database',
        '.ipa': 'application/x-ios-app',
    }
    
    suffix = file_path.suffix.lower()
    return extension_map.get(suffix)


def identify_by_content_analysis(file_path):
    """
    Analyze file content for magic bytes and patterns.
    More comprehensive header analysis.
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(512)  # Read first 512 bytes
            
            if len(header) < 4:
                return None
            
            # Archives
            if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06'):
                return 'application/zip'
            elif header.startswith(b'\x1f\x8b'):
                return 'application/gzip'
            elif header.startswith(b'Rar!'):
                return 'application/x-rar'
            elif header.startswith(b'7z\xbc\xaf\x27\x1c'):
                return 'application/x-7z-compressed'
            
            # Executables
            elif header.startswith(b'\x7fELF'):
                return 'application/x-executable'
            elif header.startswith(b'MZ'):
                return 'application/vnd.microsoft.portable-executable'
            elif header.startswith(b'\xca\xfe\xba\xbe'):
                return 'application/x-mach-binary'
            
            # Documents
            elif header.startswith(b'%PDF'):
                return 'application/pdf'
            
            # Images
            elif header.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image/png'
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                return 'image/gif'
            elif header.startswith(b'BM'):
                return 'image/bmp'
            elif header.startswith(b'II\x2a\x00') or header.startswith(b'MM\x00\x2a'):
                return 'image/tiff'
            elif header.startswith(b'RIFF') and b'WEBP' in header[:16]:
                return 'image/webp'
            # HEIC/HEIF (Apple format)
            elif len(header) >= 12 and header[4:12] == b'ftypheic':
                return 'image/heic'
            elif len(header) >= 12 and header[4:12] == b'ftypheix':
                return 'image/heic-sequence'
            elif len(header) >= 12 and header[4:12] == b'ftyphevc':
                return 'image/heic'
            elif len(header) >= 12 and header[4:12] == b'ftyphevx':
                return 'image/heic-sequence'
            elif len(header) >= 12 and (header[4:12] == b'ftypmif1' or header[4:12] == b'ftypmsf1'):
                return 'image/heif'
            # Photoshop
            elif header.startswith(b'8BPS'):
                return 'image/vnd.adobe.photoshop'
            # ICO
            elif header.startswith(b'\x00\x00\x01\x00'):
                return 'image/vnd.microsoft.icon'
            # TGA (Truevision TGA/TARGA)
            elif len(header) >= 18:
                # TGA has no magic number, but check for common patterns
                # Bytes 1-2 are color map type (0 or 1) and image type (0-11)
                if header[1] in (0, 1) and header[2] in range(0, 12):
                    # Could be TGA, return tentative type
                    return 'image/x-tga'
            
            # Videos - More thorough detection
            elif header.startswith(b'RIFF') and b'AVI ' in header[:16]:
                return 'video/x-msvideo'
            
            # QuickTime/MOV - check for ftyp atom
            elif len(header) >= 12:
                # QuickTime files have atoms with 4-byte size + 4-byte type
                if header[4:8] == b'ftyp':
                    # Check for QuickTime/MOV signature
                    if b'qt  ' in header[:32] or b'isom' in header[:32] or b'mp42' in header[:32]:
                        # Could be MOV or MP4
                        if b'qt  ' in header[:32]:
                            return 'video/quicktime'
                        else:
                            return 'video/mp4'
                elif header[4:8] == b'moov' or header[4:8] == b'mdat':
                    return 'video/quicktime'
            
            # ASF/WMV/WMA files
            elif header.startswith(b'\x30\x26\xb2\x75\x8e\x66\xcf\x11\xa6\xd9\x00\xaa\x00\x62\xce\x6c'):
                # ASF format - check if it's video or audio
                # Would need deeper parsing, but generally WMV
                return 'video/x-ms-asf'
            
            # FLV (Flash Video)
            elif header.startswith(b'FLV\x01'):
                return 'video/x-flv'
            
            # Matroska/WebM (MKV)
            elif header.startswith(b'\x1a\x45\xdf\xa3'):
                return 'video/x-matroska'
            
            # MPEG video
            elif header.startswith(b'\x00\x00\x01\xba') or header.startswith(b'\x00\x00\x01\xb3'):
                return 'video/mpeg'
            
            # Audio files
            elif header.startswith(b'ID3') or (len(header) >= 2 and header[0:2] == b'\xff\xfb'):
                return 'audio/mpeg'  # MP3
            elif header.startswith(b'OggS'):
                # Could be audio or video, check for vorbis
                if b'vorbis' in header:
                    return 'audio/ogg'
                elif b'theora' in header:
                    return 'video/ogg'
                return 'audio/ogg'  # Default to audio
            elif header.startswith(b'RIFF') and b'WAVE' in header[:16]:
                return 'audio/x-wav'
            elif len(header) >= 8 and header[4:8] == b'ftyp' and b'M4A' in header[:32]:
                return 'audio/x-m4a'
            elif header.startswith(b'fLaC'):
                return 'audio/flac'
            
            # Database
            elif header.startswith(b'SQLite format 3'):
                return 'application/vnd.sqlite3'
            
            # Text-based formats
            elif b'<html' in header.lower() or b'<!doctype html' in header.lower():
                return 'text/html'
            elif header.startswith(b'<?xml'):
                return 'text/xml'
            elif header.startswith(b'{') and b'"' in header:
                # Likely JSON
                return 'application/json'
            
            # iTunes Library files - proprietary format
            # These typically don't have a standard magic number
            # Let file command handle these
                
    except Exception:
        pass
    
    return None


def get_enhanced_mime_type(file_path, mime_detector):
    """
    Get MIME type using multiple detection methods.
    Prioritizes accuracy over generic octet-stream results.
    """
    # First try: python-magic (libmagic)
    try:
        mime_type = mime_detector.from_file(str(file_path))
    except Exception:
        mime_type = 'error/unknown'
    
    # If we get generic octet-stream, try harder
    if mime_type == 'application/octet-stream':
        # Try content analysis first (fastest, most reliable)
        specific_type = identify_by_content_analysis(file_path)
        if specific_type:
            return specific_type
        
        # Try file command (very good at obscure formats)
        specific_type = identify_with_file_command(file_path)
        if specific_type:
            return specific_type
        
        # Try binwalk if available (good for embedded/firmware)
        specific_type = identify_with_binwalk(file_path)
        if specific_type:
            return specific_type
        
        # LAST RESORT ONLY: check file extension for truly unknown formats
        # Only use this for proprietary formats that have no magic bytes
        specific_type = identify_by_extension(file_path)
        if specific_type:
            return specific_type
    
    return mime_type


def convert_image(input_path, output_path, format_type='JPEG', quality=95, verbose=False):
    """
    Convert image file using Pillow (or cairosvg for SVG, imageio as fallback).
    Preserves EXIF metadata where possible.
    Handles HEIC, corrupted files, and various formats.
    
    Args:
        input_path: Input image file
        output_path: Output image file
        format_type: Output format ('JPEG' or 'PNG')
        quality: JPEG quality (1-100, higher=better)
        verbose: Show detailed output
    
    Returns: (success, error_message)
    """
    img = None
    try:
        # Handle SVG files specially
        if input_path.suffix.lower() in ('.svg', '.svgz'):
            if not CAIROSVG_AVAILABLE:
                return False, "cairosvg not installed (required for SVG conversion)"
            
            # Convert SVG to PNG first, then to target format if JPEG
            if format_type == 'JPEG':
                # SVG -> PNG -> JPEG (to preserve quality)
                png_data = cairosvg.svg2png(url=str(input_path))
                from io import BytesIO
                img = Image.open(BytesIO(png_data))
                
                # Convert to RGB for JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.save(output_path, format='JPEG', quality=quality, optimize=True)
                img.close()
            else:
                # SVG -> PNG directly
                cairosvg.svg2png(url=str(input_path), write_to=str(output_path))
            
            return True, None
        
        # Try Pillow first (works for most formats including HEIC if pillow-heif installed)
        try:
            img = Image.open(input_path)
            
            # Load image data to catch truncated/corrupted files early
            try:
                img.load()
            except (OSError, IOError) as e:
                # Truncated or corrupted file, try imageio fallback
                if IMAGEIO_AVAILABLE:
                    if verbose:
                        print(f"    Pillow failed ({e}), trying imageio fallback...")
                    img.close()
                    return convert_image_imageio(input_path, output_path, format_type, quality, verbose)
                else:
                    raise
            
            # Preserve EXIF data
            exif = img.info.get('exif', b'')
            
            # Convert RGBA to RGB for JPEG (no transparency support)
            if format_type == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif format_type == 'JPEG' and img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save with metadata
            save_kwargs = {}
            if format_type == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
                if exif:
                    save_kwargs['exif'] = exif
            elif format_type == 'PNG':
                save_kwargs['optimize'] = True
                # PNG doesn't support EXIF directly, metadata is in different format
            
            img.save(output_path, format=format_type, **save_kwargs)
            return True, None
            
        except (OSError, IOError, UnidentifiedImageError) as e:
            # Pillow can't handle this format, try imageio
            if IMAGEIO_AVAILABLE:
                if verbose:
                    print(f"    Pillow failed, trying imageio fallback...")
                if img:
                    img.close()
                return convert_image_imageio(input_path, output_path, format_type, quality, verbose)
            else:
                raise
            
    except Exception as e:
        if img:
            try:
                img.close()
            except:
                pass
        return False, str(e)
    finally:
        if img:
            try:
                img.close()
            except:
                pass


def convert_image_imageio(input_path, output_path, format_type='JPEG', quality=95, verbose=False):
    """
    Fallback image converter using imageio.
    Used when Pillow fails to open/convert an image.
    
    Returns: (success, error_message)
    """
    try:
        # Read with imageio
        img_array = iio.imread(input_path)
        
        # Convert to RGB if needed (imageio returns numpy array)
        import numpy as np
        if len(img_array.shape) == 2:
            # Grayscale, convert to RGB
            img_array = np.stack([img_array] * 3, axis=-1)
        elif img_array.shape[2] == 4:
            # RGBA, convert to RGB with white background
            alpha = img_array[:, :, 3:4] / 255.0
            rgb = img_array[:, :, :3]
            white_bg = np.ones_like(rgb) * 255
            img_array = (rgb * alpha + white_bg * (1 - alpha)).astype(np.uint8)
        
        # Convert numpy array back to PIL for saving
        img = Image.fromarray(img_array)
        
        # Save
        if format_type == 'JPEG':
            img.save(output_path, format='JPEG', quality=quality, optimize=True)
        else:
            img.save(output_path, format='PNG', optimize=True)
        
        img.close()
        return True, None
        
    except Exception as e:
        return False, f"imageio fallback failed: {str(e)}"


def scan_and_convert_images(directory_path, format_type='JPEG', quality=95, delete_original=False, dry_run=True, verbose=False):
    """
    Scan directory and convert all image files to specified format.
    """
    mime_detector = magic.Magic(mime=True)
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Determine file extension
    ext = '.jpg' if format_type == 'JPEG' else '.png'
    
    print(f"Scanning directory: {root_path}")
    print(f"Target format: {format_type}")
    if format_type == 'JPEG':
        print(f"Quality: {quality}%")
    if dry_run:
        print("DRY RUN MODE - No files will be converted")
    else:
        print("⚠️  CONVERSION MODE - Files will be converted!")
    
    print("\nCounting files...")
    
    # Collect all files
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    
    # Filter image files (include all image types including SVG)
    # Also check by extension as fallback for files MIME detection missed
    print("Identifying image files...")
    image_files = []
    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
        '.heic', '.heif', '.heics', '.heifs', '.svg', '.svgz', '.ico',
        '.psd', '.psb', '.xcf', '.tga', '.dds', '.jp2', '.jpx', '.j2k',
        '.raw', '.cr2', '.nef', '.arw', '.dng'
    }
    
    for file_path in tqdm(all_files, desc="Checking MIME types", unit="file"):
        mime_type = get_enhanced_mime_type(file_path, mime_detector)
        # Include if MIME type is image/* OR if extension is an image extension
        if (mime_type and mime_type.startswith('image/')) or file_path.suffix.lower() in image_extensions:
            # Use MIME type if available, otherwise infer from extension
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = identify_by_extension(file_path) or 'image/unknown'
            image_files.append((file_path, mime_type))
    
    print(f"\nFound {len(image_files)} image files to process")
    
    # Check for missing optional dependencies
    svg_count = sum(1 for f, m in image_files if m == 'image/svg+xml')
    if svg_count > 0 and not CAIROSVG_AVAILABLE:
        print(f"\n⚠️  WARNING: Found {svg_count} SVG files but cairosvg is not installed.")
        print("   SVG files will fail to convert. Install with: pip install cairosvg")
    
    heic_count = sum(1 for f, m in image_files if 'heic' in m or 'heif' in m)
    if heic_count > 0 and not HEIF_AVAILABLE:
        print(f"\n⚠️  WARNING: Found {heic_count} HEIC/HEIF files but pillow-heif is not installed.")
        print("   HEIC files will fail to convert. Install with: pip install pillow-heif")
    
    if not IMAGEIO_AVAILABLE:
        print(f"\n⚠️  INFO: imageio not installed (optional fallback converter).")
        print("   Some exotic/corrupted formats may fail. Install with: pip install imageio")
    
    print("-" * 80)
    
    # Separate files
    already_target = []
    to_convert = []
    
    target_mime = 'image/jpeg' if format_type == 'JPEG' else 'image/png'
    target_ext_lower = ext.lower()
    
    for file_path, mime_type in image_files:
        if mime_type == target_mime and file_path.suffix.lower() in [target_ext_lower, '.jpeg' if format_type == 'JPEG' else None]:
            already_target.append((file_path, mime_type))
        else:
            to_convert.append((file_path, mime_type))
    
    print(f"\nAlready {format_type}: {len(already_target)} files (will skip)")
    print(f"To convert: {len(to_convert)} files")
    
    if not to_convert:
        print(f"\nℹ️  All image files are already in {format_type} format!")
        return
    
    # Show breakdown by format
    format_counts = defaultdict(int)
    for file_path, mime_type in to_convert:
        format_counts[mime_type] += 1
    
    print("\nFormats to convert:")
    for mime_type, count in sorted(format_counts.items(), key=lambda x: -x[1]):
        print(f"  {mime_type:<30} {count:>6} files")
    
    print("-" * 80)
    
    if dry_run:
        print("\nℹ️  This was a dry run. No files were converted.")
        print("   Run with --convert flag to actually convert files.")
        return
    
    # Convert files
    print(f"\n⚠️  Converting images to {format_type}...")
    converted = []
    skipped = []
    errors = []
    
    progress_bar = tqdm(to_convert, desc="Converting", unit="file")
    for file_path, mime_type in progress_bar:
        # Generate output path (same location, new extension)
        output_path = file_path.with_suffix(ext)
        
        # If output already exists and is different from input, skip
        if output_path.exists() and output_path != file_path:
            skipped.append((file_path, "output already exists"))
            if verbose:
                tqdm.write(f"  [SKIP] {file_path.name} - output exists")
            continue
        
        # If input and output are same (shouldn't happen but check anyway)
        if output_path == file_path:
            skipped.append((file_path, f"already {ext}"))
            continue
        
        # Convert
        success, error = convert_image(file_path, output_path, format_type, quality, verbose)
        
        if success:
            converted.append((file_path, output_path))
            if verbose:
                tqdm.write(f"  ✓ Converted: {file_path.name} → {output_path.name}")
            
            # Delete original if requested
            if delete_original:
                try:
                    file_path.unlink()
                    if verbose:
                        tqdm.write(f"    Deleted original: {file_path.name}")
                except Exception as e:
                    if verbose:
                        tqdm.write(f"    Warning: Could not delete original: {e}")
        else:
            errors.append((file_path, error))
            if verbose:
                tqdm.write(f"  ✗ Error: {file_path.name} - {error}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✓ Successfully converted: {len(converted)} files")
    print(f"⊘ Skipped: {len(skipped)} files")
    print(f"✗ Errors: {len(errors)} files")
    
    if errors and verbose:
        print("\nErrors:")
        for file_path, error in errors[:10]:
            print(f"  {file_path.name}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert all image files to uniform format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script converts all image files to a uniform format using Pillow.

Target formats:
  - JPEG: Lossy compression, smaller files, good for photos (default)
  - PNG: Lossless compression, larger files, supports transparency

Default: JPEG at 95%% quality
Metadata: EXIF data preserved for JPEG images

Supported input formats:
  - Common: JPEG, PNG, GIF, BMP, TIFF, WebP, ICO
  - Apple: HEIC, HEIF (requires pillow-heif)
  - Vector: SVG (requires cairosvg)
  - Advanced: TGA, PSD, DDS, JP2, RAW formats
  - Any format Pillow or imageio supports

Dependencies for special formats:
  - HEIC/HEIF: pip install pillow-heif
  - SVG: pip install cairosvg
  - Fallback converter: pip install imageio

Note: Script handles corrupted/truncated files gracefully

Examples:
  # Dry run (default) - see what would be converted
  python convert_images.py /path/to/directory
  
  # Actually convert files to JPEG
  python convert_images.py /path/to/directory --convert
  
  # Convert to PNG (lossless)
  python convert_images.py /path/to/directory --convert --format PNG
  
  # Convert and delete originals
  python convert_images.py /path/to/directory --convert --delete-original
  
  # Maximum JPEG quality
  python convert_images.py /path/to/directory --convert --quality 100
  
  # Lower quality for smaller files
  python convert_images.py /path/to/directory --convert --quality 85
  
  # Show detailed output
  python convert_images.py /path/to/directory --convert --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--convert', action='store_true',
                       help='Actually convert files (default is dry-run)')
    parser.add_argument('--format', default='JPEG', choices=['JPEG', 'PNG'],
                       help='Target format (default: JPEG)')
    parser.add_argument('--quality', type=int, default=95,
                       help='JPEG quality 1-100 (default: 95, ignored for PNG)')
    parser.add_argument('--delete-original', action='store_true',
                       help='Delete original files after successful conversion')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file')
    
    args = parser.parse_args()
    
    # Validate quality
    if args.quality < 1 or args.quality > 100:
        print("Error: --quality must be between 1 and 100", file=sys.stderr)
        sys.exit(1)
    
    # Confirm if not dry run
    if args.convert:
        print(f"\n⚠️  WARNING: This will convert all image files to {args.format}!")
        print(f"   Directory: {args.directory}")
        if args.format == 'JPEG':
            print(f"   Quality: {args.quality}%")
        if args.delete_original:
            print("   ⚠️  ORIGINALS WILL BE DELETED after conversion!")
        else:
            print("   Originals will be kept (you'll have both files)")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Scan and convert
    scan_and_convert_images(
        args.directory,
        format_type=args.format,
        quality=args.quality,
        delete_original=args.delete_original,
        dry_run=not args.convert,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
