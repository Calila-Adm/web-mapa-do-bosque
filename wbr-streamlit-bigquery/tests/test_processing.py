import pytest
import pandas as pd
from src.wbr.processing import processar_dados_wbr, COLUNA_DATA, COLUNA_METRICA

def test_processar_dados_wbr():
    # Teste de exemplo para a função processar_dados_wbr
    # Criação de um DataFrame de exemplo
    data = {
        'data': pd.date_range(start='2023-01-01', periods=10, freq='D'),
        'metric': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    }
    df = pd.DataFrame(data)
    df.rename(columns={'data': COLUNA_DATA, 'metric': COLUNA_METRICA}, inplace=True)

    # Chamada da função com o DataFrame de exemplo
    resultado = processar_dados_wbr(df)

    # Verificações de teste
    assert 'semanas_cy' in resultado
    assert 'meses_cy' in resultado
    assert 'semanas_py' in resultado
    assert 'meses_py' in resultado
    assert isinstance(resultado['semanas_cy'], pd.DataFrame)
    assert isinstance(resultado['meses_cy'], pd.DataFrame)