#!/usr/bin/env python3
"""
Script to convert all document files to PDF format.
Uses LibreOffice to convert Word, Excel, PowerPoint, RTF, ODT, and other formats.
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm


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
        
        # Documents - Microsoft Office
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.rtf': 'text/rtf',
        
        # Documents - OpenOffice/LibreOffice
        '.odt': 'application/vnd.oasis.opendocument.text',
        '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
        '.odp': 'application/vnd.oasis.opendocument.presentation',
        '.odg': 'application/vnd.oasis.opendocument.graphics',
        
        # Documents - Other
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        
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
        '.ico': 'image/vnd.microsoft.icon',
        '.svg': 'image/svg+xml',
        
        # Videos
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.m4v': 'video/x-m4v',
        
        # Audio
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/x-wav',
        '.m4a': 'audio/x-m4a',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac',
        '.wma': 'audio/x-ms-wma',
    }
    
    suffix = file_path.suffix.lower()
    return extension_map.get(suffix)


def identify_by_content_analysis(file_path):
    """
    Analyze file content for magic bytes and patterns.
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(512)
            
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
            
            # Videos
            elif header.startswith(b'RIFF') and b'AVI ' in header[:16]:
                return 'video/x-msvideo'
            
            # Audio files
            elif header.startswith(b'ID3') or (len(header) >= 2 and header[0:2] == b'\xff\xfb'):
                return 'audio/mpeg'
            elif header.startswith(b'OggS'):
                return 'audio/ogg'
            elif header.startswith(b'RIFF') and b'WAVE' in header[:16]:
                return 'audio/x-wav'
            elif header.startswith(b'fLaC'):
                return 'audio/flac'
                
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
        specific_type = identify_by_extension(file_path)
        if specific_type:
            return specific_type
    
    return mime_type


def check_libreoffice():
    """Check if LibreOffice is installed."""
    soffice_paths = ['soffice', 'libreoffice']
    for cmd in soffice_paths:
        if shutil.which(cmd):
            return cmd
    return None


