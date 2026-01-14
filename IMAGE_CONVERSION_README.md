# Image Conversion Script - Setup and Usage

## Installation

The script requires several Python packages to handle all image formats:

```bash
# Core requirements (required)
pip install Pillow python-magic tqdm

# Optional: HEIC/HEIF support (Apple photos from iPhone/iPad)
pip install pillow-heif

# Optional: SVG support
pip install cairosvg

# Optional: Additional format support (RAW, HDR, etc.)
pip install imageio imageio-ffmpeg rawpy

# Or install all at once:
pip install Pillow python-magic tqdm pillow-heif cairosvg imageio imageio-ffmpeg rawpy
```

## Supported Formats

The script now detects and converts **ALL** image formats:

### Common Formats
- JPEG (.jpg, .jpeg, .jpe, .jfif, .jif)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp, .dib)
- TIFF (.tiff, .tif)
- WebP (.webp)
- ICO (.ico, .icon, .cur)

### Modern/Apple Formats
- HEIC/HEIF (.heic, .heif, .heics, .heifs)
- AVIF (.avif)

### Professional/RAW Formats
- **Photoshop**: .psd, .psb
- **GIMP**: .xcf
- **Camera RAW**: .raw, .cr2 (Canon), .nef (Nikon), .arw (Sony), .dng (Adobe), .orf (Olympus), .rw2 (Panasonic), .pef (Pentax), .sr2 (Sony), .raf (Fujifilm)

### Other Formats
- **Raster**: TGA, DDS, JPEG 2000 (.jp2, .j2k), PCX, Netpbm (.ppm, .pgm, .pbm), SGI, PICT, OpenEXR, HDR, IFF, FITS
- **Vector**: SVG (requires cairosvg)

The script now:
1. **Checks file extensions first** (fast identification of 80+ image formats)
2. **Falls back to MIME detection** for files without extensions
3. **Includes comprehensive format support** - HEIC, RAW, PSD, TGA, JPEG 2000, HDR, EXR, and more
4. **Handles errors gracefully** with multiple fallback methods (Pillow → pillow-heif → imageio)

The script should now find all 30K+ images in your directory!