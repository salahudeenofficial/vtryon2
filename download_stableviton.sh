#!/bin/bash

# download_stableviton.sh - Download checkpoints folder from Google Drive to StableVITON directory

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STABLEVITON_DIR="${SCRIPT_DIR}/StableVITON"
GOOGLE_DRIVE_URL="https://drive.google.com/drive/folders/1eh6MJxB_PrSgblZncZfYTWPHiqNXcWHW?usp=drive_link"

echo "=========================================="
echo "Downloading StableVITON Checkpoints"
echo "=========================================="
echo "Target directory: ${STABLEVITON_DIR}"
echo "Google Drive URL: ${GOOGLE_DRIVE_URL}"
echo ""

# Check if gdown is installed
if ! command -v gdown &> /dev/null; then
    echo "❌ gdown is not installed. Installing..."
    pip install gdown || {
        echo "❌ Failed to install gdown. Please install it manually: pip install gdown"
        exit 1
    }
    echo "✓ gdown installed"
fi

# Create StableVITON directory if it doesn't exist
if [ ! -d "$STABLEVITON_DIR" ]; then
    echo "Creating StableVITON directory..."
    mkdir -p "$STABLEVITON_DIR"
    echo "✓ StableVITON directory created"
else
    echo "✓ StableVITON directory already exists"
fi

# Change to StableVITON directory
cd "$STABLEVITON_DIR"

echo ""
echo "Downloading checkpoints folder..."
echo "This may take a while depending on the size of the files..."
echo ""

# Download the folder using gdown
gdown --folder "$GOOGLE_DRIVE_URL" --remaining-ok || {
    echo "❌ Failed to download checkpoints folder"
    echo "Please check:"
    echo "  1. The Google Drive link is accessible"
    echo "  2. You have permission to access the folder"
    echo "  3. Your internet connection is stable"
    exit 1
}

echo ""
echo "=========================================="
echo "✓ Download complete!"
echo "=========================================="
echo "Checkpoints folder location: ${STABLEVITON_DIR}/checkpoints"
echo ""

# Verify the checkpoints folder exists
if [ -d "${STABLEVITON_DIR}/checkpoints" ]; then
    echo "✓ Verified: checkpoints folder exists"
    echo "Contents:"
    ls -lh "${STABLEVITON_DIR}/checkpoints" | head -10
else
    echo "⚠️  Warning: checkpoints folder not found after download"
    echo "Please check the download manually"
fi

echo ""
echo "=========================================="