def convert_document_to_pdf(input_path, output_path, verbose=False):
    """
    Convert document to PDF using LibreOffice.
    
    Args:
        input_path: Input document file
        output_path: Output PDF file
        verbose: Show detailed output
    
    Returns: (success, error_message)
    """
    soffice = check_libreoffice()
    if not soffice:
        return False, "LibreOffice not installed (required for document conversion)"
    
    try:
        # LibreOffice converts to output directory, not specific file
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run LibreOffice conversion
        cmd = [
            soffice,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(output_dir),
            str(input_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            return False, f"LibreOffice error: {result.stderr}"
        
        # LibreOffice creates filename based on input name
        expected_output = output_dir / f"{input_path.stem}.pdf"
        
        # If output filename differs, rename it
        if expected_output != output_path and expected_output.exists():
            if output_path.exists():
                output_path.unlink()
            expected_output.rename(output_path)
        
        if not output_path.exists():
            return False, "PDF file was not created"
        
        return True, None
        
    except subprocess.TimeoutExpired:
        return False, "Conversion timeout (> 5 minutes)"
    except Exception as e:
        return False, str(e)


def scan_and_convert_documents(directory_path, delete_original=False, dry_run=True, verbose=False):
    """
    Scan directory and convert all document files to PDF.
    """
    mime_detector = magic.Magic(mime=True)
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Check for LibreOffice
    soffice = check_libreoffice()
    if not soffice:
        print("ERROR: LibreOffice is not installed!", file=sys.stderr)
        print("Install LibreOffice to convert documents:", file=sys.stderr)
        print("  - Ubuntu/Debian: sudo apt install libreoffice", file=sys.stderr)
        print("  - macOS: brew install --cask libreoffice", file=sys.stderr)
        print("  - Windows: Download from https://www.libreoffice.org/", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print(f"Target format: PDF")
    print(f"Using: {soffice}")
    if dry_run:
        print("DRY RUN MODE - No files will be converted")
    else:
        print("⚠️  CONVERSION MODE - Files will be converted!")
    
    print("\nCounting files...")
    
    # Collect all files (same as scan_mime_types.py)
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    
    print(f"Found {len(all_files)} total files")
    
    # Document MIME types that can be converted to PDF
    convertible_mime_types = {
        # Microsoft Office
        'application/msword',  # .doc
        'application/vnd.ms-word',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-powerpoint',  # .ppt
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'application/vnd.ms-office',
        
        # OpenOffice/LibreOffice
        'application/vnd.oasis.opendocument.text',  # .odt
        'application/vnd.oasis.opendocument.spreadsheet',  # .ods
        'application/vnd.oasis.opendocument.presentation',  # .odp
        'application/vnd.oasis.opendocument.graphics',  # .odg
        
        # Rich Text
        'text/rtf',
        'application/rtf',
        
        # Plain text (optional - can convert but usually not needed)
        # 'text/plain',
    }
    
    # Filter document files - check MIME type for ALL files (same as scan_mime_types.py)
    print("Identifying document files...")
    document_files = []
    
    for file_path in tqdm(all_files, desc="Checking MIME types", unit="file"):
        mime_type = get_enhanced_mime_type(file_path, mime_detector)
        
        # Include if MIME type indicates convertible document
        if mime_type in convertible_mime_types:
            document_files.append((file_path, mime_type))
    
    print(f"\nFound {len(document_files)} document files to process")
    print("-" * 80)
    
    # Separate files
    already_pdf = []
    to_convert = []
    
    for file_path, mime_type in document_files:
        if mime_type == 'application/pdf':
            already_pdf.append((file_path, mime_type))
        else:
            to_convert.append((file_path, mime_type))
    
    print(f"\nTo convert: {len(to_convert)} files")
    
    if not to_convert:
        print(f"\nℹ️  No documents to convert!")
        return
    
    # Show breakdown by format
    format_counts = defaultdict(int)
    for file_path, mime_type in to_convert:
        format_counts[mime_type] += 1
    
    print("\nFormats to convert:")
    for mime_type, count in sorted(format_counts.items(), key=lambda x: -x[1]):
        print(f"  {mime_type:<70} {count:>6} files")
    
    print("-" * 80)
    
    if dry_run:
        print("\nℹ️  This was a dry run. No files were converted.")
        print("   Run with --convert flag to actually convert files.")
        return
    
    # Convert files
    print(f"\n⚠️  Converting documents to PDF...")
    converted = []
    skipped = []
    errors = []
    
    progress_bar = tqdm(to_convert, desc="Converting", unit="file")
    for file_path, mime_type in progress_bar:
        # Generate output path (same location, .pdf extension)
        output_path = file_path.with_suffix('.pdf')
        
        # If output already exists and is different from input, skip
        if output_path.exists() and output_path != file_path:
            skipped.append((file_path, "output already exists"))
            if verbose:
                tqdm.write(f"  [SKIP] {file_path.name} - PDF already exists")
            continue
        
        # Convert
        success, error = convert_document_to_pdf(file_path, output_path, verbose)
        
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
        description='Convert all document files to PDF format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script converts document files to PDF using LibreOffice.

Supported formats:
  - Microsoft Word: .doc, .docx
  - Microsoft Excel: .xls, .xlsx
  - Microsoft PowerPoint: .ppt, .pptx
  - Rich Text Format: .rtf
  - OpenDocument: .odt, .ods, .odp, .odg

Requirements:
  - LibreOffice must be installed (soffice command)
  - Install: apt install libreoffice (Linux) or brew install --cask libreoffice (macOS)

Examples:
  # Dry run (default) - see what would be converted
  python convert_documents.py /path/to/directory
  
  # Actually convert files to PDF
  python convert_documents.py /path/to/directory --convert
  
  # Convert and delete originals
  python convert_documents.py /path/to/directory --convert --delete-original
  
  # Show detailed output
  python convert_documents.py /path/to/directory --convert --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--convert', action='store_true',
                       help='Actually convert files (default is dry-run)')
    parser.add_argument('--delete-original', action='store_true',
                       help='Delete original files after successful conversion')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file')
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if args.convert:
        print(f"\n⚠️  WARNING: This will convert all documents to PDF!")
        print(f"   Directory: {args.directory}")
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
    scan_and_convert_documents(
        args.directory,
        delete_original=args.delete_original,
        dry_run=not args.convert,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
