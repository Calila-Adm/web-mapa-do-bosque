#!/usr/bin/env python3
"""
WBR Dashboard - Main Application Entry Point
============================================
Dashboard principal para análise de métricas WBR (Working Backwards Reporting).
"""

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.env import load_environment_variables
# from src.clients.database.bigquery import BigQueryClient  # Comentado - usando factory agora
from src.clients.database.factory import get_database_client, get_table_config, fetch_data_generic
from src.core.wbr import gerar_grafico_wbr, calcular_metricas_wbr
from src.core.wbr_metrics import calcular_kpis  # Now using unified wbr_metrics

# Load environment variables
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, '..'))
load_environment_variables(base_dir=PROJECT_ROOT)

# Database configuration
db_type = os.getenv("DB_TYPE", "postgresql").lower()

# Normalize credential path for BigQuery (if using BigQuery)
if db_type == "bigquery":
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and not os.path.isabs(cred_path):
        abs_path = os.path.join(PROJECT_ROOT, cred_path)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path

# Initialize the database client using factory
db_client = get_database_client()

# Page configuration
st.set_page_config(page_title="WBR Dashboard", layout="wide", page_icon="📊")

# Get table configurations based on database type
TABLES_CONFIG = get_table_config(db_type)

# Check database configuration
if db_type == "bigquery":
    BQ_PROJECT = os.getenv("BIGQUERY_PROJECT_ID")
    BQ_DATASET = os.getenv("BIGQUERY_DATASET")
    if not BQ_PROJECT or not BQ_DATASET:
        st.error("❌ Configuração do BigQuery não encontrada!")
        st.info("Configure as seguintes variáveis de ambiente:")
        st.code("""
        BIGQUERY_PROJECT_ID=seu-projeto
        BIGQUERY_DATASET=seu-dataset
        GOOGLE_APPLICATION_CREDENTIALS=caminho/para/credentials.json
        """)
        st.stop()
elif db_type in ["postgresql", "postgres"]:
    # Check PostgreSQL configuration
    if not os.getenv("DATABASE_URL") and not (os.getenv("POSTGRES_DATABASE") and os.getenv("POSTGRES_USER")):
        st.error("❌ Configuração do PostgreSQL não encontrada!")
        st.info("Configure DATABASE_URL ou as variáveis individuais:")
        st.code("""
        DATABASE_URL=postgresql://user:password@host:port/dbname
        # OU
        POSTGRES_HOST=localhost
        POSTGRES_PORT=5432
        POSTGRES_DATABASE=seu-banco
        POSTGRES_USER=seu-usuario
        POSTGRES_PASSWORD=sua-senha
        """)
        st.stop()
else:
    st.error(f"❌ Tipo de banco de dados não reconhecido: {db_type}")
    st.info("Configure DB_TYPE como 'bigquery' ou 'postgresql' no arquivo .env")
    st.stop()

# Cache function for getting available date range
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def get_available_date_range():
    """Get the min and max dates available in the database - optimized version"""
    try:
        dates = []
        
        # For BigQuery, we can optimize with a specific query
        if db_type == "bigquery":
            for table_name in ['pessoas', 'veiculos', 'vendas']:
                config = TABLES_CONFIG[table_name]
                query = f"""
                SELECT 
                    MIN({config['coluna_data']}) as min_date,
                    MAX({config['coluna_data']}) as max_date
                FROM `{config['table']}`
                WHERE {config['coluna_data']} IS NOT NULL
                """
                try:
                    result = db_client.query(query).to_dataframe()
                    if not result.empty:
                        dates.extend([result['min_date'].iloc[0], result['max_date'].iloc[0]])
                except Exception:
                    pass
        else:
            # For PostgreSQL or other databases, load minimal data
            for table_name in ['pessoas', 'veiculos', 'vendas']:
                config = TABLES_CONFIG[table_name]
                try:
                    # Try to get just the date column
                    df = fetch_data_generic(
                        client=db_client,
                        config=config,
                        year_filter=None,
                        shopping_filter=None
                    )
                    
                    if df is not None and not df.empty:
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            dates.extend([df['date'].min(), df['date'].max()])
                        elif isinstance(df.index, pd.DatetimeIndex):
                            dates.extend([df.index.min(), df.index.max()])
                except Exception:
                    pass
        
        if dates:
            # Filter out None/NaT values
            valid_dates = [d for d in dates if pd.notna(d)]
            if valid_dates:
                min_date = min(valid_dates)
                max_date = max(valid_dates)
                return pd.Timestamp(min_date), pd.Timestamp(max_date)
        
        return None, None
            
    except Exception as e:
        st.error(f"Erro ao buscar range de datas: {str(e)}")
        return None, None

