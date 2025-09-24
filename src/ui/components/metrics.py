"""
Componente de exibição de métricas
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.services.metrics_service import MetricsService


class MetricsComponent:
    """Componente para exibição de métricas e KPIs"""

    def __init__(self):
        self.metrics_service = MetricsService()

    def render_metrics(
        self,
        df: pd.DataFrame,
        titulo: str,
        data_referencia: pd.Timestamp
    ):
        """
        Renderiza métricas KPI para um dataframe

        Args:
            df: DataFrame com os dados
            titulo: Título das métricas
            data_referencia: Data de referência para cálculos
        """
        if df is None or df.empty:
            st.warning(f"Sem dados para calcular KPIs de {titulo}")
            return

        # Calcula KPIs
        kpis = self.metrics_service.calculate_kpis(df, data_referencia)

        # Renderiza em 2 colunas
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="📈 YoY",
                value=f"{kpis.get('yoy_pct', 0):.1f}%",
                delta=f"{kpis.get('yoy_abs', 0):,.0f}",
                help="Comparação Year-over-Year"
            )
            st.metric(
                label="📅 MTD",
                value=f"{kpis.get('mtd_atual', 0):,.0f}",
                delta=f"{kpis.get('mtd_pct', 0):.1f}%",
                help="Month-to-Date"
            )

        with col2:
            st.metric(
                label="📊 WoW",
                value=f"{kpis.get('wow_pct', 0):.1f}%",
                delta=f"{kpis.get('wow_abs', 0):,.0f}",
                help="Comparação Week-over-Week"
            )
            if 'metric_value' in df.columns:
                st.metric(
                    label="📌 Média",
                    value=f"{df['metric_value'].mean():,.0f}",
                    help="Média do período"
                )

    def render_instagram_metrics(self, df_engagement: pd.DataFrame, metric_type: str):
        """
        Renderiza métricas específicas do Instagram

        Args:
            df_engagement: DataFrame com dados de engajamento
            metric_type: Tipo de métrica (alcance, impressoes, likes, etc)
        """
        if df_engagement.empty:
            st.info(f"Sem dados de {metric_type} disponíveis")
            return

        # Mapeamento de colunas por tipo de métrica
        metric_columns = {
            'alcance': 'total_alcance',
            'impressoes': 'total_impressoes',
            'engajamento': 'engajamento_total',
            'likes': 'total_likes',
            'comentarios': 'total_comentarios',
            'compartilhamentos': 'total_compartilhamentos',
            'salvamentos': 'total_salvos'
        }

        metric_col = metric_columns.get(metric_type)
        if not metric_col or metric_col not in df_engagement.columns:
            return

        # Calcula métricas
        total = df_engagement[metric_col].sum()
        media_diaria = df_engagement[metric_col].mean()
        total_posts = df_engagement['total_posts'].sum() if 'total_posts' in df_engagement.columns else 1
        media_por_post = total / max(total_posts, 1)

        # Renderiza métricas em 3 colunas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(f"Total de {metric_type.title()}", f"{total:,.0f}")

        with col2:
            st.metric("Média por Dia", f"{media_diaria:,.0f}")

        with col3:
            st.metric("Média por Post", f"{media_por_post:,.0f}")

    def render_advanced_metrics(
        self,
        df: pd.DataFrame,
        data_referencia: pd.Timestamp,
        titulo: str = "Análise WBR Avançada"
    ):
        """
        Renderiza métricas WBR avançadas

        Args:
            df: DataFrame com os dados
            data_referencia: Data de referência
            titulo: Título da seção
        """
        if df is None or df.empty:
            st.info("Carregue dados primeiro para ver as métricas WBR avançadas")
            return

        st.subheader(f"{titulo} - Análise WOW/YOY")

        # Calcula métricas avançadas
        metricas_derivadas = None
        if 'metric_value' in df.columns:
            metricas_derivadas = {
                'taxa_crescimento': {
                    'type': 'division',
                    'numerator': 'metric_value',
                    'denominator': 'metric_value',
                    'description': 'Taxa de crescimento relativa'
                }
            }

        metrics_result = self.metrics_service.calculate_advanced_metrics(
            df,
            data_referencia,
            metricas_derivadas
        )

        if metrics_result.get('success'):
            # Exibe comparações
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Métricas Analisadas",
                    metrics_result.get('metrics_analyzed', 0)
                )

            with col2:
                summary = metrics_result.get('summary', [])
                if summary:
                    avg_wow = sum(s.get('WOW_%', 0) or 0 for s in summary) / len(summary)
                    st.metric(
                        "WOW Médio",
                        f"{avg_wow:.1f}%",
                        delta=f"{avg_wow:.1f}%"
                    )

            with col3:
                if summary:
                    avg_yoy = sum(s.get('YOY_%', 0) or 0 for s in summary) / len(summary)
                    st.metric(
                        "YOY Médio",
                        f"{avg_yoy:.1f}%",
                        delta=f"{avg_yoy:.1f}%"
                    )

            # Mostra tabela resumo
            if summary:
                st.subheader("📈 Resumo de Métricas")
                summary_df = pd.DataFrame(summary)
                st.dataframe(
                    summary_df,
                    width="stretch",
                    hide_index=True
                )

            # Mostra comparação de semanas
            self._render_week_comparison(metrics_result)
        else:
            error_msg = metrics_result.get('error', 'Erro desconhecido')
            st.warning(f"Não foi possível calcular métricas avançadas: {error_msg}")

    def _render_week_comparison(self, metrics_result: Dict[str, Any]):
        """
        Renderiza comparação de semanas anteriores

        Args:
            metrics_result: Resultado do cálculo de métricas
        """
        st.subheader("📅 Comparação de Semanas")
        tab1, tab2 = st.tabs(["Ano Atual", "Ano Anterior"])

        with tab1:
            cy_data = metrics_result.get('trailing_weeks', {}).get('current_year', [])
            if cy_data:
                st.dataframe(pd.DataFrame(cy_data), width="stretch", hide_index=True)
            else:
                st.info("Sem dados do ano atual")

        with tab2:
            py_data = metrics_result.get('trailing_weeks', {}).get('previous_year', [])
            if py_data:
                st.dataframe(pd.DataFrame(py_data), width="stretch", hide_index=True)
            else:
                st.info("Sem dados do ano anterior")