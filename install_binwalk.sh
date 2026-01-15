#!/bin/bash
# Installation script for binwalk and dependencies

echo "Installing binwalk and dependencies..."
sudo apt-get update
sudo apt-get install -y binwalk

echo ""
echo "Binwalk installed successfully!"
echo "You can now run Airganizer with full binwalk analysis:"
echo "  python -m src /path/to/directory"