# Title and description
st.title("📊 Dashboard WBR - Análise de Fluxo")
st.markdown("---")

# Get available date range before showing the sidebar
min_date_available, max_date_available = get_available_date_range()

# Sidebar with filters only (no BigQuery configuration)
with st.sidebar:
    st.header("🎯 Filtros")
    
    # Date reference filter
    st.subheader("📅 Data de Referência")
    
    # Check if we have data available
    if min_date_available is not None and max_date_available is not None:
        # Convert to date objects for the date_input widget
        min_date = min_date_available.date() if hasattr(min_date_available, 'date') else min_date_available
        max_date = max_date_available.date() if hasattr(max_date_available, 'date') else max_date_available
        
        # Default value should be the most recent date with data, not today
        default_date = max_date
        
        # Show available date range - REMOVIDO conforme solicitado
        # st.caption(f"📊 Dados disponíveis: {min_date.strftime('%d/%m/%Y')} até {max_date.strftime('%d/%m/%Y')}")
        
        data_ref = st.date_input(
            "Selecione a data",
            value=default_date,
            min_value=min_date,
            max_value=max_date,
            help=f"Selecione uma data entre {min_date.strftime('%d/%m/%Y')} e {max_date.strftime('%d/%m/%Y')}"
        )
    else:
        # No data available or error loading data
        st.error("⚠️ Não foi possível determinar o período de dados disponível")
        st.info("Verifique a conexão com o banco de dados")
        # Use a fallback date input without restrictions
        data_ref = st.date_input(
            "Selecione a data",
            value=datetime.now(),
            help="Data final do período"
        )
    
    # Normaliza para Timestamp
    try:
        data_ref_ts = pd.Timestamp(data_ref)
    except Exception:
        data_ref_ts = pd.Timestamp(datetime.now() if max_date_available is None else max_date_available)
    
    # Calcula o período de análise baseado na data de referência
    # Precisamos de DOIS anos de dados para comparação YoY
    ano_ref = data_ref_ts.year
    ano_anterior = ano_ref - 1
    ano_inicio = ano_ref - 2  # Pega desde 2 anos atrás
    
    # Data inicial: 1º de janeiro do ano anterior
    # Para garantir que temos dados suficientes para comparação
    data_inicio_ts = pd.Timestamp(f'{ano_anterior}-01-01')
    
    # Se a data inicial calculada está antes dos dados disponíveis, ajusta
    if min_date_available is not None and data_inicio_ts < min_date_available:
        data_inicio_ts = min_date_available
        st.warning(f"⚠️ Ajustado início para {data_inicio_ts.strftime('%d/%m/%Y')} (primeiro dado disponível)")
    
    # Data final: data selecionada
    data_fim_ts = data_ref_ts
    
    # Validação adicional: verifica se temos dados suficientes para comparação YoY
    if min_date_available is not None and max_date_available is not None:
        dias_disponiveis = (max_date_available - min_date_available).days
        if dias_disponiveis < 365:
            st.warning(f"⚠️ Apenas {dias_disponiveis} dias de dados disponíveis. Comparação YoY pode ser limitada.")
    
    # Informações de período e comparação removidas conforme solicitado
    
    # Shopping filter (optional - will be populated if column exists)
    shopping_col = os.getenv("WBR_SHOPPING_COL", "shopping")
    filtro_shopping = st.text_input(
        "🏢 Shopping (opcional)",
        placeholder="Digite o nome do shopping",
        help="Deixe vazio para ver todos"
    )
    
    st.markdown("---")
    st.header("📐 Layout")
    
    # Layout selector - removida opção "Lado a lado"
    layout_opcao = st.radio(
        "Disposição dos gráficos:",
        options=["Um abaixo do outro", "Abas"],
        help="Escolha como visualizar os gráficos"
    )
    
    st.markdown("---")
    # Mostra informação de conexão apropriada
    if db_type == "bigquery":
        st.caption(f"🔗 Conectado a: BigQuery - {os.getenv('BIGQUERY_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET')}")
    else:
        db_info = os.getenv('POSTGRES_DATABASE', 'PostgreSQL')
        host_info = os.getenv('POSTGRES_HOST', 'localhost')
        st.caption(f"🔗 Conectado a: PostgreSQL - {db_info}@{host_info}")

