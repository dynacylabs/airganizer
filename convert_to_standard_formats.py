#!/usr/bin/env python3
"""
Script to convert files to standard formats based on mime type.
Target formats: PDF, MP3, JPEG, MP4
Logs unconvertible files for later review and deletion.
"""

import os
import sys
import argparse
import logging
import magic
from pathlib import Path
from datetime import datetime
import subprocess
import shutil

# Conversion mappings by category
CONVERSION_MAP = {
    # Images -> JPEG
    'image/jpeg': 'already_standard',  # Already JPEG
    'image/png': 'jpeg',
    'image/x-tga': 'jpeg',
    'image/bmp': 'jpeg',
    'image/gif': 'jpeg',
    'image/tiff': 'jpeg',
    'image/wmf': 'jpeg',
    'image/x-pict': 'jpeg',
    'image/jxl': 'jpeg',
    'image/svg+xml': 'jpeg',  # Rasterize SVG to JPEG
    'image/vnd.microsoft.icon': 'jpeg',
    'image/x-xcf': 'jpeg',  # GIMP format
    'image/g3fax': 'jpeg',  # Fax images
    
    # Documents -> PDF
    'application/pdf': 'already_standard',  # Already PDF
    'application/msword': 'pdf',  # .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'pdf',  # .docx
    'application/vnd.ms-powerpoint': 'pdf',  # .ppt
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pdf',  # .pptx
    'application/vnd.ms-excel': 'pdf',  # .xls
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'pdf',  # .xlsx
    'application/vnd.oasis.opendocument.text': 'pdf',  # .odt
    'text/rtf': 'pdf',
    'text/html': 'pdf',
    'text/plain': 'pdf',
    'text/xml': 'pdf',
    'text/csv': 'pdf',
    
    # Audio -> MP3
    'audio/mpeg': 'already_standard',  # Already MP3
    'audio/ogg': 'mp3',
    'audio/x-m4a': 'mp3',
    'audio/x-mp4a-latm': 'mp3',
    'audio/x-hx-aac-adts': 'mp3',
    
    # Video -> MP4
    'video/mp4': 'already_standard',  # Already MP4
    'video/quicktime': 'mp4',  # .mov
    'video/x-m4v': 'mp4',
    'video/x-ms-asf': 'mp4',  # .asf/.wmv
    'video/x-ms-wmv': 'mp4',
    'video/x-msvideo': 'mp4',  # .avi
    'video/mpeg': 'mp4',
    'video/mpeg4-generic': 'mp4',
    'video/x-flv': 'mp4',
    'video/x-matroska': 'mp4',  # .mkv
    'video/3gpp': 'mp4',
}

# Files that cannot be converted to standard formats
UNCONVERTIBLE_TYPES = [
    'application/json',
    'application/gzip',
    'application/octet-stream',
    'application/onenote',
    'application/vnd.ms-office',  # Legacy Office format
    'error/unknown',
    'message/rfc822',  # Email files
    'text/x-c',
    'text/x-c++',
    'text/x-java',
    'application/javascript',
    'application/vnd.sqlite3',
    'application/x-appleworks3',
    'application/x-dbt',
    'application/vnd.hp-HPGL',  # CAD plotting files
    'audio/midi',
    'audio/x-syx',  # MIDI SysEx
    'image/x-atari-degas',  # Old Atari format
    'image/x-award-bioslogo',  # BIOS logos
    'image/vnd.dwg',  # CAD files
    'application/x-matlab-data',  # MATLAB proprietary
]


def setup_logging(log_file):
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def check_dependencies():
    """Check if required conversion tools are installed."""
    dependencies = {
        'ffmpeg': ['ffmpeg', '-version'],
        'imagemagick': ['convert', '-version'],
        'libreoffice': ['libreoffice', '--version'],
    }
    
    missing = []
    for name, cmd in dependencies.items():
        if not shutil.which(cmd[0]):
            missing.append(name)
    
    return missing


def convert_image_to_jpeg(input_path, output_path):
    """Convert image to JPEG using ImageMagick."""
    # Try magick command first (ImageMagick v7), fall back to convert (v6)
    commands = [['magick', input_path, '-quality', '95', output_path],
                ['convert', input_path, '-quality', '95', output_path]]
    
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return True
        except subprocess.CalledProcessError as e:
            # Check if it's a real image error or just wrong command
            if 'improper image header' in e.stderr or 'corrupt image' in e.stderr:
                logging.error(f"Image file is corrupted or not a valid image: {input_path}")
                return False
            # Try next command
            continue
        except subprocess.TimeoutExpired:
            logging.error(f"Image conversion timeout for {input_path}")
            return False
        except FileNotFoundError:
            # Try next command
            continue
        except Exception as e:
            logging.error(f"Image conversion error for {input_path}: {e}")
            return False
    
    logging.error(f"ImageMagick not found. Install ImageMagick.")
    return False


