#!/usr/bin/env python3
"""
Script to delete text/plain files categorized as garbage (system, log, empty).
Uses same categorization logic as analyze_text_files.py.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm


def get_enhanced_mime_type(file_path, mime_detector):
    """Get MIME type using python-magic."""
    try:
        return mime_detector.from_file(str(file_path))
    except Exception:
        return 'error/unknown'


def analyze_text_file(file_path):
    """
    Analyze a text file to determine if it's worth keeping.
    Same logic as analyze_text_files.py.
    
    Returns: (category, confidence, reason)
    """
    try:
        stat = file_path.stat()
        file_size = stat.st_size
        file_name = file_path.name.lower()
        
        # Empty or near-empty files
        if file_size == 0:
            return 'empty', 1.0, 'File is empty'
        if file_size < 10:
            return 'empty', 0.9, 'File is nearly empty (< 10 bytes)'
        
        # Check file name patterns first (fast)
        # Log files
        if any(pattern in file_name for pattern in ['.log', 'log.', '_log', 'debug', 'error', 'trace', 'crash']):
            return 'log', 0.9, 'Filename indicates log file'
        
        # System/temporary files
        if any(pattern in file_name for pattern in ['.tmp', '.temp', '.cache', '.bak', '~', '.swp', '.swo']):
            return 'system', 0.9, 'Temporary/backup file'
        
        # Configuration files
        if any(ext in file_name for ext in ['.conf', '.cfg', '.ini', '.properties', '.env', 'config', 'settings']):
            return 'config', 0.8, 'Configuration file'
        
        # Code files (might be misidentified as text/plain)
        code_extensions = ['.py', '.js', '.java', '.c', '.cpp', '.h', '.sh', '.bash', '.sql', '.r', '.m']
        if any(file_name.endswith(ext) for ext in code_extensions):
            return 'code', 0.9, 'Code file'
        
        # Common document files
        if any(name in file_name for name in ['readme', 'todo', 'notes', 'license', 'changelog', 'authors']):
            return 'document', 0.8, 'Common document name'
        
        # Check file location (directory structure)
        path_parts = [p.lower() for p in file_path.parts]
        
        # System directories (likely garbage)
        garbage_dirs = [
            'log', 'logs', 'cache', 'temp', 'tmp', '.git', '.svn', 
            'node_modules', '__pycache__', '.metadata', '.settings',
            'backup', 'backups', '.trash', '.spotlight-v100', '.fseventsd'
        ]
        if any(d in path_parts for d in garbage_dirs):
            return 'system', 0.8, 'Located in system/cache directory'
        
        # Only read content if file is reasonably small (< 1MB)
        if file_size > 1_000_000:
            return 'data', 0.6, 'Large file (> 1MB), likely log or data'
        
        # Read a sample of the file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(min(10000, file_size))
                lines = sample.split('\n')[:100]
                
                if not lines or not sample.strip():
                    return 'empty', 0.9, 'Content is empty/whitespace'
                
                # Count lines with timestamps (log indicator)
                timestamp_patterns = [
                    r'\d{4}-\d{2}-\d{2}',
                    r'\d{2}/\d{2}/\d{4}',
                    r'\d{2}:\d{2}:\d{2}',
                    r'\[\d+\]',
                ]
                timestamp_lines = sum(1 for line in lines if any(re.search(p, line) for p in timestamp_patterns))
                timestamp_ratio = timestamp_lines / len(lines) if lines else 0
                
                if timestamp_ratio > 0.5:
                    return 'log', 0.9, f'{int(timestamp_ratio*100)}% lines have timestamps'
                
                # Check for repetitive content
                if len(lines) > 10:
                    unique_lines = len(set(lines))
                    repetition_ratio = 1 - (unique_lines / len(lines))
                    if repetition_ratio > 0.7:
                        return 'log', 0.8, f'{int(repetition_ratio*100)}% lines are repetitive'
                
                # Check for log level keywords
                log_keywords = ['ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE', 'FATAL', 'Exception', 'Stack trace']
                log_keyword_count = sum(1 for line in lines if any(kw in line for kw in log_keywords))
                if log_keyword_count > len(lines) * 0.3:
                    return 'log', 0.85, f'{int((log_keyword_count/len(lines))*100)}% lines have log keywords'
                
                # Other checks for code, data, documents...
                return 'unknown', 0.5, 'No clear pattern detected'
                
        except Exception:
            return 'unknown', 0.3, 'Could not read content'
            
    except Exception:
        return 'unknown', 0.2, 'Error analyzing file'


def delete_garbage_text_files(directory_path, categories_to_delete, dry_run=True, verbose=False):
    """
    Scan directory and delete text/plain files in specified categories.
    """
    mime_detector = magic.Magic(mime=True)
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print(f"Categories to delete: {', '.join(categories_to_delete)}")
    if dry_run:
        print("DRY RUN MODE - No files will be deleted")
    else:
        print("⚠️  DELETE MODE - Files will be permanently removed!")
    
    print("\nCounting files...")
    
    # Collect all files
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    
    print(f"Found {len(all_files)} total files")
    print("Identifying text/plain files...")
    
    # Filter text/plain files
    text_files = []
    for file_path in tqdm(all_files, desc="Checking MIME types", unit="file"):
        mime_type = get_enhanced_mime_type(file_path, mime_detector)
        if mime_type == 'text/plain':
            text_files.append(file_path)
    
    print(f"\nFound {len(text_files)} text/plain files")
    print("Analyzing and filtering...")
    
    # Analyze and filter files to delete
    to_delete = []
    category_counts = defaultdict(int)
    category_sizes = defaultdict(int)
    skipped_missing = 0
    
    for file_path in tqdm(text_files, desc="Analyzing", unit="file"):
        try:
            # Check if file still exists (might have been deleted by system)
            if not file_path.exists():
                skipped_missing += 1
                continue
            
            category, confidence, reason = analyze_text_file(file_path)
            file_size = file_path.stat().st_size
            
            category_counts[category] += 1
            category_sizes[category] += file_size
            
            if category in categories_to_delete:
                to_delete.append({
                    'path': file_path,
                    'category': category,
                    'size': file_size,
                    'confidence': confidence,
                    'reason': reason
                })
        except (FileNotFoundError, PermissionError) as e:
            # File was deleted or inaccessible between scans
            skipped_missing += 1
            continue
    
    # Print summary
    print("\n" + "=" * 80)
    print("DELETION SUMMARY")
    print("=" * 80)
    
    total_delete_size = sum(item['size'] for item in to_delete)
    
    print(f"\nTotal text files found: {len(text_files)}")
    if skipped_missing > 0:
        print(f"Files no longer accessible: {skipped_missing}")
    print(f"Files to delete: {len(to_delete)} ({total_delete_size / (1024*1024):.1f} MB)")
    
    print("\nBreakdown by category:")
    for category in categories_to_delete:
        count = category_counts[category]
        size = category_sizes[category]
        print(f"  {category:<10} {count:>6} files ({size / (1024*1024):>8.1f} MB)")
    
    print("-" * 80)
    
    if not to_delete:
        print("\nℹ️  No files to delete!")
        return
    
    if dry_run:
        print("\nℹ️  This was a dry run. No files were deleted.")
        print("   Run with --delete flag to actually delete files.")
        
        if verbose:
            print("\nExample files that would be deleted:")
            for item in to_delete[:10]:
                rel_path = item['path'].relative_to(root_path)
                print(f"  [{item['category']}] {rel_path}")
                print(f"    → {item['reason']}")
        return
    
    # Actually delete files
    print(f"\n⚠️  Deleting {len(to_delete)} files...")
    deleted = []
    errors = []
    
    progress_bar = tqdm(to_delete, desc="Deleting", unit="file")
    for item in progress_bar:
        file_path = item['path']
        try:
            # Check if file still exists before trying to delete
            if not file_path.exists():
                if verbose:
                    tqdm.write(f"  - Skipped: {file_path.name} (already deleted)")
                continue
                
            file_path.unlink()
            deleted.append(file_path)
            if verbose:
                tqdm.write(f"  ✓ Deleted: {file_path.name} [{item['category']}]")
        except FileNotFoundError:
            # File was already deleted
            if verbose:
                tqdm.write(f"  - Skipped: {file_path.name} (already deleted)")
        except Exception as e:
            errors.append((file_path, str(e)))
            if verbose:
                tqdm.write(f"  ✗ Error: {file_path.name} - {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\n✓ Successfully deleted: {len(deleted)} files")
    print(f"✗ Errors: {len(errors)} files")
    
    if errors:
        print("\nErrors:")
        for file_path, error in errors[:10]:
            print(f"  {file_path.name}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Delete text/plain files categorized as garbage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script deletes text/plain files based on their category.

Default categories to delete: system, log, empty
Safe categories (never deleted): code, config, document
Review categories (optional): data, unknown

Examples:
  # Dry run - see what would be deleted (default: system, log, empty)
  python delete_garbage_text_files.py /path/to/directory
  
  # Actually delete garbage files
  python delete_garbage_text_files.py /path/to/directory --delete
  
  # Delete system and log files only
  python delete_garbage_text_files.py /path/to/directory --categories system log --delete
  
  # Also delete unknown files
  python delete_garbage_text_files.py /path/to/directory --categories system log empty unknown --delete
  
  # Verbose output
  python delete_garbage_text_files.py /path/to/directory --delete --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--delete', action='store_true',
                       help='Actually delete files (default is dry-run)')
    parser.add_argument('--categories', nargs='+', 
                       default=['system', 'log', 'empty'],
                       choices=['system', 'log', 'empty', 'data', 'unknown', 'code', 'config', 'document'],
                       help='Categories to delete (default: system log empty)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file')
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if args.delete:
        print(f"\n⚠️  WARNING: This will permanently delete text files!")
        print(f"   Directory: {args.directory}")
        print(f"   Categories: {', '.join(args.categories)}")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Delete files
    delete_garbage_text_files(
        args.directory,
        categories_to_delete=args.categories,
        dry_run=not args.delete,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
