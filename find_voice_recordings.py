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


# Audio MIME types to analyze
AUDIO_MIME_TYPES = {
    'audio/mpeg',           # MP3
    'audio/ogg',            # OGG
    'audio/x-m4a',          # M4A
    'audio/x-wav',          # WAV
    'audio/x-aiff',         # AIFF
    'audio/flac',           # FLAC
    'audio/aac',            # AAC
    'audio/x-ms-wma',       # WMA
    'audio/AMR',            # AMR (voice codec)
    'audio/midi',           # MIDI
    'audio/x-mp4a-latm',
    'audio/x-hx-aac-adts',
}


def get_mime_type(file_path):
    """Get MIME type of file."""
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    except Exception:
        return None


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
    try:
        # Load audio (limit to first 60 seconds for speed)
        y, sr = librosa.load(str(file_path), duration=60, sr=22050)
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
        percussive_ratio = np.sum(np.abs(y_percussive)) / (np.sum(np.abs(y)) + 1e-6)
        
        # 5. Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        
        # 6. Zero crossing rate (speech has higher ZCR)
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
        
    except Exception as e:
        return None, 0.0, f"error_{str(e)[:30]}"


def analyze_audio_basic(file_path):
    """
    Basic audio analysis without librosa.
    Uses only duration and metadata.
    Returns: (is_song, confidence, reason)
    """
    try:
        # Get file size as rough duration estimate
        size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Check metadata
        has_metadata = has_music_metadata(file_path)
        
        confidence = 0.0
        reasons = []
        
        # If it has music metadata, very likely a song
        if has_metadata:
            confidence += 0.6
            reasons.append("has_music_metadata")
        
        # File size heuristic (rough estimate: 1MB ≈ 1 minute for MP3)
        if size_mb > 2:  # > 2MB likely a song
            confidence += 0.3
            reasons.append(f"large_{size_mb:.1f}MB")
        elif size_mb < 0.5:  # < 0.5MB likely a short recording
            confidence -= 0.2
            reasons.append(f"small_{size_mb:.1f}MB")
        
        is_song = confidence > 0.4
        reason = "+".join(reasons) if reasons else "no_indicators"
        
        return is_song, confidence, reason
        
    except Exception as e:
        return None, 0.0, f"error_{str(e)[:30]}"


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
        if mime_type in AUDIO_MIME_TYPES:
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
            errors.append((file_path, reason))
            if verbose:
                tqdm.write(f"  [ERROR] {file_path.name}: {reason}")
        elif is_song:
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
