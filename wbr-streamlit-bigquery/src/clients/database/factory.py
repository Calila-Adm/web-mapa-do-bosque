"""
Factory pattern para criar o cliente de banco de dados apropriado
baseado na configuração de ambiente.
"""
import os
from typing import Union, Optional

# Importações condicionais para evitar erros se uma lib não estiver instalada
def get_database_client():
    """
    Retorna o cliente de banco de dados apropriado baseado em DB_TYPE.
    
    Returns:
        BigQueryClient ou PostgreSQLClient dependendo da configuração
    """
    db_type = os.getenv("DB_TYPE", "postgresql").lower()
    
    if db_type == "postgresql" or db_type == "postgres":
        try:
            from .postgresql import PostgreSQLClient
            return PostgreSQLClient()
        except ImportError as e:
            raise ImportError(
                "PostgreSQL dependencies not installed. "
                "Run: pip install psycopg2-binary"
            ) from e
    
    elif db_type == "bigquery":
        try:
            from .bigquery import BigQueryClient
            return BigQueryClient()
        except ImportError as e:
            raise ImportError(
                "BigQuery dependencies not installed. "
                "Run: pip install google-cloud-bigquery google-cloud-bigquery-storage db-dtypes"
            ) from e
    
    else:
        raise ValueError(
            f"Unknown database type: {db_type}. "
            "Set DB_TYPE to 'postgresql' or 'bigquery' in your .env file"
        )


def get_table_config(db_type: Optional[str] = None):
    """
    Retorna a configuração apropriada de tabelas baseada no tipo de banco.
    
    Args:
        db_type: Tipo do banco ('postgresql' ou 'bigquery'). Se None, lê de DB_TYPE
        
    Returns:
        Dict com configuração das tabelas
    """
    if db_type is None:
        db_type = os.getenv("DB_TYPE", "postgresql").lower()
    
    if db_type in ["postgresql", "postgres"]:
        # Configuração para PostgreSQL
        schema = os.getenv("POSTGRES_SCHEMA", "mapa_do_bosque")  # Schema correto
        return {
            'pessoas': {
                'schema': schema,
                'table': os.getenv("POSTGRES_TABLE_PESSOAS", "fluxo_de_pessoas"),  # Nome correto com underscore
                'date_col': 'data',  # Ajuste conforme sua tabela real
                'metric_col': 'value',  # Ajuste conforme sua tabela real
                'titulo': 'Fluxo de Pessoas',
                'unidade': 'pessoas',
                'icon': '👥',
                'color': '#1E90FF'
            },
            'veiculos': {
                'schema': schema,
                'table': os.getenv("POSTGRES_TABLE_VEICULOS", "fluxo_de_veiculos"),  # Nome correto com underscore
                'date_col': 'data',  # Ajuste conforme sua tabela real
                'metric_col': 'value',  # Ajuste conforme sua tabela real
                'titulo': 'Fluxo de Veículos',
                'unidade': 'veículos',
                'icon': '🚗',
                'color': '#FF6B6B'
            }
        }
    else:
        # Configuração para BigQuery (mantém a original)
        return {
            'pessoas': {
                'table': 'brief_fluxo_de_pessoas',
                'date_col': 'data_de_entrada',
                'metric_col': 'quantidade_de_registros_de_entrada',
                'titulo': 'Fluxo de Pessoas',
                'unidade': 'pessoas',
                'icon': '👥',
                'color': '#1E90FF'
            },
            'veiculos': {
                'table': 'brief_fluxo_de_veiculos',
                'date_col': 'data_fluxo',
                'metric_col': 'entradas_veiculos',
                'titulo': 'Fluxo de Veículos',
                'unidade': 'veículos',
                'icon': '🚗',
                'color': '#FF6B6B'
            }
        }


def fetch_data_generic(client, config, year_filter=None, shopping_filter=None):
    """
    Função genérica para buscar dados usando qualquer cliente.
    
    Args:
        client: BigQueryClient ou PostgreSQLClient
        config: Dicionário com configuração da tabela
        year_filter: Filtro opcional de ano
        shopping_filter: Filtro opcional de shopping
        
    Returns:
        DataFrame com os dados
    """
    db_type = os.getenv("DB_TYPE", "postgresql").lower()
    
    if db_type in ["postgresql", "postgres"]:
        # Para PostgreSQL
        df = client.fetch_wbr_data(
            schema=config.get('schema'),
            table=config['table'],
            date_col=config['date_col'],
            metric_col=config['metric_col'],
            shopping_col=config.get('shopping_col')
        )
    else:
        # Para BigQuery
        df = client.fetch_wbr_data(
            project_id=os.getenv("BIGQUERY_PROJECT_ID"),
            dataset=os.getenv("BIGQUERY_DATASET"),
            table=config['table'],
            date_col=config['date_col'],
            metric_col=config['metric_col'],
            shopping_col=config.get('shopping_col')
        )
    
    # Aplicar filtros se necessário
    if year_filter:
        df = df[df['date'].dt.year == year_filter]
    
    if shopping_filter and 'shopping' in df.columns:
        df = df[df['shopping'].str.contains(shopping_filter, case=False, na=False)]
    
    return df