"""
Componente de visualização de dados brutos
"""
import streamlit as st
import pandas as pd
from typing import Optional


class DataPreviewComponent:
    """Componente para visualização de dados brutos"""

    def render_data_preview(
        self,
        df: pd.DataFrame,
        title: str = "📋 Ver dados brutos",
        max_rows: int = 30
    ):
        """
        Renderiza prévia dos dados em formato expansível

        Args:
            df: DataFrame com os dados
            title: Título do expander
            max_rows: Número máximo de linhas a exibir
        """
        if df is None or df.empty:
            return

        with st.expander(title):
            self._format_and_display(df, max_rows)

    def _format_and_display(
        self,
        df: pd.DataFrame,
        max_rows: int = 30
    ):
        """
        Formata e exibe o DataFrame

        Args:
            df: DataFrame a ser exibido
            max_rows: Número máximo de linhas
        """
        # Cria cópia para não modificar original
        display_df = df.copy()

        # Se 'date' for o índice, reseta
        if display_df.index.name == 'date' or isinstance(display_df.index, pd.DatetimeIndex):
            display_df = display_df.reset_index()

        # Formata colunas de data
        for col in display_df.columns:
            if 'date' in col.lower() or 'data' in col.lower():
                try:
                    display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%d/%m/%Y')
                except:
                    pass

        # Formata colunas numéricas
        numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if 'value' in col.lower() or 'total' in col.lower():
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")

        # Exibe DataFrame
        st.dataframe(
            display_df.head(max_rows),
            width="stretch",
            hide_index=True
        )

        # Mostra informação sobre o total de linhas
        total_rows = len(df)
        if total_rows > max_rows:
            st.caption(f"Mostrando {max_rows} de {total_rows} linhas")

    def render_instagram_raw_data(
        self,
        df: pd.DataFrame,
        title: str = "🔎 Ver dados brutos do Instagram"
    ):
        """
        Renderiza dados brutos específicos do Instagram

        Args:
            df: DataFrame com dados do Instagram
            title: Título do expander
        """
        if df.empty:
            return

        with st.expander(title):
            # Formata especificamente para dados do Instagram
            display_df = df.copy()

            # Ordena por data (mais recente primeiro)
            if 'data' in display_df.columns:
                display_df = display_df.sort_values('data', ascending=False)

            # Formata colunas
            if 'data' in display_df.columns:
                display_df['data'] = pd.to_datetime(display_df['data']).dt.strftime('%d/%m/%Y')

            # Lista de colunas de métricas do Instagram
            instagram_metrics = [
                'total_alcance', 'total_impressoes', 'engajamento_total',
                'total_likes', 'total_comentarios', 'total_compartilhamentos',
                'total_salvos', 'total_posts'
            ]

            # Formata métricas
            for col in instagram_metrics:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")

            # Reordena colunas para melhor visualização
            priority_cols = ['shopping', 'data'] if 'shopping' in display_df.columns else ['data']
            other_cols = [col for col in display_df.columns if col not in priority_cols]
            display_df = display_df[priority_cols + other_cols]

            st.dataframe(
                display_df.head(30),
                width="stretch",
                hide_index=True
            )