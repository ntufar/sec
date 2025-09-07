#!/bin/bash
# Setup script for SEC Downloader environment variables
# Run this script before using the application: source setup_env.sh

echo "Setting up SEC Downloader environment..."

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS - setting up WeasyPrint environment variables"
    
    # WeasyPrint requires this on macOS to find system libraries
    export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH
    
    echo "✅ Environment variables set for SEC Downloader"
    echo "   DYLD_FALLBACK_LIBRARY_PATH: $DYLD_FALLBACK_LIBRARY_PATH"
    
    # Check if Homebrew libraries are installed
    if ! brew list cairo >/dev/null 2>&1; then
        echo "⚠️  Warning: WeasyPrint system libraries not found"
        echo "   Run: brew install cairo pango gdk-pixbuf libffi"
    else
        echo "✅ WeasyPrint system libraries found"
    fi
else
    echo "✅ Non-macOS system detected - no special setup required"
fi

echo ""
echo "You can now run SEC Downloader commands:"
echo "  python -m sec_downloader --help"
echo "  python -m sec_downloader list-tickers"
echo "  python -m sec_downloader download AAPL --convert"
