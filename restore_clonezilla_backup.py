#!/usr/bin/env python3
"""
Clonezilla Backup File Recovery Tool

This script helps recover files from a Clonezilla backup without full restoration.
It extracts partition images and mounts them for file access.
"""

import os
import sys
import subprocess
import argparse
import tempfile
from pathlib import Path

try:
    import patoolib
    HAS_PATOOL = True
except ImportError:
    HAS_PATOOL = False


class ClonezillaRestorer:
    def __init__(self, backup_dir, output_dir=None):
        self.backup_dir = Path(backup_dir)
        self.output_dir = Path(output_dir) if output_dir else Path("./restored_files")
        self.mount_dir = Path(tempfile.mkdtemp(prefix="clonezilla_mount_"))
        self.image_dir = Path(tempfile.mkdtemp(prefix="clonezilla_images_"))
        
    def validate_backup(self):
        """Check if this is a valid Clonezilla backup"""
        clonezilla_img = self.backup_dir / "clonezilla-img"
        if not clonezilla_img.exists():
            print(f"❌ Error: Not a Clonezilla backup (missing clonezilla-img file)")
            return False
        print(f"✓ Valid Clonezilla backup detected")
        return True
    
    def find_partitions(self):
        """Find all partition images in the backup"""
        partitions = []
        seen_base_names = set()
        
        # Look for all files matching the pattern
        all_files = list(self.backup_dir.glob("*-ptcl-img.gz*"))
        
        print(f"\n🔍 Debug: Found {len(all_files)} items matching *-ptcl-img.gz*")
        for f in all_files:
            print(f"  - {f.name} (is_dir: {f.is_dir()}, is_file: {f.is_file()})")
        
        # Also check inside directories that match the pattern
        for item in self.backup_dir.glob("*-ptcl-img.gz"):
            if item.is_dir():
                print(f"  Checking inside directory: {item.name}")
                for subfile in item.iterdir():
                    if subfile.is_file():
                        print(f"    - {subfile.name}")
                        all_files.append(subfile)
        
        for file in all_files:
            # Skip directories
            if file.is_dir():
                continue
            
            name = file.name
            # Extract partition info
            if '-ptcl-img.gz' in name:
                # Get base name (everything before -ptcl-img.gz)
                base_name = name.split('-ptcl-img.gz')[0]
                
                # Skip if we already processed this base name
                if base_name in seen_base_names:
                    continue
                seen_base_names.add(base_name)
                
                # Find all files for this partition (base + split parts)
                # Only include actual files, not directories
                parts = sorted([
                    f for f in self.backup_dir.glob(f"{base_name}-ptcl-img.gz*") 
                    if f.is_file()
                ])
                
                if not parts:
                    continue
                
                # Parse filesystem type from base name
                fs_type = None
                if '.vfat-' in base_name or '.fat-' in base_name:
                    fs_type = 'vfat'
                elif '.ext4-' in base_name:
                    fs_type = 'ext4'
                elif '.ext3-' in base_name:
                    fs_type = 'ext3'
                elif '.ntfs-' in base_name:
                    fs_type = 'ntfs'
                elif '.xfs-' in base_name:
                    fs_type = 'xfs'
                
                partitions.append({
                    'name': base_name,
                    'files': parts,
                    'fs_type': fs_type,
                    'is_split': len(parts) > 1
                })
        
        return partitions
    
    def extract_partition(self, partition):
        """Extract and reconstruct a partition image"""
        print(f"\n📦 Extracting partition: {partition['name']}")
        print(f"   Filesystem: {partition['fs_type'] or 'unknown'}")
        print(f"   Split files: {len(partition['files'])}")
        
        # Debug: show what files we found
        for f in partition['files']:
            print(f"   Found: {f.name} (exists: {f.exists()}, is_file: {f.is_file()})")
        
        output_img = self.image_dir / f"{partition['name']}.img"
        
        try:
            if partition['is_split']:
                # Concatenate split files FIRST
                print(f"   Combining {len(partition['files'])} split files...")
                temp_compressed = self.image_dir / f"{partition['name']}.compressed"
                
                with open(temp_compressed, 'wb') as outfile:
                    for part_file in partition['files']:
                        print(f"   - Concatenating {part_file.name}...")
                        with open(part_file, 'rb') as infile:
                            chunk_size = 1024 * 1024  # 1MB chunks
                            while True:
                                chunk = infile.read(chunk_size)
                                if not chunk:
                                    break
                                outfile.write(chunk)
                
                compressed_file = temp_compressed
            else:
                compressed_file = partition['files'][0]
            
            # Try to detect compression format
            try:
                result = subprocess.run(['file', str(compressed_file)], capture_output=True, text=True)
                file_type = result.stdout.strip()
                print(f"   File type: {file_type}")
            except:
                pass
            
            # Try using patool first (if available)
            if HAS_PATOOL:
                try:
                    print(f"   Decompressing with patool...")
                    patoolib.extract_archive(str(compressed_file), outdir=str(self.image_dir))
                    
                    # Find the extracted file (should be the .img file)
                    extracted_files = list(self.image_dir.glob(f"{partition['name']}*"))
                    extracted_files = [f for f in extracted_files if f != compressed_file and f.is_file()]
                    
                    if extracted_files:
                        # Rename to expected output name
                        extracted_files[0].rename(output_img)
                        print(f"   ✓ Extracted to: {output_img}")
                    else:
                        raise Exception("No extracted file found")
                    
                    if partition['is_split']:
                        temp_compressed.unlink()
                    
                    return output_img
                except Exception as e:
                    print(f"   Patool extraction failed: {e}")
                    print(f"   Trying manual decompression...")
            
            # Fallback to manual decompression
            print(f"   Decompressing manually...")
            
            # Try different decompression tools
            decompress_methods = [
                (['gunzip', '-c'], 'gzip'),
                (['pigz', '-d', '-c'], 'pigz'),
                (['lz4', '-d', '-c'], 'lz4'),
                (['zstd', '-d', '-c'], 'zstd'),
                (['xz', '-d', '-c'], 'xz'),
                (['bunzip2', '-c'], 'bzip2'),
            ]
            
            success = False
            for cmd, name in decompress_methods:
                try:
                    print(f"   Trying {name}...")
                    with open(output_img, 'wb') as outfile:
                        result = subprocess.run(cmd + [str(compressed_file)], 
                                              stdout=outfile, stderr=subprocess.PIPE)
                        if result.returncode == 0:
                            success = True
                            print(f"   ✓ Successfully decompressed with {name}")
                            break
                except FileNotFoundError:
                    continue
                except Exception as e:
                    print(f"   {name} failed: {e}")
                    continue
            
            if not success:
                raise Exception("All decompression methods failed")
            
            if partition['is_split']:
                temp_compressed.unlink()
            
            print(f"   ✓ Extracted to: {output_img}")
            return output_img
        
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error extracting partition: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return None
    
    def mount_partition(self, image_path, partition_info):
        """Mount a partition image"""
        mount_point = self.mount_dir / partition_info['name']
        mount_point.mkdir(exist_ok=True)
        
        fs_type = partition_info['fs_type']
        
        print(f"\n🔧 Mounting {partition_info['name']}...")
        print(f"   Mount point: {mount_point}")
        
        try:
            # Try to mount with specific filesystem type
            if fs_type:
                cmd = ['sudo', 'mount', '-t', fs_type, '-o', 'ro,loop', str(image_path), str(mount_point)]
            else:
                cmd = ['sudo', 'mount', '-o', 'ro,loop', str(image_path), str(mount_point)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✓ Successfully mounted!")
                return mount_point
            else:
                print(f"   ⚠ Mount failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error mounting: {e}")
            return None
    
    def list_mounted_contents(self, mount_point):
        """List contents of mounted partition"""
        print(f"\n📂 Contents of {mount_point.name}:")
        try:
            result = subprocess.run(['ls', '-lah', str(mount_point)], capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print(f"   Error listing contents: {e}")
    
    def copy_files(self, mount_point, partition_name):
        """Copy files from mounted partition to output directory"""
        output_path = self.output_dir / partition_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n💾 Copying files from {partition_name}...")
        print(f"   Destination: {output_path}")
        
        try:
            cmd = ['sudo', 'cp', '-r', str(mount_point) + '/.', str(output_path)]
            subprocess.run(cmd, check=True)
            # Fix permissions
            subprocess.run(['sudo', 'chown', '-R', f'{os.getuid()}:{os.getgid()}', str(output_path)], check=True)
            print(f"   ✓ Files copied successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error copying files: {e}")
            return False
    
    def unmount_all(self):
        """Unmount all mounted partitions"""
        print(f"\n🔓 Unmounting partitions...")
        try:
            subprocess.run(['sudo', 'umount', '-l', str(self.mount_dir / '*')], 
                         stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'umount', str(self.mount_dir)], 
                         stderr=subprocess.DEVNULL)
        except:
            pass
    
    def cleanup(self):
        """Clean up temporary directories"""
        print(f"\n🧹 Cleaning up...")
        self.unmount_all()
        
        try:
            subprocess.run(['sudo', 'rm', '-rf', str(self.image_dir)], stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'rm', '-rf', str(self.mount_dir)], stderr=subprocess.DEVNULL)
        except:
            pass
    
    def restore(self, auto_copy=True):
        """Main restoration process"""
        print("=" * 70)
        print("🔄 Clonezilla Backup File Recovery Tool")
        print("=" * 70)
        
        if not self.validate_backup():
            return False
        
        partitions = self.find_partitions()
        if not partitions:
            print("❌ No partition images found in backup")
            return False
        
        print(f"\n✓ Found {len(partitions)} partition(s) to restore:")
        for i, part in enumerate(partitions, 1):
            print(f"   {i}. {part['name']} ({part['fs_type'] or 'unknown'} filesystem)")
        
        mounted_partitions = []
        
        try:
            for partition in partitions:
                # Skip swap partitions
                if 'swap' in partition['name'].lower():
                    print(f"\n⏭  Skipping swap partition: {partition['name']}")
                    continue
                
                # Extract partition
                image_path = self.extract_partition(partition)
                if not image_path:
                    continue
                
                # Mount partition
                mount_point = self.mount_partition(image_path, partition)
                if mount_point:
                    mounted_partitions.append((mount_point, partition['name']))
                    self.list_mounted_contents(mount_point)
                    
                    if auto_copy:
                        self.copy_files(mount_point, partition['name'])
            
            if not auto_copy and mounted_partitions:
                print("\n" + "=" * 70)
                print("📍 Partitions are mounted and ready for file recovery!")
                print("=" * 70)
                for mount_point, name in mounted_partitions:
                    print(f"   {name}: {mount_point}")
                print("\nYou can now browse and copy files manually.")
                print("Press Enter when done to unmount and cleanup...")
                input()
            
            if auto_copy:
                print("\n" + "=" * 70)
                print("✅ File Recovery Complete!")
                print("=" * 70)
                print(f"📁 Recovered files are in: {self.output_dir.absolute()}")
                
        finally:
            self.cleanup()
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Recover files from a Clonezilla backup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-copy all files to ./restored_files
  %(prog)s /path/to/backup
  
  # Specify output directory
  %(prog)s /path/to/backup -o /path/to/output
  
  # Just mount partitions for manual browsing
  %(prog)s /path/to/backup --no-auto-copy
        """
    )
    
    parser.add_argument('backup_dir', help='Path to Clonezilla backup directory')
    parser.add_argument('-o', '--output', help='Output directory for recovered files (default: ./restored_files)')
    parser.add_argument('--no-auto-copy', action='store_true', 
                       help='Mount partitions without auto-copying (for manual file browsing)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.backup_dir):
        print(f"❌ Error: Backup directory not found: {args.backup_dir}")
        sys.exit(1)
    
    # Check if running with sudo for mount operations
    if os.geteuid() != 0:
        print("⚠️  Note: This script requires sudo privileges to mount partitions.")
        print("    You may be prompted for your password.\n")
    
    restorer = ClonezillaRestorer(args.backup_dir, args.output)
    
    try:
        success = restorer.restore(auto_copy=not args.no_auto_copy)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        restorer.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        restorer.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
