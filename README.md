# Electricity Tariff and Spot Price Analysis System

## Project Overview

This project provides a comprehensive system for collecting, analyzing, and visualizing electricity tariffs and spot prices. It consists of three main components:

1. Data Collection & Analysis System
2. REST API Service
3. WordPress Integration Plugin

## System Architecture

### Core Components

```
├── api/                 # API client implementations
├── db/                  # Database models and operations
├── strom-tarif-plugin/  # WordPress plugin
└── tests/              # Test suite
```

## Features

### 1. Data Collection

#### Spot Price Collection

- Fetches spot prices from multiple sources:
  - Awattar API (`awattar/client.py`)
  - SmartEnergy API (`smartenergy/client.py`)
- Automated data updates with gap detection
- Handles API failures gracefully

#### Tariff Analysis

- Crawls electricity provider websites (`get_tarife.py`)
- Uses LLM-based analysis for tariff extraction (`llm_analyze.py`)
- Supports multiple LLM providers:
  - OpenRouter (Llama, Gemini)
  - Groq
  - Local deployment options

### 2. Data Storage

- SQLite database with SQLAlchemy ORM
- Models for:
  - Spot prices (`spot_prices.py`)
  - Daily statistics
- Automated database maintenance

### 3. Visualization

- SVG chart generation (`gen_chartsvg.py`)
  - Daily and weekly price trends
  - Min/max price indicators
  - Responsive design
- Matplotlib-based charts (`print_chart.py`)
- Support for multiple time ranges

### 4. WordPress Plugin

The `strom-tarif-plugin` provides:

- Shortcodes for tariff display:
  - Table layout
  - Card layout
- Price chart integration
- Responsive design
- API integration with caching
- Custom styling options

## Configuration

The system uses a central `config.py` for:

- Database settings
- API credentials
- LLM configurations
- Crawling settings
- Query templates

## Installation

### Prerequisites

- Python 3.8+
- SQLite
- WordPress 5.0+ (for plugin)

### Setup Data Collection

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Initialize database
python -m db.models.spot_prices

# Test data collection
python get_tarife.py
```

### WordPress Plugin Installation

1. Copy `strom-tarif-plugin` to `wp-content/plugins/`
2. Activate plugin in WordPress admin
3. Use shortcodes:
   - `[tarifliste]` - Display tariff comparison
   - `[diagrammxyz]` - Display price charts

## API Endpoints

The system serves data via REST API:

- `/api/v1/tarifliste` - Current tariff data
- `/api/v1/spotprices` - Spot price data and charts

## Usage Examples

### Collect Tariff Data

```python
from get_tarife import fetch_and_convert_csv_to_dict
tariffs = fetch_and_convert_csv_to_dict()
```

### Generate Price Chart

```python
from gen_chartsvg import gen_chart_svg
gen_chart_svg(startday=date.today(), endday=date.today() + timedelta(days=1))
```

### WordPress Shortcodes

```php
// Display tariff table
[tarifliste rows="10" layout="table"]

// Display price chart
[diagrammxyz type="bar" title="Daily Prices"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License.

## Authors

- dev@gwen.at
- https://skale.dev
