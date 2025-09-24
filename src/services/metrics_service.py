"""
Serviço de métricas - Cálculo de KPIs e métricas
"""
from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st
from src.core.wbr_metrics import calcular_kpis
from src.core.wbr import calcular_metricas_wbr


class MetricsService:
    """Serviço para cálculo de métricas e KPIs"""

    @staticmethod
    def calculate_kpis(
        df: pd.DataFrame,
        data_referencia: pd.Timestamp
    ) -> Dict[str, Any]:
        """
        Calcula KPIs principais

        Args:
            df: DataFrame com os dados
            data_referencia: Data de referência para cálculos

        Returns:
            Dicionário com KPIs calculados
        """
        if df is None or df.empty:
            return {
                'yoy_pct': 0,
                'yoy_abs': 0,
                'wow_pct': 0,
                'wow_abs': 0,
                'mtd_atual': 0,
                'mtd_pct': 0
            }

        try:
            return calcular_kpis(df, data_referencia=data_referencia)
        except Exception as e:
            st.error(f"Erro ao calcular KPIs: {str(e)}")
            return {
                'yoy_pct': 0,
                'yoy_abs': 0,
                'wow_pct': 0,
                'wow_abs': 0,
                'mtd_atual': 0,
                'mtd_pct': 0
            }

    @staticmethod
    def calculate_advanced_metrics(
        df: pd.DataFrame,
        data_referencia: pd.Timestamp,
        metricas_derivadas: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calcula métricas WBR avançadas

        Args:
            df: DataFrame com os dados
            data_referencia: Data de referência
            metricas_derivadas: Métricas derivadas customizadas

        Returns:
            Dicionário com métricas avançadas
        """
        if df is None or df.empty:
            return {'success': False, 'error': 'Sem dados para análise'}

        try:
            return calcular_metricas_wbr(
                df,
                data_referencia=data_referencia,
                coluna_data='date',
                coluna_metrica='metric_value',
                metricas_derivadas=metricas_derivadas
            )
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def render_metrics_display(
        df: pd.DataFrame,
        titulo: str,
        data_referencia: pd.Timestamp
    ):
        """
        Renderiza display de métricas

        Args:
            df: DataFrame com os dados
            titulo: Título das métricas
            data_referencia: Data de referência
        """
        if df is None or df.empty:
            st.warning(f"Sem dados para calcular KPIs de {titulo}")
            return

        try:
            kpis = calcular_kpis(df, data_referencia=data_referencia)

            # Usar 2 colunas para métricas em layout mais compacto
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
                st.metric(
                    label="📌 Média",
                    value=f"{df['metric_value'].mean():,.0f}",
                    help="Média do período"
                )
        except Exception as e:
            st.error(f"Erro ao calcular KPIs: {str(e)}")