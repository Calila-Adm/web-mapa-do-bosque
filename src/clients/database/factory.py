"""
Factory pattern para criar clientes de banco de dados.
Suporta múltiplas conexões simultâneas.
"""
import os
from typing import Union, Optional, Dict, Any

# Importações condicionais para evitar erros se uma lib não estiver instalada
def get_database_client(client_type: Optional[str] = None):
    """
    Retorna o cliente de banco de dados apropriado.

    Args:
        client_type: Tipo específico de cliente ('postgresql', 'bigquery', 'supabase')
                    Se None, usa DB_TYPE do ambiente

    Returns:
        Cliente de banco de dados solicitado
    """
    if client_type is None:
        client_type = os.getenv("DB_TYPE", "postgresql").lower()
    else:
        client_type = client_type.lower()

    if client_type == "postgresql" or client_type == "postgres":
        try:
            from .postgresql import PostgreSQLClient
            return PostgreSQLClient()
        except ImportError as e:
            raise ImportError(
                "PostgreSQL dependencies not installed. "
                "Run: pip install psycopg2-binary"
            ) from e

    elif client_type == "bigquery":
        try:
            from .bigquery import BigQueryClient
            return BigQueryClient()
        except ImportError as e:
            raise ImportError(
                "BigQuery dependencies not installed. "
                "Run: pip install google-cloud-bigquery google-cloud-bigquery-storage db-dtypes"
            ) from e

    elif client_type == "supabase":
        try:
            from .supabase_postgres import SupabaseClient
            return SupabaseClient()
        except ImportError as e:
            raise ImportError(
                "Supabase dependencies not installed. "
                "Run: pip install sqlalchemy psycopg2-binary"
            ) from e

    else:
        raise ValueError(
            f"Unknown database type: {client_type}. "
            "Valid types: 'postgresql', 'bigquery', 'supabase'"
        )


def get_multiple_clients() -> Dict[str, Any]:
    """
    Retorna múltiplos clientes de banco de dados configurados.

    Returns:
        Dict com clientes disponíveis
    """
    clients = {}

    # Cliente principal baseado em DB_TYPE
    primary_type = os.getenv("DB_TYPE", "postgresql").lower()
    try:
        clients['primary'] = get_database_client(primary_type)
        clients[primary_type] = clients['primary']
    except Exception as e:
        print(f"Warning: Could not initialize primary client ({primary_type}): {e}")

    # Adicionar Supabase se configurado
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
        try:
            clients['supabase'] = get_database_client('supabase')
        except Exception as e:
            print(f"Warning: Could not initialize Supabase client: {e}")

    # Adicionar BigQuery se configurado e não for o principal
    if primary_type != "bigquery" and os.getenv("BIGQUERY_PROJECT_ID"):
        try:
            clients['bigquery'] = get_database_client('bigquery')
        except Exception as e:
            print(f"Warning: Could not initialize BigQuery client: {e}")

    # Adicionar PostgreSQL se configurado e não for o principal
    if primary_type != "postgresql" and (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_HOST")):
        try:
            clients['postgresql'] = get_database_client('postgresql')
        except Exception as e:
            print(f"Warning: Could not initialize PostgreSQL client: {e}")

    return clients


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
            },
            'vendas': {
                'schema': schema,
                'table': os.getenv("POSTGRES_TABLE_VENDAS", "vendas_gshop"),  # Nome correto com underscore
                'date_col': 'data',  # Ajuste conforme sua tabela real
                'metric_col': 'value',  # Ajuste conforme sua tabela real
                'titulo': 'Vendas',
                'unidade': 'R$',
                'icon': '💰',
                'color': '#28A745'
            }
        }
    elif db_type == "supabase":
        # Configuração para Supabase
        return {
            'pessoas': {
                'table': os.getenv("SUPABASE_TABLE_PESSOAS", "fluxo_de_pessoas"),
                'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
                'metric_col': os.getenv("SUPABASE_METRIC_COL", "quantidade"),
                'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
                'titulo': 'Fluxo de Pessoas',
                'unidade': 'pessoas',
                'icon': '👥',
                'color': '#1E90FF'
            },
            'veiculos': {
                'table': os.getenv("SUPABASE_TABLE_VEICULOS", "fluxo_de_veiculos"),
                'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
                'metric_col': os.getenv("SUPABASE_METRIC_COL", "quantidade"),
                'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
                'titulo': 'Fluxo de Veículos',
                'unidade': 'veículos',
                'icon': '🚗',
                'color': '#FF6B6B'
            },
            'vendas': {
                'table': os.getenv("SUPABASE_TABLE_VENDAS", "vendas_gshop"),
                'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
                'metric_col': os.getenv("SUPABASE_METRIC_COL", "valor"),
                'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
                'titulo': 'Vendas',
                'unidade': 'R$',
                'icon': '💰',
                'color': '#28A745'
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
            },
            'vendas': {
                'table': 'brief_vendas_shop',
                'date_col': 'data_venda',
                'metric_col': 'valor_total',
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
    Função genérica para buscar dados usando qualquer cliente.

    Args:
        client: Cliente de banco de dados
        config: Dicionário com configuração da tabela
        year_filter: Filtro opcional de ano
        shopping_filter: Filtro opcional de shopping
        client_type: Tipo do cliente ('postgresql', 'bigquery', 'supabase')

    Returns:
        DataFrame com os dados
    """
    if client_type is None:
        client_type = os.getenv("DB_TYPE", "postgresql").lower()

    if client_type in ["postgresql", "postgres"]:
        # Para PostgreSQL
        df = client.fetch_wbr_data(
            schema=config.get('schema'),
            table=config['table'],
            date_col=config['date_col'],
            metric_col=config['metric_col'],
            shopping_col=config.get('shopping_col')
        )
    elif client_type == "supabase":
        # Para Supabase
        df = client.fetch_wbr_data(
            table_name=config['table'],
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
    if year_filter and 'date' in df.columns:
        df = df[df['date'].dt.year == year_filter]

    if shopping_filter and 'shopping' in df.columns:
        df = df[df['shopping'].str.contains(shopping_filter, case=False, na=False)]

    return df