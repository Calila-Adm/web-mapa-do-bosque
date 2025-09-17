"""
Cliente PostgreSQL específico para conexão com Supabase
Usa SQLAlchemy para conectar diretamente ao banco do Supabase
"""

import os
import pandas as pd
import logging
from sqlalchemy import create_engine, text
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Cliente para acessar Supabase via PostgreSQL direto"""

    def __init__(self):
        """Inicializa conexão PostgreSQL com Supabase"""

        # Pega a connection string específica do Supabase
        supabase_db_url = os.getenv("SUPABASE_DATABASE_URL")

        if not supabase_db_url:
            raise ValueError(
                "SUPABASE_DATABASE_URL não configurada. "
                "Adicione no .env: SUPABASE_DATABASE_URL=postgresql://..."
            )

        # Cria engine SQLAlchemy
        self.engine = create_engine(
            supabase_db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )

        # Schemas dos shoppings
        self.schemas = {
            'SCIB': os.getenv("SUPABASE_SCHEMA_1", "instagram-data-fetch-scib"),
            'SBGP': os.getenv("SUPABASE_SCHEMA_2", "instagram-data-fetch-sbgp"),
            'SBI': os.getenv("SUPABASE_SCHEMA_3", "instagram-data-fetch-sbi")
        }

        logger.info("Supabase PostgreSQL client initialized")

    def query(self, sql_query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Executa uma query SQL e retorna DataFrame

        Args:
            sql_query: Query SQL para executar
            params: Parâmetros para a query

        Returns:
            DataFrame com resultados
        """
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql_query(
                    text(sql_query),
                    conn,
                    params=params
                )
                logger.info(f"Query retornou {len(result)} registros")
                return result
        except Exception as e:
            logger.error(f"Erro ao executar query: {str(e)}")
            return pd.DataFrame()

    def get_engagement_data(self, date_start: Optional[str] = None,
                           date_end: Optional[str] = None,
                           shopping_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Busca dados de engajamento do Instagram

        Args:
            date_start: Data inicial (YYYY-MM-DD)
            date_end: Data final (YYYY-MM-DD)
            shopping_filter: Filtro de shopping específico

        Returns:
            DataFrame com dados de engajamento
        """

        # Constrói WHERE clause - espelhando a lógica do queries.sql
        # Sempre pega dados dos últimos 2 anos para garantir comparações YoY
        where_clause = """
            DATE(p."createdAt") BETWEEN
                DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '2 years'
                AND CURRENT_DATE
        """
        params = {}

        # Query com UNION ALL para todos os shoppings
        query = f"""
        WITH all_data AS (
            SELECT
                'SCIB' as shopping,
                DATE(p."createdAt") as data,
                COALESCE(SUM(i.likes), 0) as total_likes,
                COALESCE(SUM(i.comments), 0) as total_comentarios,
                COALESCE(SUM(i.shares), 0) as total_compartilhamentos,
                COALESCE(SUM(i.saved), 0) as total_salvos,
                COUNT(DISTINCT p.id) as total_posts
            FROM "{self.schemas['SCIB']}"."Post" p
            LEFT JOIN "{self.schemas['SCIB']}"."PostInsight" i ON p.id = i."postId"
            WHERE {where_clause}
            GROUP BY DATE(p."createdAt")

            UNION ALL

            SELECT
                'SBGP' as shopping,
                DATE(p."createdAt") as data,
                COALESCE(SUM(i.likes), 0) as total_likes,
                COALESCE(SUM(i.comments), 0) as total_comentarios,
                COALESCE(SUM(i.shares), 0) as total_compartilhamentos,
                COALESCE(SUM(i.saved), 0) as total_salvos,
                COUNT(DISTINCT p.id) as total_posts
            FROM "{self.schemas['SBGP']}"."Post" p
            LEFT JOIN "{self.schemas['SBGP']}"."PostInsight" i ON p.id = i."postId"
            WHERE {where_clause}
            GROUP BY DATE(p."createdAt")

            UNION ALL

            SELECT
                'SBI' as shopping,
                DATE(p."createdAt") as data,
                COALESCE(SUM(i.likes), 0) as total_likes,
                COALESCE(SUM(i.comments), 0) as total_comentarios,
                COALESCE(SUM(i.shares), 0) as total_compartilhamentos,
                COALESCE(SUM(i.saved), 0) as total_salvos,
                COUNT(DISTINCT p.id) as total_posts
            FROM "{self.schemas['SBI']}"."Post" p
            LEFT JOIN "{self.schemas['SBI']}"."PostInsight" i ON p.id = i."postId"
            WHERE {where_clause}
            GROUP BY DATE(p."createdAt")
        )
        SELECT
            shopping,
            data,
            total_likes,
            total_comentarios,
            total_compartilhamentos,
            total_salvos,
            (total_likes + total_comentarios + total_compartilhamentos + total_salvos) as engajamento_total,
            total_posts
        FROM all_data
        {f"WHERE shopping = '{shopping_filter}'" if shopping_filter else ""}
        ORDER BY data DESC, shopping
        """

        return self.query(query, params)

    def get_post_count_data(self, date_start: Optional[str] = None,
                           date_end: Optional[str] = None,
                           shopping_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Busca contagem de posts por dia

        Args:
            date_start: Data inicial (YYYY-MM-DD)
            date_end: Data final (YYYY-MM-DD)
            shopping_filter: Filtro de shopping específico

        Returns:
            DataFrame com contagem de posts
        """

        # Constrói WHERE clause - espelhando a lógica do queries.sql
        # Sempre pega dados dos últimos 2 anos para garantir comparações YoY
        where_clause = """
            DATE("createdAt") BETWEEN
                DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '2 years'
                AND CURRENT_DATE
        """
        params = {}

        # Query com UNION ALL
        query = f"""
        WITH all_counts AS (
            SELECT
                'SCIB' as shopping,
                DATE("createdAt") as data,
                COUNT(*) as value
            FROM "{self.schemas['SCIB']}"."Post"
            WHERE {where_clause}
            GROUP BY DATE("createdAt")

            UNION ALL

            SELECT
                'SBGP' as shopping,
                DATE("createdAt") as data,
                COUNT(*) as value
            FROM "{self.schemas['SBGP']}"."Post"
            WHERE {where_clause}
            GROUP BY DATE("createdAt")

            UNION ALL

            SELECT
                'SBI' as shopping,
                DATE("createdAt") as data,
                COUNT(*) as value
            FROM "{self.schemas['SBI']}"."Post"
            WHERE {where_clause}
            GROUP BY DATE("createdAt")
        )
        SELECT shopping, data, value
        FROM all_counts
        {f"WHERE shopping = '{shopping_filter}'" if shopping_filter else ""}
        ORDER BY data DESC, shopping
        """

        return self.query(query, params)

    def test_connection(self) -> bool:
        """Testa a conexão com o banco"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {str(e)}")
            return False