def get_libreoffice_command():
    """Find LibreOffice command on the system."""
    # Check standard commands first
    if shutil.which('libreoffice'):
        return 'libreoffice'
    if shutil.which('soffice'):
        return 'soffice'
    
    # Check macOS application bundle
    macos_paths = [
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
        '/Applications/LibreOffice.app/Contents/MacOS/libreoffice',
        os.path.expanduser('~/Applications/LibreOffice.app/Contents/MacOS/soffice')
    ]
    
    for path in macos_paths:
        if os.path.exists(path):
            return path
    
    return None


def convert_document_to_pdf(input_path, output_dir):
    """Convert document to PDF using LibreOffice."""
    # Get LibreOffice command
    libreoffice_cmd = get_libreoffice_command()
    
    if not libreoffice_cmd:
        logging.debug(f"LibreOffice not found, skipping {input_path}")
        return False
    
    try:
        result = subprocess.run(
            [libreoffice_cmd, '--headless', '--convert-to', 'pdf', '--outdir', output_dir, input_path],
            check=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Document conversion failed for {input_path}: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logging.error(f"Document conversion timed out for {input_path}")
        return False
    except FileNotFoundError:
        logging.error(f"LibreOffice command not executable: {libreoffice_cmd}")
        return False
    except Exception as e:
        logging.error(f"Document conversion error for {input_path}: {e}")
        return False


def convert_text_to_pdf(input_path, output_path):
    """Convert text/HTML to PDF using wkhtmltopdf or similar."""
    # For HTML files
    if input_path.lower().endswith(('.html', '.htm', '.xml')):
        try:
            subprocess.run(
                ['wkhtmltopdf', input_path, output_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to LibreOffice if wkhtmltopdf not available
            return convert_document_to_pdf(input_path, os.path.dirname(output_path))
    
    # For plain text, use LibreOffice or similar
    return convert_document_to_pdf(input_path, os.path.dirname(output_path))


def convert_audio_to_mp3(input_path, output_path):
    """Convert audio to MP3 using ffmpeg."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', input_path, '-codec:a', 'libmp3lame', '-qscale:a', '2', output_path, '-y'],
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Audio conversion failed for {input_path}: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logging.error(f"Audio conversion timeout for {input_path}")
        return False
    except FileNotFoundError:
        logging.error(f"ffmpeg not found. Install ffmpeg.")
        return False
    except Exception as e:
        logging.error(f"Audio conversion error for {input_path}: {e}")
        return False


def convert_video_to_mp4(input_path, output_path):
    """Convert video to MP4 using ffmpeg."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', input_path, '-codec:v', 'libx264', '-codec:a', 'aac', 
             '-strict', 'experimental', '-b:a', '192k', output_path, '-y'],
            check=True,
            capture_output=True,
            text=True,
            timeout=600
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Video conversion failed for {input_path}: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logging.error(f"Video conversion timeout for {input_path}")
        return False
    except FileNotFoundError:
        logging.error(f"ffmpeg not found. Install ffmpeg.")
        return False
    except Exception as e:
        logging.error(f"Video conversion error for {input_path}: {e}")
        return False


def convert_file(file_path, mime_type):
    """Convert a file to its target standard format in place."""
    target_format = CONVERSION_MAP.get(mime_type)
    
    if not target_format:
        return None, "not_in_conversion_map"
    
    if target_format == 'already_standard':
        return None, "already_standard"
    
    # Create output filename in the same directory
    file_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if target_format == 'jpeg':
        output_path = os.path.join(file_dir, f"{base_name}.jpg")
        success = convert_image_to_jpeg(file_path, output_path)
    elif target_format == 'pdf':
        if mime_type in ['text/html', 'text/xml', 'text/plain']:
            output_path = os.path.join(file_dir, f"{base_name}.pdf")
            success = convert_text_to_pdf(file_path, output_path)
        else:
            output_path = os.path.join(file_dir, f"{base_name}.pdf")
            success = convert_document_to_pdf(file_path, file_dir)
    elif target_format == 'mp3':
        output_path = os.path.join(file_dir, f"{base_name}.mp3")
        success = convert_audio_to_mp3(file_path, output_path)
    elif target_format == 'mp4':
        output_path = os.path.join(file_dir, f"{base_name}.mp4")
        success = convert_video_to_mp4(file_path, output_path)
    else:
        return None, f"unknown_target_format: {target_format}"
    
    if success:
        # Delete the original file after successful conversion
        try:
            os.remove(file_path)
            logging.info(f"Converted and replaced: {file_path} -> {output_path}")
        except Exception as e:
            logging.warning(f"Could not delete original {file_path}: {e}")
        return output_path, "converted"
    else:
        return None, "conversion_failed"


def scan_and_convert(directory, unconvertible_log, dry_run=False):
    """Scan directory and convert files to standard formats in place."""
    mime = magic.Magic(mime=True)
    
    # System directories and patterns to skip
    SKIP_DIRS = {
        '.fseventsd',
        '.Spotlight-V100',
        '.Trashes',
        '.TemporaryItems',
        '.DocumentRevisions-V100',
        '__pycache__',
        'node_modules',
        '.git',
        '.svn',
        'AppData'  # Windows user data - often contains fake file extensions
    }
    
    # File patterns to skip (Windows registry transaction files disguised as images)
    SKIP_PATTERNS = [
        'UsrClass.dat',
        '.TMContainer',
        '.TM.tga',
        '.regtrans-ms'
    ]
    
    stats = {
        'total': 0,
        'already_standard': 0,
        'converted': 0,
        'conversion_failed': 0,
        'unconvertible': 0,
        'errors': 0,
        'skipped_system': 0
    }
    
    unconvertible_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip system directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        # Skip files matching system file patterns
        files = [f for f in files if not any(pattern in f for pattern in SKIP_PATTERNS)]
        for file in files:
            file_path = os.path.join(root, file)
            stats['total'] += 1
            
            try:
                mime_type = mime.from_file(file_path)
                
                # Check if unconvertible
                if mime_type in UNCONVERTIBLE_TYPES:
                    unconvertible_files.append((file_path, mime_type))
                    stats['unconvertible'] += 1
                    logging.info(f"Unconvertible: {file_path} ({mime_type})")
                    continue
                
                # Check if convertible
                if mime_type in CONVERSION_MAP:
                    target = CONVERSION_MAP[mime_type]
                    
                    if target == 'already_standard':
                        stats['already_standard'] += 1
                        logging.debug(f"Already standard: {file_path} ({mime_type})")
                    else:
                        if dry_run:
                            logging.info(f"[DRY RUN] Would convert: {file_path} ({mime_type}) -> {target.upper()}")
                            stats['converted'] += 1
                        else:
                            output_path, status = convert_file(file_path, mime_type)
                            
                            if status == "converted":
                                stats['converted'] += 1
                            elif status == "conversion_failed":
                                logging.error(f"Conversion failed: {file_path}")
                                stats['conversion_failed'] += 1
                                unconvertible_files.append((file_path, f"{mime_type} (conversion failed)"))
                else:
                    # Not in conversion map
                    unconvertible_files.append((file_path, mime_type))
                    stats['unconvertible'] += 1
                    logging.warning(f"Unknown mime type: {file_path} ({mime_type})")
                    
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                stats['errors'] += 1
                unconvertible_files.append((file_path, f"error: {e}"))
    
    # Write unconvertible files log
    with open(unconvertible_log, 'w') as f:
        f.write(f"# Unconvertible Files Log\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Total unconvertible: {len(unconvertible_files)}\n")
        f.write(f"#\n")
        f.write(f"# Format: file_path | mime_type\n")
        f.write(f"#" + "="*78 + "\n\n")
        
        for file_path, mime_type in unconvertible_files:
            f.write(f"{file_path} | {mime_type}\n")
    
    return stats, unconvertible_files


def main():
    parser = argparse.ArgumentParser(
        description="Convert files to standard formats (PDF, MP3, JPEG, MP4) in place based on mime type.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be converted
  python convert_to_standard_formats.py /path/to/files --dry-run

  # Actually convert files in place (replaces original files)
  python convert_to_standard_formats.py /path/to/files
        """
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to scan for files to convert"
    )
    parser.add_argument(
        "--unconvertible-log",
        type=str,
        default="unconvertible_files.log",
        help="Log file for unconvertible files (default: unconvertible_files.log)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be converted without actually converting"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = f"conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(log_file)
    
    # Validate directory
    if not os.path.exists(args.directory):
        logging.error(f"Directory '{args.directory}' does not exist.")
        return 1
    
    if not os.path.isdir(args.directory):
        logging.error(f"'{args.directory}' is not a directory.")
        return 1
    
    # Check dependencies
    if not args.dry_run:
        missing_deps = check_dependencies()
        if missing_deps:
            logging.warning(f"Missing dependencies: {', '.join(missing_deps)}")
            logging.warning("Some conversions may fail. Install missing tools for full functionality.")
    
    logging.info(f"{'[DRY RUN] ' if args.dry_run else ''}Starting in-place conversion scan...")
    logging.info(f"Directory: {args.directory}")
    logging.info(f"Unconvertible log: {args.unconvertible_log}")
    logging.info("WARNING: Original files will be replaced with converted versions!")
    logging.info("=" * 80)
    
    # Scan and convert
    stats, unconvertible_files = scan_and_convert(
        args.directory,
        args.unconvertible_log,
        args.dry_run
    )
    
    # Print summary
    logging.info("=" * 80)
    logging.info("Conversion Summary:")
    logging.info(f"  Total files scanned: {stats['total']}")
    logging.info(f"  Already in standard format: {stats['already_standard']}")
    logging.info(f"  Successfully converted: {stats['converted']}")
    logging.info(f"  Conversion failed: {stats['conversion_failed']}")
    logging.info(f"  Unconvertible files: {stats['unconvertible']}")
    logging.info(f"  Errors: {stats['errors']}")
    logging.info(f"\nUnconvertible files logged to: {args.unconvertible_log}")
    logging.info(f"Full log saved to: {log_file}")
    
    if args.dry_run:
        logging.info("\nThis was a dry run. Run without --dry-run to actually convert files.")
    
    return 0


if __name__ == "__main__":
    exit(main())
