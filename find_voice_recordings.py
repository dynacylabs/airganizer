#!/usr/bin/env python3
"""
Script to find voice recordings by deleting actual songs.
Analyzes audio files for musical characteristics and keeps only non-song recordings.
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("WARNING: librosa not installed. Install with: pip install librosa soundfile")
    print("Falling back to basic heuristics (duration and metadata only)\n")

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


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
            # Parse binwalk output for common signatures
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
            elif 'elf' in output or 'executable' in output:
                return 'application/x-executable'
            elif 'sqlite' in output:
                return 'application/vnd.sqlite3'
            elif 'certificate' in output or 'private key' in output:
                return 'application/x-pem-file'
            elif 'tar archive' in output:
                return 'application/x-tar'
            elif '7-zip' in output:
                return 'application/x-7z-compressed'
            elif 'rar archive' in output:
                return 'application/x-rar'
            
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
        '.ico': 'image/vnd.microsoft.icon',
        '.svg': 'image/svg+xml',
        '.tn': 'image/x-thumbnail',
        
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


def get_mime_type(file_path):
    """Get MIME type of file using enhanced detection."""
    mime_detector = magic.Magic(mime=True)
    return get_enhanced_mime_type(file_path, mime_detector)


def has_music_metadata(file_path):
    """Check if file has typical song metadata (artist, album, etc.)."""
    if not MUTAGEN_AVAILABLE:
        return False
    
    try:
        audio = MutagenFile(str(file_path))
        if audio is None:
            return False
        
        # Check for common music tags
        music_tags = ['artist', 'album', 'title', 'TPE1', 'TALB', 'TIT2', '©ART', '©alb', '©nam']
        
        for tag in music_tags:
            if tag in audio:
                return True
        
        # Check if it has structured metadata at all
        if audio.tags and len(audio.tags) > 2:
            return True
            
    except Exception:
        pass
    
    return False


def analyze_audio_advanced(file_path):
    """
    Advanced audio analysis using librosa.
    Returns: (is_song, confidence, reason)
    """
    import warnings
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    try:
        # Load audio (limit to first 30 seconds for speed - enough to detect patterns)
        y, sr = librosa.load(str(file_path), duration=30, sr=22050, mono=True)
        
        # Get actual duration from file metadata (faster than loading entire file)
        try:
            import soundfile as sf
            info = sf.info(str(file_path))
            duration = info.duration
        except:
            duration = librosa.get_duration(y=y, sr=sr)
        
        # 1. Duration check
        if duration < 30:
            return False, 0.9, f"very_short_{duration:.1f}s"
        
        # 2. Detect tempo and beat
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # 3. Beat consistency (songs have regular beats)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        beat_strength = np.mean(onset_env)
        beat_consistency = np.std(onset_env) / (np.mean(onset_env) + 1e-6)
        
        # 4. Harmonic/percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_ratio = np.sum(np.abs(y_harmonic)) / (np.sum(np.abs(y)) + 1e-6)
        
        # 5. Zero crossing rate (speech has higher ZCR)
        zcr = librosa.feature.zero_crossing_rate(y)
        mean_zcr = np.mean(zcr)
        
        # Song characteristics:
        # - Duration > 90 seconds (songs typically 2-7 minutes)
        # - Tempo between 60-180 BPM
        # - Strong harmonic content (> 0.35)
        # - Regular beat patterns (consistency < 1.0)
        # - Lower zero crossing rate (< 0.1 for music)
        
        reasons = []
        confidence = 0.0
        
        # Duration scoring
        if duration > 90:
            confidence += 0.25
            reasons.append(f"long_{duration:.0f}s")
        elif duration > 60:
            confidence += 0.1
            reasons.append(f"medium_{duration:.0f}s")
        
        # Tempo scoring
        if 60 <= tempo <= 180:
            confidence += 0.25
            reasons.append(f"tempo_{tempo:.0f}bpm")
        
        # Harmonic content scoring
        if harmonic_ratio > 0.35:
            confidence += 0.25
            reasons.append(f"harmonic_{harmonic_ratio:.2f}")
        
        # Beat consistency scoring
        if beat_consistency < 1.0 and beat_strength > 0.1:
            confidence += 0.15
            reasons.append(f"beat_consistent")
        
        # Zero crossing rate (speech typically has higher ZCR)
        if mean_zcr < 0.1:
            confidence += 0.1
            reasons.append("music_zcr")
        else:
            reasons.append(f"speech_zcr_{mean_zcr:.3f}")
        
        is_song = confidence > 0.5
        reason = "+".join(reasons)
        
        return is_song, confidence, reason
        
    except (RuntimeError, ValueError, OSError, IOError) as e:
        # File format errors, corruption, unsupported codecs
        # Fall back to basic analysis
        return None, 0.0, f"librosa_error"
    except Exception as e:
        return None, 0.0, f"error"


def analyze_audio_basic(file_path):
    """
    Basic audio analysis without librosa.
    Uses ONLY metadata - no file size or filename heuristics.
    Returns: (is_song, confidence, reason)
    """
    if not MUTAGEN_AVAILABLE:
        return None, 0.0, "no_mutagen"
    
    try:
        # Check metadata
        has_metadata = has_music_metadata(file_path)
        
        if has_metadata:
            # Has artist/album/title metadata = definitely a song
            return True, 0.9, "music_metadata"
        else:
            # No music metadata = likely a recording/voice memo
            return False, 0.7, "no_music_metadata"
        
    except Exception as e:
        # Can't read metadata - unknown
        return None, 0.0, f"metadata_read_error"


def scan_and_delete_songs(directory_path, dry_run=True, verbose=False):
    """
    Scan directory for audio files and delete songs (keeping voice recordings).
    """
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print(f"Analysis mode: {'Advanced (librosa)' if LIBROSA_AVAILABLE else 'Basic (duration/metadata only)'}")
    
    if dry_run:
        print("DRY RUN MODE - No files will be deleted\n")
    else:
        print("⚠️  DELETION MODE - Songs will be permanently deleted!\n")
    
    print("Strategy: Delete songs, KEEP voice recordings and sound effects\n")
    print("Counting files...")
    
    # Collect all files
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    
    # Filter audio files
    print("Identifying audio files...")
    audio_files = []
    for file_path in tqdm(all_files, desc="Checking MIME types", unit="file"):
        mime_type = get_mime_type(file_path)
        # Check if it's ANY audio file (starts with "audio/")
        if mime_type and mime_type.startswith('audio/'):
            audio_files.append(file_path)
    
    print(f"\nFound {len(audio_files)} audio files to analyze")
    print("-" * 80)
    
    # Analyze audio files
    songs_to_delete = []
    recordings_to_keep = []
    errors = []
    
    analyze_func = analyze_audio_advanced if LIBROSA_AVAILABLE else analyze_audio_basic
    
    progress_bar = tqdm(audio_files, desc="Analyzing audio", unit="file")
    for file_path in progress_bar:
        is_song, confidence, reason = analyze_func(file_path)
        
        if is_song is None:
            # Librosa failed, try metadata-only analysis
            is_song, confidence, reason = analyze_audio_basic(file_path)
            if is_song is not None:
                reason = f"metadata_{reason}"
            else:
                # Both failed - add to errors
                errors.append((file_path, reason))
                if verbose:
                    tqdm.write(f"  [ERROR] {file_path.name}: {reason}")
                continue
        
        if is_song:
            songs_to_delete.append((file_path, confidence, reason))
            if verbose:
                tqdm.write(f"  [SONG→DELETE] {file_path.name} (conf={confidence:.2f}, {reason})")
        else:
            recordings_to_keep.append((file_path, confidence, reason))
            if verbose:
                tqdm.write(f"  [RECORDING→KEEP] {file_path.name} (conf={confidence:.2f}, {reason})")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✗ SONGS to DELETE ({len(songs_to_delete)} files):")
    print("-" * 80)
    for file_path, confidence, reason in sorted(songs_to_delete, key=lambda x: -x[1]):
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  {str(file_path.relative_to(root_path)):<60} [{confidence:.2f}] {size_mb:.1f}MB")
        if verbose:
            print(f"    Reason: {reason}")
    
    print(f"\n✓ RECORDINGS to KEEP ({len(recordings_to_keep)} files):")
    print("-" * 80)
    for file_path, confidence, reason in sorted(recordings_to_keep, key=lambda x: x[1]):
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  {str(file_path.relative_to(root_path)):<60} [{confidence:.2f}] {size_mb:.1f}MB")
        if verbose:
            print(f"    Reason: {reason}")
    
    if errors:
        print(f"\n⚠️  ERRORS ({len(errors)} files):")
        print("-" * 80)
        for file_path, reason in errors:
            print(f"  {file_path.name}: {reason}")
    
    print("-" * 80)
    total_delete_size = sum(f[0].stat().st_size for f in songs_to_delete)
    total_keep_size = sum(f[0].stat().st_size for f in recordings_to_keep)
    print(f"  {'Songs to DELETE':<60} {len(songs_to_delete):>6} files ({format_size(total_delete_size)})")
    print(f"  {'Recordings to KEEP':<60} {len(recordings_to_keep):>6} files ({format_size(total_keep_size)})")
    print("=" * 80)
    
    # Perform deletion if not dry run
    if not dry_run and songs_to_delete:
        print("\n⚠️  Deleting songs...")
        deleted_count = 0
        
        progress_bar = tqdm(songs_to_delete, desc="Deleting songs", unit="file")
        for file_path, confidence, reason in progress_bar:
            try:
                file_path.unlink()
                deleted_count += 1
                if verbose:
                    tqdm.write(f"  ✓ Deleted: {file_path.name}")
            except Exception as e:
                tqdm.write(f"  ✗ Error deleting {file_path.name}: {e}")
        
        print(f"\n✓ Successfully deleted {deleted_count} of {len(songs_to_delete)} songs")
        print(f"✓ Kept {len(recordings_to_keep)} voice recordings and sound effects")
    elif not songs_to_delete:
        print("\nℹ️  No songs found to delete. All audio files appear to be recordings!")
    else:
        print("\nℹ️  This was a dry run. No files were deleted.")
        print("   Run with --delete flag to actually delete songs.")


def format_size(size_bytes):
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Find voice recordings by deleting actual songs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script analyzes audio files to distinguish between songs and recordings:

SONGS (will be DELETED):
  - Duration > 90 seconds
  - Regular tempo (60-180 BPM)
  - Strong harmonic/melodic content
  - Music metadata (artist, album)
  - Consistent beat patterns

RECORDINGS (will be KEPT):
  - Short duration (< 90 seconds)
  - No musical structure
  - Speech characteristics
  - No metadata or minimal tags
  - Voice memos, sound effects, etc.

Examples:
  # Dry run (default) - see what would be deleted
  python find_voice_recordings.py /path/to/directory
  
  # Show detailed analysis
  python find_voice_recordings.py /path/to/directory --verbose
  
  # Actually delete songs
  python find_voice_recordings.py /path/to/directory --delete
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--delete', action='store_true',
                       help='Actually delete songs (default is dry-run)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed analysis for each file')
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if args.delete:
        print("\n⚠️  WARNING: This will permanently delete all files identified as SONGS!")
        print(f"   Directory: {args.directory}")
        print("\n   Files to DELETE: Songs (music with regular tempo, harmonic content, metadata)")
        print("   Files to KEEP: Voice recordings, sound effects, short audio clips")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Check dependencies
    if not LIBROSA_AVAILABLE and not args.delete:
        print("\n💡 TIP: Install librosa for better accuracy:")
        print("   pip install librosa soundfile\n")
    
    # Scan and delete
    scan_and_delete_songs(args.directory, dry_run=not args.delete, verbose=args.verbose)


if __name__ == "__main__":
    main()
