"""
Cliente PostgreSQL específico para conexão com Supabase
Usa SQLAlchemy para conectar diretamente ao banco do Supabase
"""

import os
import pandas as pd
import logging
from sqlalchemy import create_engine, text
from typing import Optional, Dict, Any
from ..sql.instagram_queries import InstagramQueries

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

        # Inicializa o gerenciador de queries
        self.instagram_queries = InstagramQueries()

        logger.info("Supabase PostgreSQL client initialized")

    def query(self, sql_query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Executa uma query SQL e retorna DataFrame
        Substitui placeholders de data para manter compatibilidade com WBR

        Args:
            sql_query: Query SQL para executar
            params: Parâmetros para a query

        Returns:
            DataFrame com resultados
        """
        try:
            # Substitui placeholders de data se existirem
            # Corrigido para usar desde o primeiro dia do ano anterior até hoje
            if '{{date_filter}}' in sql_query:
                date_filter = """
                DATE("postedAt") BETWEEN
                    DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')
                    AND CURRENT_DATE
                """
                sql_query = sql_query.replace('{{date_filter}}', date_filter)

            if '{{date_filter_with_alias}}' in sql_query:
                date_filter_with_alias = """
                DATE(P."postedAt") BETWEEN
                    DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')
                    AND CURRENT_DATE
                """
                sql_query = sql_query.replace('{{date_filter_with_alias}}', date_filter_with_alias)

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

    def get_engagement_data_using_queries(self, date_start: Optional[str] = None,
                           date_end: Optional[str] = None,
                           shopping_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Busca dados de engajamento do Instagram usando InstagramQueries

        Args:
            date_start: Data inicial (YYYY-MM-DD) - usado via placeholders na query
            date_end: Data final (YYYY-MM-DD) - usado via placeholders na query
            shopping_filter: Filtro de shopping específico

        Returns:
            DataFrame com dados de engajamento
        """
        # Usa a query do InstagramQueries com placeholders
        query = self.instagram_queries.get_engagement_query(
            date_start=date_start,
            date_end=date_end,
            shopping_filter=shopping_filter
        )

        return self.query(query)

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

        # Constrói WHERE clause - usa parâmetros de data quando fornecidos
        if date_start and date_end:
            # Usa o período específico solicitado pela aplicação
            where_clause = f"""
                DATE(p."postedAt") BETWEEN '{date_start}' AND '{date_end}'
            """
        else:
            # Fallback: dados desde o primeiro dia do ano anterior até hoje
            # (corrigido para atender a especificação do usuário)
            where_clause = """
                DATE(p."postedAt") BETWEEN
                    DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')
                    AND CURRENT_DATE
            """
        params = {}

        # Query com UNION ALL para todos os shoppings
        query = f"""
        WITH all_data AS (
            SELECT
                'SCIB' as shopping,
                DATE(p."postedAt") as data,
                COALESCE(SUM(i.likes), 0) as total_likes,
                COALESCE(SUM(i.reach),0) as total_alcance,
                COALESCE(SUM(i.impressions),0) as total_impressoes,
                COALESCE(SUM(i.comments), 0) as total_comentarios,
                COALESCE(SUM(i.shares), 0) as total_compartilhamentos,
                COALESCE(SUM(i.saved), 0) as total_salvos,
                COUNT(DISTINCT p.id) as total_posts
            FROM "{self.schemas['SCIB']}"."Post" p
            LEFT JOIN "{self.schemas['SCIB']}"."PostInsight" i ON p.id = i."postId"
            WHERE {where_clause}
            GROUP BY DATE(p."postedAt")

            UNION ALL

            SELECT
                'SBGP' as shopping,
                DATE(p."postedAt") as data,
                COALESCE(SUM(i.likes), 0) as total_likes,
                COALESCE(SUM(i.reach),0) as total_alcance,
                COALESCE(SUM(i.impressions),0) as total_impressoes,
                COALESCE(SUM(i.comments), 0) as total_comentarios,
                COALESCE(SUM(i.shares), 0) as total_compartilhamentos,
                COALESCE(SUM(i.saved), 0) as total_salvos,
                COUNT(DISTINCT p.id) as total_posts
            FROM "{self.schemas['SBGP']}"."Post" p
            LEFT JOIN "{self.schemas['SBGP']}"."PostInsight" i ON p.id = i."postId"
            WHERE {where_clause}
            GROUP BY DATE(p."postedAt")

            UNION ALL

            SELECT
                'SBI' as shopping,
                DATE(p."postedAt") as data,
                COALESCE(SUM(i.likes), 0) as total_likes,
                COALESCE(SUM(i.reach),0) as total_alcance,
                COALESCE(SUM(i.impressions),0) as total_impressoes,
                COALESCE(SUM(i.comments), 0) as total_comentarios,
                COALESCE(SUM(i.shares), 0) as total_compartilhamentos,
                COALESCE(SUM(i.saved), 0) as total_salvos,
                COUNT(DISTINCT p.id) as total_posts
            FROM "{self.schemas['SBI']}"."Post" p
            LEFT JOIN "{self.schemas['SBI']}"."PostInsight" i ON p.id = i."postId"
            WHERE {where_clause}
            GROUP BY DATE(p."postedAt")
        )
        SELECT
            shopping,
            data,
            total_likes,
            total_alcance,
            total_impressoes,
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
        Busca contagem de posts por dia usando InstagramQueries

        Args:
            date_start: Data inicial (YYYY-MM-DD) - usado via placeholders na query
            date_end: Data final (YYYY-MM-DD) - usado via placeholders na query
            shopping_filter: Filtro de shopping específico

        Returns:
            DataFrame com contagem de posts
        """
        # Usa a query do InstagramQueries com placeholders
        query = self.instagram_queries.get_post_count_query(
            date_start=date_start,
            date_end=date_end,
            shopping_filter=shopping_filter
        )

        return self.query(query)

    def fetch_wbr_data(self, *, table_name: str, date_col: str = 'data',
                       metric_col: str = 'value', shopping_col: Optional[str] = 'shopping') -> pd.DataFrame:
        """
        Busca dados WBR das tabelas principais (fluxo de pessoas, veículos, vendas).

        Args:
            table_name: Nome da tabela com schema (ex: "mapa-do-bosque.fluxo_de_pessoas")
            date_col: Nome da coluna de data
            metric_col: Nome da coluna de métrica
            shopping_col: Nome da coluna de shopping (opcional)

        Returns:
            DataFrame com colunas padronizadas: date, metric_value, shopping (se houver)
        """
        try:
            # Monta query básica
            select_cols = [f"{date_col} as date", f"{metric_col} as metric_value"]
            if shopping_col:
                select_cols.append(f"{shopping_col} as shopping")

            query = f"""
            SELECT {', '.join(select_cols)}
            FROM "{table_name.replace('.', '"."')}"
            WHERE {date_col} IS NOT NULL
            ORDER BY {date_col} DESC
            """

            # Executa query
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)

            # Converte coluna de data para datetime
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            logger.info(f"Fetched {len(df)} rows from {table_name}")
            return df

        except Exception as e:
            logger.error(f"Erro ao buscar dados de {table_name}: {str(e)}")
            return pd.DataFrame()

    def test_connection(self) -> bool:
        """Testa a conexão com o banco"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {str(e)}")
            return False