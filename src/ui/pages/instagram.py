"""
Página de métricas do Instagram
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.services.instagram_service import InstagramService
from src.ui.components.charts import ChartComponent
from src.ui.components.metrics import MetricsComponent
from src.ui.components.data_preview import DataPreviewComponent


class InstagramPage:
    """Página de métricas do Instagram"""

    def __init__(self):
        self.instagram_service = InstagramService()
        self.chart_component = ChartComponent()
        self.metrics_component = MetricsComponent()
        self.data_preview = DataPreviewComponent()

    def render(self, filters: Dict[str, Any]):
        """
        Renderiza página de métricas do Instagram

        Args:
            filters: Filtros selecionados na sidebar
        """
        st.header("📱 Métricas do Instagram")

        # Verifica conexão com Supabase
        if not self.instagram_service.is_connected():
            st.warning("⚠️ Conexão com Supabase não disponível")
            st.info("Configure SUPABASE_DATABASE_URL no arquivo .env")
            return

        # Prepara filtros de data
        date_start = filters.get('data_inicio').strftime('%Y-%m-%d')
        date_end = filters.get('data_fim').strftime('%Y-%m-%d')
        shopping_filter = filters.get('shopping')

        # Carrega dados
        with st.spinner('Carregando dados do Instagram...'):
            df_engagement = self.instagram_service.load_engagement_data(
                date_start,
                date_end,
                shopping_filter
            )
            df_post_count = self.instagram_service.load_post_count_data(
                date_start,
                date_end,
                shopping_filter
            )

        if df_engagement.empty and df_post_count.empty:
            st.warning("Sem dados do Instagram disponíveis para o período selecionado")
            return

        # Cria abas para diferentes métricas
        tabs = st.tabs([
            "👁️ Impressões",
            "📈 Alcance",
            "📊 Engajamento Total",
            "❤️ Likes",
            "💬 Comentários",
            "🔄 Compartilhamentos",
            "💾 Salvamentos",
            "📝 Posts Publicados"
        ])

        # Renderiza cada aba
        with tabs[0]:  # Impressões
            self._render_metric_tab(
                df_engagement,
                'total_impressoes',
                'Impressões',
                'Quantidade de Impressões',
                filters
            )

        with tabs[1]:  # Alcance
            self._render_metric_tab(
                df_engagement,
                'total_alcance',
                'Alcance',
                'Pessoas Alcançadas',
                filters
            )

        with tabs[2]:  # Engajamento Total
            self._render_engagement_tab(df_engagement, filters)

        with tabs[3]:  # Likes
            self._render_metric_tab(
                df_engagement,
                'total_likes',
                'Likes',
                'Quantidade de Likes',
                filters
            )

        with tabs[4]:  # Comentários
            self._render_metric_tab(
                df_engagement,
                'total_comentarios',
                'Comentários',
                'Quantidade de Comentários',
                filters
            )

        with tabs[5]:  # Compartilhamentos
            self._render_metric_tab(
                df_engagement,
                'total_compartilhamentos',
                'Compartilhamentos',
                'Quantidade de Compartilhamentos',
                filters
            )

        with tabs[6]:  # Salvamentos
            self._render_metric_tab(
                df_engagement,
                'total_salvos',
                'Salvamentos',
                'Quantidade de Salvamentos',
                filters
            )

        with tabs[7]:  # Posts Publicados
            self._render_posts_tab(df_post_count, filters)

    def _render_metric_tab(
        self,
        df: pd.DataFrame,
        metric_col: str,
        metric_name: str,
        y_label: str,
        filters: Dict[str, Any]
    ):
        """
        Renderiza aba de métrica específica

        Args:
            df: DataFrame com os dados
            metric_col: Coluna da métrica
            metric_name: Nome da métrica
            y_label: Label do eixo Y
            filters: Filtros aplicados
        """
        if df.empty or metric_col not in df.columns:
            st.info(f"Sem dados de {metric_name.lower()} disponíveis")
            return

        # Renderiza gráfico
        self.chart_component.render_instagram_chart(
            df,
            metric_col,
            f'Total de {metric_name} por Dia',
            y_label,
            filters.get('data_referencia'),
            filters.get('shopping'),
            filters.get('metodo_semana', 'iso')
        )

        # Renderiza métricas
        self.metrics_component.render_instagram_metrics(
            df,
            metric_name.lower()
        )

    def _render_engagement_tab(self, df: pd.DataFrame, filters: Dict[str, Any]):
        """
        Renderiza aba de engajamento total

        Args:
            df: DataFrame com dados de engajamento
            filters: Filtros aplicados
        """
        if df.empty:
            st.info("Sem dados de engajamento disponíveis")
            return

        # Renderiza gráfico
        self.chart_component.render_instagram_chart(
            df,
            'engajamento_total',
            'Engajamento Total por Dia',
            'Total de Interações',
            filters.get('data_referencia'),
            filters.get('shopping'),
            filters.get('metodo_semana', 'iso')
        )

        # Métricas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total = df['engajamento_total'].sum() if 'engajamento_total' in df.columns else 0
            st.metric("Total", f"{total:,.0f}")

        with col2:
            media = df['engajamento_total'].mean() if 'engajamento_total' in df.columns else 0
            st.metric("Média Diária", f"{media:,.0f}")

        with col3:
            maximo = df['engajamento_total'].max() if 'engajamento_total' in df.columns else 0
            st.metric("Máximo", f"{maximo:,.0f}")

        with col4:
            posts = df['total_posts'].sum() if 'total_posts' in df.columns else 0
            st.metric("Posts", f"{posts:,.0f}")

        # Exibir dados brutos
        self.data_preview.render_instagram_raw_data(df)

    def _render_posts_tab(self, df: pd.DataFrame, filters: Dict[str, Any]):
        """
        Renderiza aba de posts publicados

        Args:
            df: DataFrame com contagem de posts
            filters: Filtros aplicados
        """
        if df.empty:
            st.info("Sem dados de posts disponíveis")
            return

        # Renderiza gráfico
        self.chart_component.render_instagram_chart(
            df,
            'total_posts',
            'Quantidade de Posts Publicados',
            'Número de Posts',
            filters.get('data_referencia'),
            filters.get('shopping'),
            filters.get('metodo_semana', 'iso')
        )

        # Métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            total_posts = df['total_posts'].sum() if 'total_posts' in df.columns else 0
            st.metric("Total de Posts", f"{total_posts:,.0f}")

        with col2:
            media_posts = df['total_posts'].mean() if 'total_posts' in df.columns else 0
            st.metric("Média por Dia", f"{media_posts:,.1f}")

        with col3:
            if 'data' in df.columns and len(df) > 0:
                days = (df['data'].max() - df['data'].min()).days + 1
                st.metric("Período (dias)", f"{days}")
            else:
                st.metric("Período (dias)", "0")