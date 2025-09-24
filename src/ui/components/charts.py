"""
Componente de gráficos
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any
from src.core.wbr import gerar_grafico_wbr


class ChartComponent:
    """Componente para renderização de gráficos"""

    def render_chart(
        self,
        config: Dict[str, Any],
        df: pd.DataFrame,
        data_referencia: pd.Timestamp
    ):
        """
        Renderiza gráfico WBR para uma configuração específica

        Args:
            config: Configuração da tabela/gráfico
            df: DataFrame com os dados
            data_referencia: Data de referência para o gráfico
        """
        if df is None or df.empty:
            st.warning(f"Sem dados disponíveis para {config['titulo']}")
            return

        try:
            # Gera gráfico WBR
            fig = gerar_grafico_wbr(
                df=df,
                coluna_data='date',
                coluna_pessoas='metric_value',
                titulo=f"{config['icon']} {config['titulo']}",
                unidade=config['unidade'],
                data_referencia=data_referencia
            )

            # Exibe gráfico
            st.plotly_chart(
                fig,
                width="stretch",
                key=f"chart_{config['table']}"
            )

            # Opcional: Mostra prévia dos dados
            with st.expander("📋 Ver dados brutos"):
                self._render_data_preview(df)

        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {str(e)}")

    def _render_data_preview(self, df: pd.DataFrame):
        """
        Renderiza prévia dos dados em formato tabular

        Args:
            df: DataFrame com os dados
        """
        # Seja resiliente se 'date' for o índice
        display_df = df.reset_index()

        # Se reset_index criou uma coluna 'index' e 'date' não existe, renomeia
        if 'date' not in display_df.columns and 'index' in display_df.columns:
            display_df = display_df.rename(columns={'index': 'date'})

        # Agrupar por data e somar metric_value para visualização diária
        if 'date' in display_df.columns and 'metric_value' in display_df.columns:
            # Garantir que date seja datetime
            display_df['date'] = pd.to_datetime(display_df['date'])

            # Agrupar por data (apenas a parte da data, sem hora)
            daily_df = display_df.groupby(display_df['date'].dt.date).agg({
                'metric_value': 'sum'
            }).reset_index()
            daily_df.columns = ['Data', 'Total_Diario']

            # Ordenar por data (mais recente primeiro)
            daily_df = daily_df.sort_values('Data', ascending=False)

            # Adicionar dia da semana
            daily_df['Dia_Semana'] = pd.to_datetime(daily_df['Data']).dt.strftime('%a')
            dias_pt = {
                'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua',
                'Thu': 'Qui', 'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'
            }
            daily_df['Dia_Semana'] = daily_df['Dia_Semana'].replace(dias_pt)

            # Formatar a data para exibição
            daily_df['Data'] = pd.to_datetime(daily_df['Data']).dt.strftime('%d/%m/%Y')

            # Formatar o valor com separador de milhares
            daily_df['Total_Diario'] = daily_df['Total_Diario'].apply(lambda x: f"{x:,.0f}")

            # Reorganizar colunas
            daily_df = daily_df[['Data', 'Dia_Semana', 'Total_Diario']]
            daily_df.columns = ['Data', 'Dia', 'Total Diário']

            # Mostrar últimos 30 dias
            st.dataframe(daily_df.head(30), width="stretch", hide_index=True)
        else:
            # Fallback para o comportamento original
            cols = [c for c in ['date', 'metric_value'] if c in display_df.columns]
            if cols:
                st.dataframe(display_df[cols].tail(30), width="stretch", hide_index=True)

    def render_instagram_chart(
        self,
        df: pd.DataFrame,
        metric_col: str,
        title: str,
        y_label: str,
        data_referencia: pd.Timestamp,
        shopping_filter: str = None
    ):
        """
        Renderiza gráfico padronizado para métricas do Instagram

        Args:
            df: DataFrame com os dados
            metric_col: Coluna da métrica a ser exibida
            title: Título do gráfico
            y_label: Label do eixo Y
            data_referencia: Data de referência
            shopping_filter: Filtro de shopping aplicado
        """
        if df.empty:
            st.warning(f"Sem dados disponíveis para {title}")
            return None

        # Padroniza DataFrame para formato WBR
        df_chart = df.rename(columns={
            'data': 'date',
            metric_col: 'metric_value'
        })[['date', 'metric_value', 'shopping'] if 'shopping' in df.columns else ['date', 'metric_value']].copy()

        # Se houver filtro de shopping, aplica
        if shopping_filter and 'shopping' in df_chart.columns:
            df_chart = df_chart[df_chart['shopping'] == shopping_filter]

        # Configuração para render_chart
        config = {
            'titulo': title,
            'icon': '',
            'unidade': y_label,
            'table': metric_col
        }

        # Chama render_chart para manter padrão visual
        self.render_chart(config, df_chart, data_referencia)