#!/bin/bash

# Daily Digest Setup Script
# Run this script to set up your daily digest tool

set -e

echo "🚀 Setting up Daily Digest Generator..."
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 from https://python.org"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📋 Creating .env file from template..."
        cp .env.example .env
        echo "⚠️  Please edit .env file with your API credentials"
    else
        echo "❌ .env.example not found. Please create .env manually."
    fi
else
    echo "✅ .env file already exists"
fi

echo
echo "🎉 Setup complete!"
echo
echo "Next steps:"
echo "1. Edit .env with your API credentials:"
echo "   - GitHub token"
echo "   - Jira credentials"
echo "   - Google Calendar ICS URL"
echo
echo "2. Test the installation:"
echo "   source venv/bin/activate"
echo "   python daily_digest.py --date yesterday"
echo
echo "3. Set up daily automation (optional):"
echo "   crontab -e"
echo "   Add: 0 18 * * * cd $(pwd) && source venv/bin/activate && python daily_digest.py"
echo
echo "📖 See README.md for detailed configuration instructions"
echo "Happy tracking! 📊"