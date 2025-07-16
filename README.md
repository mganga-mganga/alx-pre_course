# Scout AI - AFL Scouting Platform

A comprehensive AI-powered scouting platform for the Australian Football League (AFL) that aggregates data from multiple sources, analyzes player and team performance, generates interactive visualizations, and produces customizable reports.

## Features

- **Data Aggregation**: Scrapes data from Squiggle API, FootyWire, and other AFL sources
- **Advanced Analytics**: ML-powered player evaluation and performance prediction
- **Interactive Visualizations**: Dynamic dashboards with AFL-specific metrics
- **Natural Language Queries**: Chat with your data using plain English
- **Multi-format Reporting**: Generate PDF, Excel, and web-based reports
- **Mobile-Friendly**: Access insights on-the-go
- **State League Coverage**: Includes VFL, SANFL, WAFL, and junior competitions

## Setup Instructions

1. **Create Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate  # Windows
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup ChromeDriver:**
   ChromeDriver will be automatically downloaded via webdriver-manager

4. **Run the Platform:**
   ```bash
   streamlit run scout_ai_dashboard.py
   ```

## Project Structure

```
scout_ai_afl/
├── data/
│   ├── raw/
│   ├── processed/
│   └── afl_data.db
├── src/
│   ├── data_collection/
│   ├── analysis/
│   ├── visualization/
│   ├── reporting/
│   └── nlp/
├── models/
├── reports/
└── static/
```

## Usage

1. Start the Streamlit dashboard
2. Use natural language queries like "Find midfielders under 23 with high clearance rates"
3. Filter data by position, age, stats, and league
4. Generate custom reports in your preferred format
5. Export visualizations and analysis

## Data Sources

- Squiggle API: Match results, predictions, ladder data
- FootyWire: Player statistics and performance metrics
- Additional sources for advanced analytics

## Legal Compliance

This platform complies with Australian Privacy Principles and respects data usage terms from all sources.
