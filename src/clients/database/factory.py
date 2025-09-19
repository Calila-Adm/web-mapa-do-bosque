"""
Factory pattern para criar clientes de banco de dados.
Suporta múltiplas conexões simultâneas.
"""
import os
from typing import Union, Optional, Dict, Any

# Importações condicionais para evitar erros se uma lib não estiver instalada
def get_database_client(client_type: Optional[str] = None):
    """
    Retorna o cliente Supabase (único banco de dados suportado).

    Args:
        client_type: Ignorado - sempre retorna Supabase

    Returns:
        Cliente Supabase
    """
    try:
        from .supabase_postgres import SupabaseClient
        return SupabaseClient()
    except ImportError as e:
        raise ImportError(
            "Supabase dependencies not installed. "
            "Run: pip install sqlalchemy psycopg2-binary"
        ) from e


def get_multiple_clients() -> Dict[str, Any]:
    """
    Retorna cliente Supabase disponível.

    Returns:
        Dict com cliente Supabase
    """
    clients = {}

    # Sempre usar Supabase como cliente principal
    try:
        clients['primary'] = get_database_client()
        clients['supabase'] = clients['primary']
    except Exception as e:
        print(f"Warning: Could not initialize Supabase client: {e}")

    return clients


def get_table_config(db_type: Optional[str] = None):
    """
    Retorna a configuração das tabelas do Supabase.

    Args:
        db_type: Ignorado - sempre retorna configuração do Supabase

    Returns:
        Dict com configuração das tabelas
    """
    # Sempre usar configuração do Supabase - com underscore
    schema = os.getenv("SUPABASE_SCHEMA_MAPA", "mapa_do_bosque")
    return {
        'pessoas': {
            'schema': schema,
            'table': os.getenv("SUPABASE_TABLE_PESSOAS", "fluxo_de_pessoas"),
            'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
            'metric_col': os.getenv("SUPABASE_METRIC_COL", "value"),
            'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
            'titulo': 'Fluxo de Pessoas',
            'unidade': 'pessoas',
            'icon': '👥',
            'color': '#1E90FF'
        },
        'veiculos': {
            'schema': schema,
            'table': os.getenv("SUPABASE_TABLE_VEICULOS", "fluxo_de_veiculos"),
            'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
            'metric_col': os.getenv("SUPABASE_METRIC_COL", "value"),
            'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
            'titulo': 'Fluxo de Veículos',
            'unidade': 'veículos',
            'icon': '🚗',
            'color': '#FF6B6B'
        },
        'vendas': {
            'schema': schema,
            'table': os.getenv("SUPABASE_TABLE_VENDAS", "vendas_gshop"),
            'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
            'metric_col': os.getenv("SUPABASE_METRIC_COL", "value"),
            'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
            'titulo': 'Vendas',
            'unidade': 'R$',
            'icon': '💰',
            'color': '#28A745'
        }
    }


def get_supabase_table_config():
    """
    Retorna configuração específica para tabelas do Supabase.
    Estas são tabelas adicionais, não substituem as principais.
    As tabelas podem incluir o schema no formato 'schema.table'.

    Returns:
        Dict com configuração das tabelas adicionais do Supabase
    """
    # Get schemas from environment
    schema_analytics = os.getenv("SUPABASE_SCHEMA_2", "analytics")
    schema_operations = os.getenv("SUPABASE_SCHEMA_3", "operations")

    return {
        'analytics': {
            'table': os.getenv("SUPABASE_TABLE_ANALYTICS", f"{schema_analytics}.analytics_data"),
            'date_col': os.getenv("SUPABASE_ANALYTICS_DATE_COL", "timestamp"),
            'metric_col': os.getenv("SUPABASE_ANALYTICS_METRIC_COL", "value"),
            'titulo': 'Analytics',
            'unidade': 'eventos',
            'icon': '📈',
            'color': '#9B59B6'
        },
        'satisfaction': {
            'table': os.getenv("SUPABASE_TABLE_SATISFACTION", f"{schema_analytics}.customer_satisfaction"),
            'date_col': os.getenv("SUPABASE_SATISFACTION_DATE_COL", "date"),
            'metric_col': os.getenv("SUPABASE_SATISFACTION_METRIC_COL", "score"),
            'titulo': 'Satisfação do Cliente',
            'unidade': 'pontos',
            'icon': '😊',
            'color': '#FFA500'
        },
        'occupancy': {
            'table': os.getenv("SUPABASE_TABLE_OCCUPANCY", f"{schema_operations}.mall_occupancy"),
            'date_col': os.getenv("SUPABASE_OCCUPANCY_DATE_COL", "date"),
            'metric_col': os.getenv("SUPABASE_OCCUPANCY_METRIC_COL", "percentage"),
            'titulo': 'Taxa de Ocupação',
            'unidade': '%',
            'icon': '🏢',
            'color': '#20B2AA'
        },
        'energy': {
            'table': os.getenv("SUPABASE_TABLE_ENERGY", f"{schema_operations}.energy_consumption"),
            'date_col': os.getenv("SUPABASE_ENERGY_DATE_COL", "date"),
            'metric_col': os.getenv("SUPABASE_ENERGY_METRIC_COL", "kwh"),
            'titulo': 'Consumo de Energia',
            'unidade': 'kWh',
            'icon': '⚡',
            'color': '#FFD700'
        }
    }


def fetch_data_generic(client, config, year_filter=None, shopping_filter=None, client_type=None):
    """
    Função para buscar dados usando cliente Supabase.

    Args:
        client: Cliente Supabase
        config: Dicionário com configuração da tabela
        year_filter: Filtro opcional de ano
        shopping_filter: Filtro opcional de shopping
        client_type: Ignorado - sempre usa Supabase

    Returns:
        DataFrame com os dados
    """
    # Sempre usar Supabase - precisa incluir o schema
    table_with_schema = config['table']
    if config.get('schema'):
        table_with_schema = f"{config['schema']}.{config['table']}"

    df = client.fetch_wbr_data(
        table_name=table_with_schema,
        date_col=config['date_col'],
        metric_col=config['metric_col'],
        shopping_col=config.get('shopping_col')
    )

    # Aplicar filtros se necessário
    if year_filter and 'date' in df.columns:
        df = df[df['date'].dt.year == year_filter]

    if shopping_filter and 'shopping' in df.columns:
        df = df[df['shopping'].str.contains(shopping_filter, case=False, na=False)]

    return df