# Cache function for loading data
@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def load_table_data(config: dict):
    """Load data from database for a specific table configuration"""
    try:
        # Use the generic fetch function from factory
        df = fetch_data_generic(
            client=db_client,
            config=config,
            year_filter=None,  # Applied later in apply_filters
            shopping_filter=None  # Applied later in apply_filters
        )
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {config['titulo']}: {str(e)}")
        return None

def apply_filters(df: pd.DataFrame, date_start=None, date_end=None, year_filter=None, shopping_filter=None):
    """Apply filters to dataframe"""
    if df is None or df.empty:
        return df
    
    # Apply date range filter
    if date_start and date_end:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= date_start) & (df['date'] <= date_end)]
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df[(df.index >= date_start) & (df.index <= date_end)]
    
    # Apply year filter (if no date range specified)
    elif year_filter:
        if 'date' in df.columns:
            df = df[pd.to_datetime(df['date']).dt.year == year_filter]
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df[df.index.year == year_filter]
    
    # Apply shopping filter
    if shopping_filter and 'shopping' in df.columns:
        df = df[df['shopping'].str.contains(shopping_filter, case=False, na=False)]
    
    return df

def render_metrics(df: pd.DataFrame, titulo: str):
    """Render KPI metrics for a dataframe"""
    if df is None or df.empty:
        st.warning(f"Sem dados para calcular KPIs de {titulo}")
        return
    
    try:
        kpis = calcular_kpis(df, data_referencia=data_ref_ts)
        
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

def render_chart(config: dict, df: pd.DataFrame):
    """Render WBR chart for a specific configuration"""
    if df is None or df.empty:
        st.warning(f"Sem dados disponíveis para {config['titulo']}")
        return
    
    try:
        # Generate WBR chart
        # O DataFrame vem com colunas normalizadas: 'date' e 'metric_value'
        fig = gerar_grafico_wbr(
            df=df,
            coluna_data='date',  # Nome da coluna normalizada
            coluna_pessoas='metric_value',  # Nome da coluna normalizada
            titulo=f"{config['icon']} {config['titulo']}",
            unidade=config['unidade'],
            data_referencia=data_ref_ts
        )

        # Display chart
        st.plotly_chart(fig, width='stretch', key=f"chart_{config['table']}")

        # Display metrics below chart - REMOVIDO conforme solicitado
        # render_metrics(df, config['titulo'])

        # Optional: Show data preview
        with st.expander("📋 Ver dados brutos"):
            # Be resilient if 'date' is the index
            display_df = df.reset_index()
            # If reset_index created a column named 'index' and 'date' doesn't exist, rename it to 'date'
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
                dias_pt = {'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui', 
                          'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'}
                daily_df['Dia_Semana'] = daily_df['Dia_Semana'].replace(dias_pt)
                
                # Formatar a data para exibição
                daily_df['Data'] = pd.to_datetime(daily_df['Data']).dt.strftime('%d/%m/%Y')
                
                # Formatar o valor com separador de milhares
                daily_df['Total_Diario'] = daily_df['Total_Diario'].apply(lambda x: f"{x:,.0f}")
                
                # Reorganizar colunas
                daily_df = daily_df[['Data', 'Dia_Semana', 'Total_Diario']]
                daily_df.columns = ['Data', 'Dia', 'Total Diário']
                
                # Mostrar últimos 30 dias
                st.dataframe(daily_df.head(30), width='stretch', hide_index=True)
            else:
                # Fallback para o comportamento original se as colunas esperadas não existirem
                cols = [c for c in ['date', 'metric_value'] if c in display_df.columns]
                st.dataframe(display_df[cols].tail(30), width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

# Load data for all tables
with st.spinner("Carregando dados..."):
    df_pessoas = load_table_data(TABLES_CONFIG['pessoas'])
    df_veiculos = load_table_data(TABLES_CONFIG['veiculos'])
    df_vendas = load_table_data(TABLES_CONFIG['vendas'])
    
    # Apply filters
    df_pessoas_filtered = apply_filters(
        df_pessoas, 
        date_start=data_inicio_ts,
        date_end=data_fim_ts,
        year_filter=None,
        shopping_filter=filtro_shopping
    ) if df_pessoas is not None else None
    
    df_veiculos_filtered = apply_filters(
        df_veiculos,
        date_start=data_inicio_ts,
        date_end=data_fim_ts,
        year_filter=None,
        shopping_filter=filtro_shopping
    ) if df_veiculos is not None else None
    
    df_vendas_filtered = apply_filters(
        df_vendas,
        date_start=data_inicio_ts,
        date_end=data_fim_ts,
        year_filter=None,
        shopping_filter=filtro_shopping
    ) if df_vendas is not None else None

# Render based on selected layout
if layout_opcao == "Um abaixo do outro":
    # Vertical layout
    st.subheader(f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}")
    if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
        render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
    else:
        st.warning("Nenhum dado de pessoas encontrado")
    
    st.markdown("---")
    
    st.subheader(f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}")
    if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
        render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
    else:
        st.warning("Nenhum dado de veículos encontrado")
    
    st.markdown("---")
    
    st.subheader(f"{TABLES_CONFIG['vendas']['icon']} {TABLES_CONFIG['vendas']['titulo']}")
    if df_vendas_filtered is not None and not df_vendas_filtered.empty:
        render_chart(TABLES_CONFIG['vendas'], df_vendas_filtered)
    else:
        st.warning("Nenhum dado de vendas encontrado")

else:  # Abas
    # Tabs layout
    tab_pessoas, tab_veiculos, tab_vendas = st.tabs([
        f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}",
        f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}",
        f"{TABLES_CONFIG['vendas']['icon']} {TABLES_CONFIG['vendas']['titulo']}"
    ])
    
    with tab_pessoas:
        if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
            render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
        else:
            st.warning("Nenhum dado de pessoas encontrado")
    
    with tab_veiculos:
        if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
            render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
        else:
            st.warning("Nenhum dado de veículos encontrado")
    
    with tab_vendas:
        if df_vendas_filtered is not None and not df_vendas_filtered.empty:
            render_chart(TABLES_CONFIG['vendas'], df_vendas_filtered)
        else:
            st.warning("Nenhum dado de vendas encontrado")

