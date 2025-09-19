"""
Queries SQL para métricas do Instagram dos shoppings.
Cada query combina dados dos 3 shoppings (SCIB, SBGP, SBI).
"""

import os
from typing import Optional


class InstagramQueries:
    def get_post_count_query(self, date_start: Optional[str] = None, date_end: Optional[str] = None, shopping_filter: Optional[str] = None) -> str:
        """
        Query para contar a quantidade de posts por shopping e data.
        Args:
            date_start: Data inicial (YYYY-MM-DD)
            date_end: Data final (YYYY-MM-DD)
            shopping_filter: Filtro de shopping específico (SCIB, SBGP, SBI) ou None para todos
        Returns:
            Query SQL para contagem de posts
        """

        # Filtro de shopping
        shopping_where = ""
        if shopping_filter:
            shopping_where = f"AND SHOPPING = '{shopping_filter}'"

        query = f"""
        SELECT
            SHOPPING,
            DATA,
            value
        FROM (
            SELECT
                'SCIB' AS SHOPPING,
                DATE("postedAt") AS DATA,
                COUNT(DISTINCT id) AS value
            FROM "{self.schemas['SCIB']}"."Post"
            WHERE
                {{{{date_filter}}}}
            GROUP BY DATE("postedAt")

            UNION ALL

            SELECT
                'SBGP' AS SHOPPING,
                DATE("postedAt") AS DATA,
                COUNT(DISTINCT id) AS value
            FROM "{self.schemas['SBGP']}"."Post"
            WHERE
                {{{{date_filter}}}}
            GROUP BY DATE("postedAt")

            UNION ALL

            SELECT
                'SBI' AS SHOPPING,
                DATE("postedAt") AS DATA,
                COUNT(DISTINCT id) AS value
            FROM "{self.schemas['SBI']}"."Post"
            WHERE
                {{{{date_filter}}}}
            GROUP BY DATE("postedAt")
        ) AS combined_data
        WHERE 1 = 1
        {shopping_where}
        ORDER BY DATA DESC, SHOPPING
        """
        return query
    """Gerencia queries SQL para dados do Instagram"""

    def __init__(self):
        """Inicializa com os schemas dos shoppings"""
        self.schemas = {
            'SCIB': os.getenv("SUPABASE_SCHEMA_1", "instagram-data-fetch-scib"),
            'SBGP': os.getenv("SUPABASE_SCHEMA_2", "instagram-data-fetch-sbgp"),
            'SBI': os.getenv("SUPABASE_SCHEMA_3", "instagram-data-fetch-sbi")
        }

    def get_engagement_query(self, date_start: Optional[str] = None, date_end: Optional[str] = None, shopping_filter: Optional[str] = None) -> str:
        """
        Query para métricas de engajamento (likes, comentários, compartilhamentos, salvamentos).
        Esta query pode ser usada para:
        - Gráfico de Engajamento Total
        - Gráfico de Likes
        - Gráfico de Compartilhamentos
        - Gráfico de Salvamentos

        Args:
            date_start: Data inicial (YYYY-MM-DD)
            date_end: Data final (YYYY-MM-DD)
            shopping_filter: Filtro de shopping específico (SCIB, SBGP, SBI) ou None para todos

        Returns:
            Query SQL combinando dados dos 3 shoppings
        """

        # Filtro de shopping
        shopping_where = ""
        if shopping_filter:
            shopping_where = f"AND shopping = '{shopping_filter}'"

        query = f"""
        SELECT
            shopping,
            data,
            SUM(likes) as total_likes,
            SUM(comments) as total_comentarios,
            SUM(shares) as total_compartilhamentos,
            SUM(saved) as total_salvos,
            SUM(likes + comments + shares + saved) as engajamento_total,
            COUNT(*) as total_posts
        FROM (
            SELECT
                'SCIB' as shopping,
                DATE(P."postedAt") as data,
                I.likes,
                I.comments,
                I.shares,
                I.saved
            FROM "{self.schemas['SCIB']}"."Post" as P
            JOIN "{self.schemas['SCIB']}"."PostInsight" as I ON P.id = I."postId"
            WHERE
                {{{{date_filter_with_alias}}}}

            UNION ALL

            SELECT
                'SBGP' as shopping,
                DATE(P."postedAt") as data,
                I.likes,
                I.comments,
                I.shares,
                I.saved
            FROM "{self.schemas['SBGP']}"."Post" as P
            JOIN "{self.schemas['SBGP']}"."PostInsight" as I ON P.id = I."postId"
            WHERE
                {{{{date_filter_with_alias}}}}

            UNION ALL

            SELECT
                'SBI' as shopping,
                DATE(P."postedAt") as data,
                I.likes,
                I.comments,
                I.shares,
                I.saved
            FROM "{self.schemas['SBI']}"."Post" as P
            JOIN "{self.schemas['SBI']}"."PostInsight" as I ON P.id = I."postId"
            WHERE
                {{{{date_filter_with_alias}}}}
        ) as combined_data
        WHERE 1 = 1
        {shopping_where}
        GROUP BY shopping, data
        ORDER BY data DESC, shopping
        """

        return query
