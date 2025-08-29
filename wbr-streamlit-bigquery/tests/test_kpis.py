import pytest
import pandas as pd
from src.wbr.kpis import calcular_kpis, COLUNA_DATA, COLUNA_METRICA

def test_calcular_kpis():
    # Dados de exemplo para o teste
    df = pd.DataFrame({
        COLUNA_DATA: pd.date_range(start='2023-01-01', periods=10, freq='D'),
        COLUNA_METRICA: [100, 200, 150, 300, 250, 400, 350, 500, 450, 600]
    })

    # Data de referência para os KPIs
    data_referencia = pd.Timestamp('2023-01-10')

    # Chamar a função para calcular KPIs
    kpis = calcular_kpis(df, data_referencia)

    # Verificar se os KPIs calculados estão corretos
    # Verificações básicas de existência de chaves e tipos
    for key in ['ultima_semana','var_semanal','yoy_semanal','mes_atual','yoy_mensal','trimestre_atual','yoy_trimestral','ano_atual','yoy_anual']:
        assert key in kpis