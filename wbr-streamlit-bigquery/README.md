# WBR Streamlit BigQuery

This project is a Streamlit application designed to visualize data using the Working Backwards Reporting (WBR) methodology. It retrieves data from Google BigQuery and presents it through interactive charts and key performance indicators (KPIs).

## Project Structure

```
wbr-streamlit-bigquery
├── src
│   ├── app
│   │   ├── streamlit_app.py         # Main Streamlit application (single-page)
│   │   └── pages
│   │       └── .01_wbr.py            # Hidden page (disabled with dot prefix)
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
│   └── config.toml                    # Streamlit configuration (server, theme)
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


## Deploy rápido com Docker + ngrok

Este projeto inclui um `Dockerfile` e `docker-compose.yml` para executar o Streamlit e expor via ngrok (sidecar).

Passos:

1) Crie seu arquivo `.env` a partir de `.env.example` e preencha:
   - `BIGQUERY_PROJECT_ID`, `BIGQUERY_DATASET`
   - `GOOGLE_APPLICATION_CREDENTIALS` com o caminho ABSOLUTO no host para o JSON da service account.

2) Crie `.secrets/.env` contendo seu token do ngrok:
   - `NGROK_AUTHTOKEN=seu_token`

3) Suba com Docker Compose:

   - O serviço `app` expõe a porta 8501 localmente.
   - O serviço `ngrok` criará um túnel público e a UI estará em http://localhost:4040.

Ao subir, acesse a URL Pública listada na interface do ngrok (porta 4040) ou nos logs do container do ngrok.

## Usage


## Testing

To run the tests, use the following command:
```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.