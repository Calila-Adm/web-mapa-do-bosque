# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit application for visualizing Working Backwards Reporting (WBR) metrics from Google BigQuery. The app processes and displays time-series data with interactive Plotly charts and KPIs.

## Development Commands

```bash
# Install dependencies
make install
# or
pip install -r requirements.txt

# Run the application
make run
# or
streamlit run src/app/streamlit_app.py

# Run tests
make test
# or
pytest -q

# Clean Python cache files
make clean
```

## Architecture

### Core Components

1. **BigQuery Integration** (`src/data/bigquery_client.py`)
   - Handles authentication via service account JSON
   - Executes SQL queries from `src/data/queries/wbr.sql`
   - Supports dynamic table/column discovery
   - Normalizes data to standard format (date, metric_value, optional shopping)

2. **WBR Processing Pipeline** (`src/wbr/`)
   - `core.py`: Main orchestration function `gerar_grafico_wbr()`
   - `processing.py`: Data aggregation by week/month for current/previous year
   - `kpis.py`: KPI calculations (YoY, WoW, MTD comparisons)
   - `charts.py`: Plotly chart generation with WBR-specific formatting

3. **Streamlit App** (`src/app/streamlit_app.py`)
   - Main entry point with sidebar configuration
   - Dynamic BigQuery table/column selection
   - Support for filtering by shopping location and year
   - Metric toggle between "Fluxo de Pessoas" and "Fluxo de Veículos"

### Environment Configuration

The app uses a layered environment variable approach:
1. `.env` file in project root (general config)
2. `.secrets/.env` file (sensitive credentials, gitignored)
3. Environment variables can override file values

Required environment variables:
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to BigQuery service account JSON
- `BIGQUERY_PROJECT_ID`: GCP project ID
- `BIGQUERY_DATASET`: BigQuery dataset name
- `BIGQUERY_TABLE`: Default table name

Optional variables for column mapping:
- `WBR_DATE_COL`: Date column name
- `WBR_METRIC_COL`: Metric column name
- `WBR_SHOPPING_COL`: Shopping filter column
- `WBR_METRIC_COL_PESSOAS`: People flow metric column
- `WBR_METRIC_COL_VEICULOS`: Vehicle flow metric column

### Data Flow

1. User configures parameters in Streamlit sidebar
2. `BigQueryClient.fetch_wbr_data()` executes SQL with template substitution
3. Data is normalized to standard columns (date, metric_value)
4. `processar_dados_wbr()` aggregates into weekly/monthly series
5. `calcular_kpis()` computes year-over-year metrics
6. `criar_grafico_wbr()` generates Plotly visualization
7. Results displayed in Streamlit interface

## Testing

Tests are located in `tests/` directory:
- `test_processing.py`: WBR data processing logic
- `test_kpis.py`: KPI calculation accuracy
- `test_bigquery_client.py`: BigQuery client functionality
- `conftest.py`: Shared pytest fixtures

Run a specific test:
```bash
pytest tests/test_processing.py -v
```

## Key Design Patterns

1. **Lazy Authentication**: BigQuery client authenticates only when needed
2. **Column Inference**: Automatically detects date/metric columns from table schema
3. **Caching**: Uses Streamlit's `@st.cache_data` for expensive operations
4. **Template SQL**: SQL queries use template variables for project/dataset/table
5. **Modular Processing**: Separate concerns for data fetch, processing, KPIs, and visualization