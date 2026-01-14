#!/usr/bin/env python3
"""
Script to analyze and categorize text/plain files to identify which are worth keeping.
Helps identify logs, configs, code, documentation vs garbage.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
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
    
    Returns: (category, confidence, reason)
    Categories: 'log', 'config', 'code', 'document', 'data', 'system', 'empty', 'unknown'
    Confidence: 0.0 to 1.0
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
            'backup', 'backups', '.trash', '.spotlight-v100'
        ]
        if any(d in path_parts for d in garbage_dirs):
            return 'system', 0.8, 'Located in system/cache directory'
        
        # Only read content if file is reasonably small (< 1MB)
        if file_size > 1_000_000:
            # Large text files are often logs or data dumps
            return 'data', 0.6, 'Large file (> 1MB), likely log or data'
        
        # Read a sample of the file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 10KB or whole file if smaller
                sample = f.read(min(10000, file_size))
                lines = sample.split('\n')[:100]  # First 100 lines max
                
                if not lines or not sample.strip():
                    return 'empty', 0.9, 'Content is empty/whitespace'
                
                # Count lines with timestamps (log indicator)
                timestamp_patterns = [
                    r'\d{4}-\d{2}-\d{2}',  # 2024-01-14
                    r'\d{2}/\d{2}/\d{4}',  # 01/14/2024
                    r'\d{2}:\d{2}:\d{2}',  # 12:34:56
                    r'\[\d+\]',             # [123456]
                ]
                timestamp_lines = sum(1 for line in lines if any(re.search(p, line) for p in timestamp_patterns))
                timestamp_ratio = timestamp_lines / len(lines) if lines else 0
                
                # High timestamp ratio = likely log
                if timestamp_ratio > 0.5:
                    return 'log', 0.9, f'{int(timestamp_ratio*100)}% lines have timestamps'
                
                # Check for repetitive content (logs often repeat patterns)
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
                
                # Check for code patterns
                code_patterns = [
                    r'^\s*def\s+\w+',          # Python function
                    r'^\s*function\s+\w+',     # JavaScript function
                    r'^\s*class\s+\w+',        # Class definition
                    r'^\s*public\s+\w+',       # Java/C++
                    r'^\s*if\s*\(',            # If statement
                    r'^\s*for\s*\(',           # For loop
                    r'^\s*import\s+',          # Import statement
                    r'^\s*#include\s+',        # C/C++ include
                ]
                code_lines = sum(1 for line in lines if any(re.search(p, line) for p in code_patterns))
                if code_lines > len(lines) * 0.2:
                    return 'code', 0.8, f'{int((code_lines/len(lines))*100)}% lines look like code'
                
                # Check for structured data (JSON, XML, CSV)
                if sample.strip().startswith('{') or sample.strip().startswith('['):
                    return 'data', 0.7, 'Looks like JSON data'
                if sample.strip().startswith('<') and '>' in sample:
                    return 'data', 0.7, 'Looks like XML/HTML data'
                if ',' in sample and len(lines) > 5:
                    comma_lines = sum(1 for line in lines if ',' in line)
                    if comma_lines > len(lines) * 0.8:
                        return 'data', 0.7, 'Looks like CSV data'
                
                # Check for natural language (sentences, paragraphs)
                # Count lines with sentence-ending punctuation
                sentence_pattern = r'[.!?]\s*$'
                sentence_lines = sum(1 for line in lines if re.search(sentence_pattern, line.strip()))
                
                # Check for paragraph breaks (empty lines)
                empty_lines = sum(1 for line in lines if not line.strip())
                
                # Check average word length (natural language: 4-6 chars)
                words = sample.split()
                if words:
                    avg_word_length = sum(len(w) for w in words) / len(words)
                    if 3 < avg_word_length < 8 and sentence_lines > 3:
                        return 'document', 0.75, 'Contains natural language text'
                
                # Check for configuration patterns
                config_patterns = [
                    r'^\s*\w+\s*=\s*',         # key = value
                    r'^\s*\[\w+\]',            # [section]
                    r'^\s*\w+:\s*\w+',         # key: value
                ]
                config_lines = sum(1 for line in lines if any(re.search(p, line) for p in config_patterns))
                if config_lines > len(lines) * 0.5:
                    return 'config', 0.75, f'{int((config_lines/len(lines))*100)}% lines are key-value pairs'
                
                # Default: unknown
                return 'unknown', 0.5, 'No clear pattern detected'
                
        except Exception as e:
            return 'unknown', 0.3, f'Could not read content: {e}'
            
    except Exception as e:
        return 'unknown', 0.2, f'Error analyzing file: {e}'


def scan_and_categorize_text_files(directory_path, show_examples=True, verbose=False):
    """
    Scan directory and categorize all text/plain files.
    """
    mime_detector = magic.Magic(mime=True)
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
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
    print("\nAnalyzing text files...")
    
    # Analyze each text file
    categories = defaultdict(list)
    category_sizes = defaultdict(int)
    
    for file_path in tqdm(text_files, desc="Analyzing", unit="file"):
        category, confidence, reason = analyze_text_file(file_path)
        file_size = file_path.stat().st_size
        
        categories[category].append({
            'path': file_path,
            'size': file_size,
            'confidence': confidence,
            'reason': reason
        })
        category_sizes[category] += file_size
    
    # Print results
    print("\n" + "=" * 100)
    print("TEXT FILE CATEGORIZATION")
    print("=" * 100)
    
    # Sort categories by count
    sorted_categories = sorted(categories.items(), key=lambda x: -len(x[1]))
    
    total_size = sum(category_sizes.values())
    
    for category, files in sorted_categories:
        count = len(files)
        size = category_sizes[category]
        size_mb = size / (1024 * 1024)
        percentage = (count / len(text_files)) * 100
        
        # Recommendation
        if category in ['log', 'system', 'empty']:
            recommendation = "❌ DELETE (garbage)"
        elif category in ['config', 'code', 'document']:
            recommendation = "✅ KEEP (important)"
        else:
            recommendation = "⚠️  REVIEW (uncertain)"
        
        print(f"\n{category.upper():<15} {count:>6} files ({percentage:>5.1f}%) {size_mb:>8.1f} MB  {recommendation}")
        
        # Show examples
        if show_examples and files:
            print(f"  Examples:")
            for item in files[:3]:
                rel_path = item['path'].relative_to(root_path)
                conf_pct = int(item['confidence'] * 100)
                print(f"    [{conf_pct}%] {rel_path}")
                if verbose:
                    print(f"         → {item['reason']}")
    
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    # Calculate recommendations
    delete_count = sum(len(files) for cat, files in categories.items() if cat in ['log', 'system', 'empty'])
    keep_count = sum(len(files) for cat, files in categories.items() if cat in ['config', 'code', 'document'])
    review_count = len(text_files) - delete_count - keep_count
    
    delete_size = sum(category_sizes[cat] for cat in ['log', 'system', 'empty'])
    keep_size = sum(category_sizes[cat] for cat in ['config', 'code', 'document'])
    review_size = total_size - delete_size - keep_size
    
    print(f"\n❌ Recommended to DELETE: {delete_count:>6} files ({delete_size/(1024*1024):>8.1f} MB)")
    print(f"✅ Recommended to KEEP:   {keep_count:>6} files ({keep_size/(1024*1024):>8.1f} MB)")
    print(f"⚠️  Needs REVIEW:          {review_count:>6} files ({review_size/(1024*1024):>8.1f} MB)")
    print(f"\nTotal:                   {len(text_files):>6} files ({total_size/(1024*1024):>8.1f} MB)")
    
    print("\n" + "=" * 100)
    print("\nNext steps:")
    print("  1. Review the categories above")
    print("  2. Use --category flag to see all files in a specific category")
    print("  3. Create deletion script based on categories you want to remove")
    print("=" * 100)
    
    return categories


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze text/plain files to identify which are worth keeping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script analyzes text/plain files and categorizes them:

Categories:
  - empty: Empty or nearly empty files (DELETE)
  - log: Log files with timestamps and repetitive content (DELETE)
  - system: Temporary, cache, backup files (DELETE)
  - config: Configuration files (KEEP)
  - code: Source code files (KEEP)
  - document: Documentation, README, notes (KEEP)
  - data: Structured data (JSON, XML, CSV) (REVIEW)
  - unknown: Unclear purpose (REVIEW)

Examples:
  # Analyze all text files
  python analyze_text_files.py /path/to/directory
  
  # Show detailed reasons
  python analyze_text_files.py /path/to/directory --verbose
  
  # Don't show examples
  python analyze_text_files.py /path/to/directory --no-examples
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--no-examples', action='store_true',
                       help='Don\'t show example files for each category')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed analysis reasons')
    
    args = parser.parse_args()
    
    # Scan and categorize
    scan_and_categorize_text_files(
        args.directory,
        show_examples=not args.no_examples,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
