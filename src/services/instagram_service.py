"""
Serviço do Instagram - Gerenciamento de métricas do Instagram
"""
from typing import Optional, Dict, Any
import pandas as pd
import streamlit as st
import os
from src.clients.database.supabase_postgres import SupabaseClient
from src.services.filter_service import FilterService


class InstagramService:
    """Serviço para gerenciamento de métricas do Instagram"""

    def __init__(self):
        self.supabase_client = None
        self.filter_service = FilterService()
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa cliente Supabase se configurado"""
        if os.getenv("SUPABASE_DATABASE_URL"):
            try:
                self.supabase_client = SupabaseClient()
                self.connected = self.supabase_client.test_connection()
            except Exception as e:
                st.error(f"Erro ao conectar com Supabase: {str(e)}")
                self.connected = False
        else:
            self.connected = False

    def is_connected(self) -> bool:
        """Verifica se está conectado ao Supabase"""
        return self.connected

    @st.cache_data(ttl=300, show_spinner=False)
    def load_engagement_data(
        _self,
        date_start: str,
        date_end: str,
        shopping_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Carrega dados de engajamento do Instagram

        Args:
            date_start: Data inicial (formato YYYY-MM-DD)
            date_end: Data final (formato YYYY-MM-DD)
            shopping_filter: Filtro de shopping opcional

        Returns:
            DataFrame com dados de engajamento
        """
        if not _self.connected or not _self.supabase_client:
            return pd.DataFrame()

        try:
            df = _self.supabase_client.get_engagement_data(
                date_start=date_start,
                date_end=date_end,
                shopping_filter=shopping_filter
            )

            if not df.empty:
                df['data'] = pd.to_datetime(df['data'])
                # Aplicar filtros adicionais se necessário
                df = _self.filter_service.apply_filters(
                    df,
                    date_start=pd.Timestamp(date_start),
                    date_end=pd.Timestamp(date_end),
                    shopping_filter=shopping_filter
                )

            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados de engajamento: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=300, show_spinner=False)
    def load_post_count_data(
        _self,
        date_start: str,
        date_end: str,
        shopping_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Carrega contagem de posts do Instagram

        Args:
            date_start: Data inicial (formato YYYY-MM-DD)
            date_end: Data final (formato YYYY-MM-DD)
            shopping_filter: Filtro de shopping opcional

        Returns:
            DataFrame com contagem de posts
        """
        if not _self.connected or not _self.supabase_client:
            return pd.DataFrame()

        try:
            df = _self.supabase_client.get_post_count_data(
                date_start=date_start,
                date_end=date_end,
                shopping_filter=shopping_filter
            )

            if not df.empty:
                df['data'] = pd.to_datetime(df['data'])
                # Renomeia colunas para compatibilidade
                df.columns = ['shopping', 'data', 'total_posts']
                # Aplicar filtros adicionais
                df = _self.filter_service.apply_filters(
                    df,
                    date_start=pd.Timestamp(date_start),
                    date_end=pd.Timestamp(date_end),
                    shopping_filter=shopping_filter
                )

            return df
        except Exception as e:
            st.error(f"Erro ao carregar contagem de posts: {str(e)}")
            return pd.DataFrame()

    def get_shopping_colors(self) -> Dict[str, str]:
        """
        Retorna mapeamento de cores para cada shopping

        Returns:
            Dicionário com cores por shopping
        """
        return {
            'SCIB': '#1f77b4',  # Azul
            'SBGP': '#2ca02c',  # Verde
            'SBI': '#d62728'    # Vermelho
        }

    def calculate_instagram_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula métricas agregadas do Instagram

        Args:
            df: DataFrame com dados do Instagram

        Returns:
            Dicionário com métricas calculadas
        """
        if df.empty:
            return {
                'total_alcance': 0,
                'total_impressoes': 0,
                'total_engajamento': 0,
                'total_posts': 0,
                'media_alcance_por_post': 0,
                'media_engajamento_por_post': 0
            }

        metrics = {
            'total_alcance': df['total_alcance'].sum() if 'total_alcance' in df.columns else 0,
            'total_impressoes': df['total_impressoes'].sum() if 'total_impressoes' in df.columns else 0,
            'total_engajamento': df['engajamento_total'].sum() if 'engajamento_total' in df.columns else 0,
            'total_posts': df['total_posts'].sum() if 'total_posts' in df.columns else 0,
        }

        # Calcula médias por post
        if metrics['total_posts'] > 0:
            metrics['media_alcance_por_post'] = metrics['total_alcance'] / metrics['total_posts']
            metrics['media_engajamento_por_post'] = metrics['total_engajamento'] / metrics['total_posts']
        else:
            metrics['media_alcance_por_post'] = 0
            metrics['media_engajamento_por_post'] = 0

        return metrics