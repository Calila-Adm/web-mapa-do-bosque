"""
Constantes e enumerações do aplicativo.
"""

from enum import Enum

class MetricType(Enum):
    """Tipos de métricas disponíveis."""
    PESSOAS = "pessoas"
    VEICULOS = "veiculos"
    VENDAS = "vendas"

class TimeGranularity(Enum):
    """Granularidade temporal para agregações."""
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"
    QUARTERLY = "Q"
    YEARLY = "Y"

class KPIType(Enum):
    """Tipos de KPIs calculados."""
    YOY = "yoy"  # Year over Year
    WOW = "wow"  # Week over Week
    MTD = "mtd"  # Month to Date
    QTD = "qtd"  # Quarter to Date
    YTD = "ytd"  # Year to Date

class DatabaseType(Enum):
    """Tipos de bancos de dados suportados."""
    BIGQUERY = "bigquery"
    POSTGRESQL = "postgresql"
    SUPABASE = "supabase"

# Table configurations
TABLES_CONFIG = {
    MetricType.PESSOAS: {
        'titulo': 'Fluxo de Pessoas',
        'unidade': 'pessoas',
        'icon': '👥',
        'color': '#1E90FF'
    },
    MetricType.VEICULOS: {
        'titulo': 'Fluxo de Veículos',
        'unidade': 'veículos',
        'icon': '🚗',
        'color': '#FF6B6B'
    },
    MetricType.VENDAS: {
        'titulo': 'Vendas',
        'unidade': 'R$',
        'icon': '💰',
        'color': '#28A745'
    }
}
