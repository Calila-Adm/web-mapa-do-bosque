# WBR Streamlit BigQuery

This project is a Streamlit application designed to visualize data using the Working Backwards Reporting (WBR) methodology. It retrieves data from Google BigQuery and presents it through interactive charts and key performance indicators (KPIs).

## Project Structure

```
wbr-streamlit-bigquery
├── src
│   ├── app
│   │   ├── streamlit_app.py         # Main entry point for the Streamlit application
│   │   └── pages
│   │       └── 01_Overview.py        # Overview page displaying key metrics
│   ├── data
│   │   ├── bigquery_client.py        # Handles BigQuery interactions
│   │   ├── queries
│   │   │   └── wbr.sql               # SQL queries for WBR data retrieval
│   │   └── __init__.py               # Marks the data directory as a package
│   ├── wbr
│   │   ├── processing.py             # Data processing functions for WBR
│   │   ├── kpis.py                   # Functions for KPI calculations
│   │   ├── charts.py                 # Visualization functions
│   │   └── __init__.py               # Marks the WBR directory as a package
│   ├── utils
│   │   ├── env.py                    # Environment variable loading
│   │   └── logging.py                 # Logging setup for the application
│   └── config
│       ├── settings.py               # Configuration settings for the application
│       └── __init__.py               # Marks the config directory as a package
├── tests
│   ├── test_processing.py             # Unit tests for processing functions
│   ├── test_kpis.py                   # Unit tests for KPI calculations
│   └── test_bigquery_client.py        # Unit tests for BigQuery client functions
├── notebooks
│   └── exploration.ipynb              # Jupyter notebook for exploratory data analysis
├── .streamlit
│   └── config.toml                    # Streamlit configuration settings
├── .env.example                        # Template for environment variables
├── .gitignore                         # Files and directories to ignore by Git
├── requirements.txt                   # Python dependencies for the project
├── pyproject.toml                     # Project dependencies and configurations
├── Makefile                           # Automation commands for the project
└── README.md                          # Documentation for the project
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd wbr-streamlit-bigquery
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   - Copy `.env.example` to `.env` and fill in the required variables.

5. **Run the Streamlit Application**
   ```bash
   streamlit run src/app/streamlit_app.py
   ```

## Usage

- Navigate to the overview page to view key metrics and visualizations.
- Use the sidebar to explore different sections of the application.

## Testing

To run the tests, use the following command:
```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.