# Advanced WBR Metrics Section
st.markdown("---")
st.header("📊 Métricas WBR Avançadas")

with st.expander("🔍 Análise Detalhada de Métricas WBR", expanded=False):
    # Check if we have data to analyze
    if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
        st.subheader("Pessoas - Análise WOW/YOY")
        
        # Calculate advanced metrics
        metricas_derivadas = {
            'taxa_crescimento': {
                'type': 'division',
                'numerator': 'metric_value',
                'denominator': 'metric_value',
                'description': 'Taxa de crescimento relativa'
            }
        } if 'metric_value' in df_pessoas_filtered.columns else None
        
        metrics_result = calcular_metricas_wbr(
            df_pessoas_filtered,
            data_referencia=data_ref_ts,
            coluna_data='date',
            coluna_metrica='metric_value',
            metricas_derivadas=metricas_derivadas
        )
        
        if metrics_result.get('success'):
            # Display comparisons
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
            
            # Show summary table
            if summary:
                st.subheader("📈 Resumo de Métricas")
                summary_df = pd.DataFrame(summary)
                st.dataframe(
                    summary_df,
                    width='stretch',
                    hide_index=True
                )
            
            # Show trailing weeks comparison
            st.subheader("📅 Comparação de Semanas")
            tab1, tab2 = st.tabs(["Ano Atual", "Ano Anterior"])
            
            with tab1:
                cy_data = metrics_result.get('trailing_weeks', {}).get('current_year', [])
                if cy_data:
                    st.dataframe(pd.DataFrame(cy_data), width='stretch', hide_index=True)
            
            with tab2:
                py_data = metrics_result.get('trailing_weeks', {}).get('previous_year', [])
                if py_data:
                    st.dataframe(pd.DataFrame(py_data), width='stretch', hide_index=True)
        else:
            st.warning(f"Não foi possível calcular métricas avançadas: {metrics_result.get('error', 'Erro desconhecido')}")
    else:
        st.info("Carregue dados primeiro para ver as métricas WBR avançadas")

# Footer
st.markdown("---")
st.caption("💡 Dica: Use os filtros na barra lateral para refinar a análise")