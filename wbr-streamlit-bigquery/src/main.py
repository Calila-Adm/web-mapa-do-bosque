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
from src.core.wbr import gerar_grafico_wbr
from src.core.kpis import calcular_kpis

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

# Title and description
st.title("📊 Dashboard WBR - Análise de Fluxo")
st.markdown("---")

# Sidebar with filters only (no BigQuery configuration)
with st.sidebar:
    st.header("🎯 Filtros")
    
    # Date reference filter
    st.subheader("📅 Data de Referência")
    
    data_ref = st.date_input(
        "Selecione a data",
        value=datetime.now(),
        help="Data final do período. O gráfico mostrará desde o início do ano anterior até esta data"
    )
    
    # Normaliza para Timestamp
    try:
        data_ref_ts = pd.Timestamp(data_ref)
    except Exception:
        data_ref_ts = pd.Timestamp(datetime.now())
    
    # Calcula o período de análise baseado na data de referência
    # Precisamos de DOIS anos de dados para comparação YoY
    ano_ref = data_ref_ts.year
    ano_anterior = ano_ref - 1
    ano_inicio = ano_ref - 2  # Pega desde 2 anos atrás
    
    # Data inicial: 1º de janeiro de DOIS anos atrás
    # Ex: Se data ref é 31/12/2024, pega desde 01/01/2023
    data_inicio_ts = pd.Timestamp(f'{ano_anterior}-01-01')
    # Data final: data selecionada
    data_fim_ts = data_ref_ts
    
    st.caption(f"📊 Período: {data_inicio_ts.strftime('%d/%m/%Y')} até {data_fim_ts.strftime('%d/%m/%Y')}")
    st.caption(f"📈 Comparando: {ano_ref} (até {data_ref_ts.strftime('%d/%m')}) vs {ano_anterior} (mesmo período)")
    
    # Shopping filter (optional - will be populated if column exists)
    shopping_col = os.getenv("WBR_SHOPPING_COL", "shopping")
    filtro_shopping = st.text_input(
        "🏢 Shopping (opcional)",
        placeholder="Digite o nome do shopping",
        help="Deixe vazio para ver todos"
    )
    
    st.markdown("---")
    st.header("📐 Layout")
    
    # Layout selector
    layout_opcao = st.radio(
        "Disposição dos gráficos:",
        options=["Lado a lado", "Um abaixo do outro", "Abas"],
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

        # Display metrics below chart
        render_metrics(df, config['titulo'])

        # Optional: Show data preview
        with st.expander("📋 Ver dados brutos"):
            # Be resilient if 'date' is the index
            display_df = df.reset_index()
            # If reset_index created a column named 'index' and 'date' doesn't exist, rename it to 'date'
            if 'date' not in display_df.columns and 'index' in display_df.columns:
                display_df = display_df.rename(columns={'index': 'date'})
            cols = [c for c in ['date', 'metric_value'] if c in display_df.columns]
            st.dataframe(display_df[cols].tail(30), width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")

# Load data for both tables
with st.spinner("Carregando dados..."):
    df_pessoas = load_table_data(TABLES_CONFIG['pessoas'])
    df_veiculos = load_table_data(TABLES_CONFIG['veiculos'])
    
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

# Render based on selected layout
if layout_opcao == "Lado a lado":
    # Two columns layout
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.subheader(f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}")
        if df_pessoas_filtered is not None and not df_pessoas_filtered.empty:
            render_chart(TABLES_CONFIG['pessoas'], df_pessoas_filtered)
        else:
            st.warning("Nenhum dado de pessoas encontrado")
    
    with col2:
        st.subheader(f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}")
        if df_veiculos_filtered is not None and not df_veiculos_filtered.empty:
            render_chart(TABLES_CONFIG['veiculos'], df_veiculos_filtered)
        else:
            st.warning("Nenhum dado de veículos encontrado")

elif layout_opcao == "Um abaixo do outro":
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

else:  # Abas
    # Tabs layout
    tab_pessoas, tab_veiculos = st.tabs([
        f"{TABLES_CONFIG['pessoas']['icon']} {TABLES_CONFIG['pessoas']['titulo']}",
        f"{TABLES_CONFIG['veiculos']['icon']} {TABLES_CONFIG['veiculos']['titulo']}"
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

# Footer
st.markdown("---")
st.caption("💡 Dica: Use os filtros na barra lateral para refinar a análise")