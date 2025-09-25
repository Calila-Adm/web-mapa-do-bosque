"""
Página principal do Dashboard WBR
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from src.services.data_service import DataService
from src.services.filter_service import FilterService
from src.ui.components.charts import ChartComponent
from src.ui.components.metrics import MetricsComponent
from src.config.database import get_table_config


class DashboardPage:
    """Página principal do dashboard"""

    def __init__(self):
        # Lazy initialization - componentes criados sob demanda
        self._data_service = None
        self._filter_service = None
        self._chart_component = None
        self._metrics_component = None
        self.tables_config = get_table_config()

    @property
    def data_service(self):
        """Lazy loading do data service"""
        if self._data_service is None:
            from src.services.data_service import get_data_service
            self._data_service = get_data_service()
        return self._data_service

    @property
    def filter_service(self):
        """Lazy loading do filter service"""
        if self._filter_service is None:
            self._filter_service = FilterService()
        return self._filter_service

    @property
    def chart_component(self):
        """Lazy loading do chart component"""
        if self._chart_component is None:
            self._chart_component = ChartComponent()
        return self._chart_component

    @property
    def metrics_component(self):
        """Lazy loading do metrics component"""
        if self._metrics_component is None:
            self._metrics_component = MetricsComponent()
        return self._metrics_component

    def render(self, filters: Dict[str, Any]):
        """
        Renderiza página principal do dashboard

        Args:
            filters: Filtros selecionados na sidebar
        """
        st.title("📊 Dashboard WBR - Análise de Fluxo")
        st.markdown("---")


        # Carrega e processa dados
        data = self._load_and_process_data(filters)

        if not data:
            st.error("Erro ao carregar dados. Verifique a conexão com o banco de dados.")
            return

        # Renderiza sempre layout vertical (um abaixo do outro)
        self._render_vertical_layout(data, filters)

        # Rodapé
        st.markdown("---")
        st.caption("💡 Dica: Use os filtros na barra lateral para refinar a análise")

    def _load_and_process_data(self, filters: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        Carrega e processa dados das tabelas

        Args:
            filters: Filtros a serem aplicados

        Returns:
            Dicionário com DataFrames processados
        """
        data = {}

        with st.spinner("Carregando dados..."):
            # Carrega dados de cada tabela já filtrados na query
            for table_name, config in self.tables_config.items():
                # Carrega dados já filtrados pela query SQL
                df = self.data_service.load_table_data(
                    table_name,
                    config,
                    date_reference=filters.get('data_referencia'),
                    shopping_filter=filters.get('shopping')
                )

                # Não precisa mais filtrar em Python, dados já vêm filtrados
                data[table_name] = df

        return data

    def _render_vertical_layout(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """
        Renderiza layout vertical (um abaixo do outro)

        Args:
            data: Dados processados
            filters: Filtros aplicados
        """
        for table_name, config in self.tables_config.items():
            st.subheader(f"{config['icon']} {config['titulo']}")

            df = data.get(table_name)
            if df is not None and not df.empty:
                self.chart_component.render_chart(
                    config,
                    df,
                    filters.get('data_referencia'),
                    filters.get('metodo_semana', 'iso')
                )
            else:
                st.warning(f"Nenhum dado de {config['titulo'].lower()} encontrado")

            if table_name != 'vendas':  # Não adiciona separador após o último
                st.markdown("---")

