# Image Conversion Dependencies

## Required

```bash
pip install Pillow python-magic tqdm
```

## Optional (but recommended)

For maximum compatibility with all image formats:

```bash
# HEIC/HEIF support (Apple photos)
pip install pillow-heif

# SVG support (vector graphics)
pip install cairosvg

# Fallback converter for exotic/corrupted formats
pip install imageio

# NumPy (required by imageio)
pip install numpy
```

## All at once

```bash
pip install Pillow python-magic tqdm pillow-heif cairosvg imageio numpy
```

## Platform-specific notes

### macOS
```bash
brew install libmagic
pip install Pillow python-magic tqdm pillow-heif cairosvg imageio numpy
```

### Ubuntu/Debian
```bash
sudo apt-get install libmagic1
pip install Pillow python-magic tqdm pillow-heif cairosvg imageio numpy
```

### Windows
- Install libmagic: Download from https://github.com/pidydx/libmagicwin64
- Or use python-magic-bin instead of python-magic

```bash
pip install python-magic-bin Pillow tqdm pillow-heif cairosvg imageio numpy
```

## Supported Formats

With all dependencies installed, the script can convert:

- **Common formats**: JPEG, PNG, GIF, BMP, TIFF, WebP, ICO
- **Apple formats**: HEIC, HEIF (requires pillow-heif)
- **Vector**: SVG, SVGZ (requires cairosvg)
- **Advanced**: TGA, PSD, DDS, JP2
- **RAW formats**: CR2, NEF, ARW, DNG (via imageio)
- **Exotic formats**: Any format supported by Pillow or imageio

## Troubleshooting

### HEIC files not converting
```bash
pip install pillow-heif
```

### SVG files failing
```bash
pip install cairosvg
```

### "Decompression bomb" errors
The script disables PIL's decompression bomb limit to allow large legitimate images.

### Corrupted/truncated files
The script uses imageio as a fallback converter when Pillow fails.
