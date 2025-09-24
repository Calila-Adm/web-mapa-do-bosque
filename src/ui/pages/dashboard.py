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
        self.data_service = DataService()
        self.filter_service = FilterService()
        self.chart_component = ChartComponent()
        self.metrics_component = MetricsComponent()
        self.tables_config = get_table_config()

    def render(self, filters: Dict[str, Any]):
        """
        Renderiza página principal do dashboard

        Args:
            filters: Filtros selecionados na sidebar
        """
        st.title("📊 Dashboard WBR - Análise de Fluxo")
        st.markdown("---")

        # Mostra filtros ativos
        if filters.get('shopping'):
            st.info(f"🏪 **Filtro ativo:** Shopping {filters['shopping']}")

        # Carrega e processa dados
        data = self._load_and_process_data(filters)

        if not data:
            st.error("Erro ao carregar dados. Verifique a conexão com o banco de dados.")
            return

        # Renderiza baseado no layout selecionado
        if filters.get('layout') == "Abas":
            self._render_tabs_layout(data, filters)
        else:
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
            # Carrega dados de cada tabela
            for table_name, config in self.tables_config.items():
                # Carrega dados brutos
                df = self.data_service.load_table_data(table_name, config)

                if df is not None:
                    # Aplica filtros
                    df_filtered = self.filter_service.apply_filters(
                        df,
                        date_start=filters.get('data_inicio'),
                        date_end=filters.get('data_fim'),
                        shopping_filter=filters.get('shopping')
                    )
                    data[table_name] = df_filtered
                else:
                    data[table_name] = None

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
                    filters.get('data_referencia')
                )
            else:
                st.warning(f"Nenhum dado de {config['titulo'].lower()} encontrado")

            if table_name != 'vendas':  # Não adiciona separador após o último
                st.markdown("---")

    def _render_tabs_layout(self, data: Dict[str, pd.DataFrame], filters: Dict[str, Any]):
        """
        Renderiza layout em abas

        Args:
            data: Dados processados
            filters: Filtros aplicados
        """
        # Cria abas
        tabs = st.tabs([
            f"{config['icon']} {config['titulo']}"
            for config in self.tables_config.values()
        ])

        # Renderiza conteúdo de cada aba
        for idx, (table_name, config) in enumerate(self.tables_config.items()):
            with tabs[idx]:
                df = data.get(table_name)
                if df is not None and not df.empty:
                    self.chart_component.render_chart(
                        config,
                        df,
                        filters.get('data_referencia')
                    )
                else:
                    st.warning(f"Nenhum dado de {config['titulo'].lower()} encontrado")