#!/bin/bash
# Build script for Rotator Translator macOS app
# This script will create a double-clickable .app bundle

set -e  # Exit on error

echo "==================================="
echo "Rotator Translator App Builder"
echo "==================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if py2app is installed, install if needed
if ! python3 -c "import py2app" 2>/dev/null; then
    echo ""
    echo "Installing py2app (required for building Mac apps)..."
    pip3 install py2app
    echo "✓ py2app installed"
else
    echo "✓ py2app already installed"
fi

echo ""
echo "Cleaning previous builds..."
rm -rf build dist

echo ""
echo "Building macOS application bundle..."
python3 setup.py py2app

if [ -d "dist/Rotator Translator.app" ]; then
    echo ""
    echo "Code signing the application..."

    # Sign all .so and .dylib files first (inside-out signing)
    echo "Signing libraries and extensions..."
    find "dist/Rotator Translator.app" -type f \( -name "*.so" -o -name "*.dylib" \) \
        -exec codesign --force --sign "Developer ID Application: Michael Richard Garcia (49G92DYD5H)" \
        --options runtime {} \; 2>/dev/null

    # Sign the Python framework
    if [ -f "dist/Rotator Translator.app/Contents/Frameworks/Python.framework/Versions/3.12/Python" ]; then
        echo "Signing Python framework..."
        codesign --force --sign "Developer ID Application: Michael Richard Garcia (49G92DYD5H)" \
            --options runtime \
            "dist/Rotator Translator.app/Contents/Frameworks/Python.framework/Versions/3.12/Python"
    fi

    # Sign the main app bundle (without --deep)
    echo "Signing main app bundle..."
    codesign --force --sign "Developer ID Application: Michael Richard Garcia (49G92DYD5H)" \
        --options runtime \
        "dist/Rotator Translator.app"

    if [ $? -eq 0 ]; then
        echo "✓ Code signing successful"

        # Verify the signature
        echo ""
        echo "Verifying code signature..."
        codesign --verify --verbose=2 "dist/Rotator Translator.app"

        if [ $? -eq 0 ]; then
            echo "✓ Code signature verified"
        else
            echo "⚠️  Warning: Code signature verification failed"
        fi
    else
        echo "⚠️  Warning: Code signing failed - app may not run correctly"
    fi

    echo ""
    echo "==================================="
    echo "✅ SUCCESS!"
    echo "==================================="
    echo ""
    echo "Your app is ready: dist/Rotator Translator.app"
    echo ""
    echo "To install:"
    echo "  1. Open Finder and go to this folder"
    echo "  2. Drag 'Rotator Translator.app' to your Applications folder"
    echo "  3. Double-click to run!"
    echo ""
    echo "The app will open a Terminal window showing connection logs."
    echo ""

    # Optionally open the dist folder
    read -p "Open the dist folder now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open dist
    fi
else
    echo ""
    echo "❌ Build failed - app not created"
    exit 1
fi
