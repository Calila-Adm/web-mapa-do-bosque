"""
Serviço de filtros - Aplicação de filtros em DataFrames
"""
from typing import Optional
import pandas as pd


class FilterService:
    """Serviço para aplicação de filtros em dados"""

    @staticmethod
    def apply_filters(
        df: pd.DataFrame,
        date_start: Optional[pd.Timestamp] = None,
        date_end: Optional[pd.Timestamp] = None,
        year_filter: Optional[int] = None,
        shopping_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Aplica filtros ao dataframe

        Args:
            df: DataFrame a ser filtrado
            date_start: Data inicial do período
            date_end: Data final do período
            year_filter: Filtro de ano (usado se datas não especificadas)
            shopping_filter: Filtro de shopping

        Returns:
            DataFrame filtrado
        """
        if df is None or df.empty:
            return df

        # Aplica filtro de intervalo de datas
        if date_start and date_end:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= date_start) & (df['date'] <= date_end)]
            elif isinstance(df.index, pd.DatetimeIndex):
                df = df[(df.index >= date_start) & (df.index <= date_end)]

        # Aplica filtro de ano (se nenhum intervalo de datas especificado)
        elif year_filter:
            if 'date' in df.columns:
                df = df[pd.to_datetime(df['date']).dt.year == year_filter]
            elif isinstance(df.index, pd.DatetimeIndex):
                df = df[df.index.year == year_filter]

        # Aplica filtro de shopping
        if shopping_filter and 'shopping' in df.columns:
            df = df[df['shopping'] == shopping_filter]

        return df

    @staticmethod
    def apply_date_filter(
        df: pd.DataFrame,
        date_start: Optional[pd.Timestamp] = None,
        date_end: Optional[pd.Timestamp] = None
    ) -> pd.DataFrame:
        """
        Aplica apenas filtros de data ao DataFrame

        Args:
            df: DataFrame a ser filtrado
            date_start: Data inicial
            date_end: Data final

        Returns:
            DataFrame filtrado por data
        """
        if df is None or df.empty:
            return df

        if date_start and date_end:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= date_start) & (df['date'] <= date_end)]
            elif isinstance(df.index, pd.DatetimeIndex):
                df = df[(df.index >= date_start) & (df.index <= date_end)]

        return df

    @staticmethod
    def apply_shopping_filter(
        df: pd.DataFrame,
        shopping: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Aplica filtro de shopping ao DataFrame

        Args:
            df: DataFrame a ser filtrado
            shopping: Nome do shopping

        Returns:
            DataFrame filtrado por shopping
        """
        if df is None or df.empty or not shopping:
            return df

        if 'shopping' in df.columns:
            df = df[df['shopping'] == shopping]

        return df