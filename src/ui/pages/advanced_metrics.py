"""
Página de métricas WBR avançadas
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.services.data_service import DataService
from src.services.filter_service import FilterService
from src.ui.components.metrics import MetricsComponent
from src.config.database import get_table_config


class AdvancedMetricsPage:
    """Página de métricas WBR avançadas"""

    def __init__(self):
        self.data_service = DataService()
        self.filter_service = FilterService()
        self.metrics_component = MetricsComponent()
        self.tables_config = get_table_config()

    def render(self, filters: Dict[str, Any]):
        """
        Renderiza página de métricas avançadas

        Args:
            filters: Filtros selecionados na sidebar
        """
        st.header("📊 Métricas WBR Avançadas")

        # Carrega dados
        data = self._load_data(filters)

        if not data:
            st.warning("Carregue dados primeiro para ver as métricas WBR avançadas")
            return

        # Renderiza análise detalhada
        with st.expander("🔍 Análise Detalhada de Métricas WBR", expanded=True):
            # Cria tabs para cada tipo de dado
            tabs = st.tabs([
                f"{config['icon']} {config['titulo']}"
                for config in self.tables_config.values()
            ])

            # Renderiza métricas para cada tipo
            for idx, (table_name, config) in enumerate(self.tables_config.items()):
                with tabs[idx]:
                    df = data.get(table_name)
                    if df is not None and not df.empty:
                        self.metrics_component.render_advanced_metrics(
                            df,
                            filters.get('data_referencia'),
                            f"{config['titulo']}"
                        )
                    else:
                        st.info(f"Sem dados de {config['titulo'].lower()} para análise")

        # Análise comparativa
        self._render_comparative_analysis(data, filters)

        # Insights e tendências
        self._render_insights(data, filters)

    def _load_data(self, filters: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        Carrega dados para análise

        Args:
            filters: Filtros a serem aplicados

        Returns:
            Dicionário com DataFrames
        """
        data = {}

        with st.spinner("Carregando dados para análise..."):
            for table_name, config in self.tables_config.items():
                df = self.data_service.load_table_data(table_name, config)

                if df is not None:
                    df_filtered = self.filter_service.apply_filters(
                        df,
                        date_start=filters.get('data_inicio'),
                        date_end=filters.get('data_fim'),
                        shopping_filter=filters.get('shopping')
                    )
                    data[table_name] = df_filtered

        return data

    def _render_comparative_analysis(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """
        Renderiza análise comparativa entre métricas

        Args:
            data: Dados carregados
            filters: Filtros aplicados
        """
        st.subheader("📊 Análise Comparativa")

        # Verifica se há dados para comparar
        valid_data = {k: v for k, v in data.items() if v is not None and not v.empty}

        if len(valid_data) < 2:
            st.info("Dados insuficientes para análise comparativa")
            return

        # Cria colunas para comparação
        cols = st.columns(len(valid_data))

        for idx, (table_name, df) in enumerate(valid_data.items()):
            config = self.tables_config[table_name]

            with cols[idx]:
                st.markdown(f"**{config['icon']} {config['titulo']}**")

                if 'metric_value' in df.columns:
                    # Estatísticas básicas
                    st.metric("Média", f"{df['metric_value'].mean():,.0f}")
                    st.metric("Mediana", f"{df['metric_value'].median():,.0f}")
                    st.metric("Desvio Padrão", f"{df['metric_value'].std():,.0f}")

                    # Tendência
                    if len(df) > 1:
                        first_value = df['metric_value'].iloc[0]
                        last_value = df['metric_value'].iloc[-1]
                        change = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
                        st.metric(
                            "Variação Total",
                            f"{change:+.1f}%",
                            delta=f"{last_value - first_value:,.0f}"
                        )

    def _render_insights(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """
        Renderiza insights e tendências

        Args:
            data: Dados carregados
            filters: Filtros aplicados
        """
        st.subheader("💡 Insights e Tendências")

        insights = []

        for table_name, df in data.items():
            if df is None or df.empty:
                continue

            config = self.tables_config[table_name]

            if 'metric_value' in df.columns:
                # Análise de tendência
                mean_value = df['metric_value'].mean()
                max_value = df['metric_value'].max()
                min_value = df['metric_value'].min()

                # Identifica dia da semana com maior movimento
                if 'date' in df.columns:
                    df['weekday'] = pd.to_datetime(df['date']).dt.day_name()
                    best_day = df.groupby('weekday')['metric_value'].mean().idxmax()

                    insights.append(
                        f"• **{config['titulo']}**: Maior movimento às {self._translate_weekday(best_day)}s "
                        f"(média: {df[df['weekday'] == best_day]['metric_value'].mean():,.0f})"
                    )

                # Identifica outliers
                std = df['metric_value'].std()
                outliers = df[df['metric_value'] > mean_value + 2 * std]
                if len(outliers) > 0:
                    insights.append(
                        f"• **{config['titulo']}**: {len(outliers)} dias com valores excepcionais "
                        f"(acima de {mean_value + 2 * std:,.0f})"
                    )

        # Exibe insights
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.info("Sem insights disponíveis para o período selecionado")

    def _translate_weekday(self, weekday: str) -> str:
        """
        Traduz dia da semana para português

        Args:
            weekday: Dia em inglês

        Returns:
            Dia em português
        """
        translation = {
            'Monday': 'segunda-feira',
            'Tuesday': 'terça-feira',
            'Wednesday': 'quarta-feira',
            'Thursday': 'quinta-feira',
            'Friday': 'sexta-feira',
            'Saturday': 'sábado',
            'Sunday': 'domingo'
        }
        return translation.get(weekday, weekday)