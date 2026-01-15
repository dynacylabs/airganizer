#!/usr/bin/env python3
"""
Delete all files that are NOT in the 4 standard formats:
- image/jpeg (JPEG)
- application/pdf (PDF)
- video/mp4 (MP4)
- audio/mpeg (MP3)
"""

import os
import sys
import argparse
import logging
import magic
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Only keep these 4 formats
KEEP_FORMATS = {
    'image/jpeg',
    'application/pdf',
    'video/mp4',
    'audio/mpeg'
}


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


def delete_non_standard_files(directory, dry_run=False):
    """Delete all files that are not in the 4 standard formats."""
    mime = magic.Magic(mime=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'delete_non_standard_{timestamp}.log'
    setup_logging(log_file)
    
    stats = {
        'total_scanned': 0,
        'kept': 0,
        'deleted': 0,
        'errors': 0
    }
    
    files_by_type = defaultdict(int)
    deleted_by_type = defaultdict(int)
    
    logging.info(f"Scanning directory: {directory}")
    logging.info(f"Keeping only: {', '.join(sorted(KEEP_FORMATS))}")
    logging.info("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            stats['total_scanned'] += 1
            
            try:
                mime_type = mime.from_file(file_path)
                files_by_type[mime_type] += 1
                
                if mime_type in KEEP_FORMATS:
                    stats['kept'] += 1
                    logging.debug(f"Keeping: {file_path} ({mime_type})")
                else:
                    # Delete this file
                    if dry_run:
                        logging.info(f"[DRY RUN] Would delete: {file_path} ({mime_type})")
                        stats['deleted'] += 1
                        deleted_by_type[mime_type] += 1
                    else:
                        try:
                            os.remove(file_path)
                            stats['deleted'] += 1
                            deleted_by_type[mime_type] += 1
                            logging.info(f"Deleted: {file_path} ({mime_type})")
                        except Exception as e:
                            stats['errors'] += 1
                            logging.error(f"Error deleting {file_path}: {e}")
                
                # Progress update every 1000 files
                if stats['total_scanned'] % 1000 == 0:
                    logging.info(f"Progress: {stats['total_scanned']} files scanned, {stats['deleted']} deleted, {stats['kept']} kept")
                    
            except Exception as e:
                stats['errors'] += 1
                logging.error(f"Error processing {file_path}: {e}")
    
    # Print summary
    logging.info("=" * 80)
    logging.info("Summary:")
    logging.info(f"  Total files scanned: {stats['total_scanned']}")
    logging.info(f"  Files kept (standard formats): {stats['kept']}")
    logging.info(f"  Files deleted: {stats['deleted']}")
    logging.info(f"  Errors: {stats['errors']}")
    
    if deleted_by_type:
        logging.info("\nDeleted files by MIME type:")
        for mime_type in sorted(deleted_by_type.keys(), key=lambda x: deleted_by_type[x], reverse=True):
            count = deleted_by_type[mime_type]
            logging.info(f"  {mime_type}: {count}")
    
    logging.info(f"\nLog written to: {log_file}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Delete all files except PDF, JPEG, MP4, and MP3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script will delete EVERYTHING that is not one of these 4 formats:
  - image/jpeg (JPEG images)
  - application/pdf (PDF documents)
  - video/mp4 (MP4 videos)
  - audio/mpeg (MP3 audio)

Examples:
  # Dry run to see what would be deleted
  python delete_non_standard.py /Volumes/ssd --dry-run

  # Actually delete non-standard files
  python delete_non_standard.py /Volumes/ssd
        """
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        sys.exit(1)
    
    if not args.dry_run:
        print("WARNING: This will permanently delete all files that are not PDF/JPEG/MP4/MP3!")
        print(f"Directory: {args.directory}")
        response = input("Are you sure? Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    delete_non_standard_files(args.directory, args.dry_run)


if __name__ == '__main__':
    main()
