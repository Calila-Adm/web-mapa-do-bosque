"""
Configurações centralizadas do aplicativo.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Database Configuration
DB_CONFIG = {
    "type": os.getenv("DB_TYPE", "postgresql"),
    "postgres": {
        "schema": os.getenv("POSTGRES_SCHEMA", "mapa_do_bosque"),
        "tables": {
            "pessoas": os.getenv("POSTGRES_TABLE_PESSOAS", "fluxo_de_pessoas"),
            "veiculos": os.getenv("POSTGRES_TABLE_VEICULOS", "fluxo_de_veiculos"),
        }
    },
    "bigquery": {
        "project": os.getenv("BIGQUERY_PROJECT_ID"),
        "dataset": os.getenv("BIGQUERY_DATASET"),
    }
}

# Application Settings
APP_CONFIG = {
    "title": "WBR Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Chart Settings
CHART_CONFIG = {
    "height": 400,
    "template": "plotly_white",
    "colors": {
        "pessoas": "#1E90FF",
        "veiculos": "#FF6B6B",
    }
}
