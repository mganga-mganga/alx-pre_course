"""
Setup script for Scout AI AFL Platform
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "AI-powered scouting platform for the Australian Football League"

setup(
    name="scout-ai-afl",
    version="1.0.0",
    author="Scout AI Development Team",
    author_email="contact@scoutai.afl",
    description="AI-powered scouting platform for the Australian Football League",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/scoutai/scout-ai-afl",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Sports/Analytics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.1.0",
        "numpy>=1.25.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "selenium>=4.15.0",
        "scikit-learn>=1.3.0",
        "matplotlib>=3.8.0",
        "seaborn>=0.13.0",
        "plotly>=5.17.0",
        "streamlit>=1.28.0",
        "reportlab>=4.0.0",
        "openpyxl>=3.1.0",
        "transformers>=4.36.0",
        "torch>=2.1.0",
        "flask>=3.0.0",
        "sqlalchemy>=2.0.0",
        "nltk>=3.8.0",
        "wordcloud>=1.9.0",
        "Pillow>=10.1.0",
        "webdriver-manager>=4.0.0",
        "altair>=4.2.1,<5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scout-ai=scout_ai_dashboard:main",
            "scout-ai-scraper=src.data_collection.squiggle_scraper:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="afl football scouting analytics machine-learning sports",
    project_urls={
        "Bug Reports": "https://github.com/scoutai/scout-ai-afl/issues",
        "Source": "https://github.com/scoutai/scout-ai-afl",
        "Documentation": "https://scout-ai-afl.readthedocs.io/",
    },
)