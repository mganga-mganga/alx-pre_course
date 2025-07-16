#!/bin/bash

# Scout AI AFL Platform Installation Script
# For Linux/macOS systems

set -e

echo "🏈 Scout AI AFL Platform Installation"
echo "====================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version OK: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install package in development mode
echo "Installing Scout AI package..."
pip install -e .

# Download NLTK data
echo "Downloading NLTK data..."
python -c "
import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)  
    nltk.download('wordnet', quiet=True)
    print('✅ NLTK data downloaded')
except Exception as e:
    print(f'⚠️ NLTK download warning: {e}')
"

# Create necessary directories
echo "Creating directories..."
mkdir -p data/{raw,processed}
mkdir -p models
mkdir -p reports
mkdir -p static
echo "✅ Directories created"

# Check if ChromeDriver is needed
echo "Checking ChromeDriver availability..."
python -c "
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
try:
    service = Service(ChromeDriverManager().install())
    print('✅ ChromeDriver ready')
except Exception as e:
    print(f'⚠️ ChromeDriver warning: {e}')
    print('  Web scraping may not work properly')
"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "To start Scout AI:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Run the dashboard: streamlit run scout_ai_dashboard.py"
echo ""
echo "To test data collection:"
echo "python src/data_collection/squiggle_scraper.py"
echo ""
echo "For help and documentation, visit: https://github.com/scoutai/scout-ai-afl"