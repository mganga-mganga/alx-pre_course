@echo off
REM Scout AI AFL Platform Installation Script
REM For Windows systems

echo 🏈 Scout AI AFL Platform Installation
echo =====================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Update pip
echo Updating pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install package in development mode
echo Installing Scout AI package...
pip install -e .

REM Download NLTK data
echo Downloading NLTK data...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); print('✅ NLTK data downloaded')"

REM Create necessary directories
echo Creating directories...
if not exist "data\raw" mkdir data\raw
if not exist "data\processed" mkdir data\processed
if not exist "models" mkdir models
if not exist "reports" mkdir reports
if not exist "static" mkdir static
echo ✅ Directories created

REM Check ChromeDriver
echo Checking ChromeDriver availability...
python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install(); print('✅ ChromeDriver ready')" 2>nul || echo ⚠️ ChromeDriver may need manual setup

echo.
echo 🎉 Installation completed successfully!
echo.
echo To start Scout AI:
echo 1. Activate the virtual environment: .venv\Scripts\activate.bat
echo 2. Run the dashboard: streamlit run scout_ai_dashboard.py
echo.
echo To test data collection:
echo python src\data_collection\squiggle_scraper.py
echo.
echo For help and documentation, visit: https://github.com/scoutai/scout-ai-afl
pause