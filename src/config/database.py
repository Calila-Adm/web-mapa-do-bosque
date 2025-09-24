"""
Configurações de banco de dados - Supabase e PostgreSQL
"""
from typing import Dict, Any, Optional
import os


def get_supabase_config() -> Dict[str, Any]:
    """Retorna configurações do Supabase"""
    return {
        'url': os.getenv('SUPABASE_DATABASE_URL'),
        'schema': os.getenv('SUPABASE_SCHEMA_MAPA', 'mapa_do_bosque'),
        'tables': get_table_config()
    }


def get_postgresql_config() -> Dict[str, Any]:
    """Retorna configurações do PostgreSQL para migração"""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DATABASE'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'url': os.getenv('DATABASE_URL')
    }


def get_table_config() -> Dict[str, Dict[str, Any]]:
    """Retorna configuração das tabelas principais"""
    schema = os.getenv('SUPABASE_SCHEMA_MAPA', 'mapa_do_bosque')

    return {
        'pessoas': {
            'table': os.getenv("SUPABASE_TABLE_PESSOAS", "fluxo_de_pessoas"),
            'schema': schema,
            'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
            'metric_col': os.getenv("SUPABASE_METRIC_COL", "value"),
            'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
            'titulo': 'Fluxo de Pessoas',
            'icon': '👥',
            'unidade': 'pessoas'
        },
        'veiculos': {
            'table': os.getenv("SUPABASE_TABLE_VEICULOS", "fluxo_de_veiculos"),
            'schema': schema,
            'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
            'metric_col': os.getenv("SUPABASE_METRIC_COL", "value"),
            'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
            'titulo': 'Fluxo de Veículos',
            'icon': '🚗',
            'unidade': 'veículos'
        },
        'vendas': {
            'table': os.getenv("SUPABASE_TABLE_VENDAS", "vendas_gshop"),
            'schema': schema,
            'date_col': os.getenv("SUPABASE_DATE_COL", "data"),
            'metric_col': os.getenv("SUPABASE_METRIC_COL", "value"),
            'shopping_col': os.getenv("SUPABASE_SHOPPING_COL", "shopping"),
            'titulo': 'Vendas',
            'icon': '💰',
            'unidade': 'R$'
        }
    }


def get_instagram_config() -> Dict[str, Any]:
    """Retorna configuração das tabelas do Instagram"""
    return {
        'engagement': 'instagram_metrics_engagement',
        'posts': 'instagram_metrics_posts',
        'schema': 'public'
    }


def get_database_type() -> str:
    """Retorna o tipo de banco de dados configurado"""
    db_type = os.getenv("DB_TYPE", "supabase").lower()

    # Normaliza valores para suportar apenas Supabase e PostgreSQL
    if db_type in ["supabase", "postgresql", "postgres"]:
        return db_type

    # Default para Supabase se tipo inválido
    return "supabase"


def validate_database_config() -> tuple[bool, Optional[str]]:
    """
    Valida se as configurações de banco de dados estão corretas

    Returns:
        tuple[bool, Optional[str]]: (válido, mensagem_erro)
    """
    db_type = get_database_type()

    if db_type == "supabase":
        if not os.getenv("SUPABASE_DATABASE_URL"):
            return False, "SUPABASE_DATABASE_URL não configurada"

    elif db_type in ["postgresql", "postgres"]:
        # Verifica se tem URL ou configurações individuais
        has_url = bool(os.getenv("DATABASE_URL"))
        has_individual = bool(
            os.getenv("POSTGRES_DATABASE") and
            os.getenv("POSTGRES_USER")
        )

        if not (has_url or has_individual):
            return False, "Configurações do PostgreSQL incompletas"

    return True, None