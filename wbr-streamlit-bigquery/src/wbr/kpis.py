import pandas as pd
from datetime import timedelta


def calcular_yoy(valor_cy, valor_py):
    if valor_py == 0 or pd.isna(valor_py) or pd.isna(valor_cy):
        return 0
    return ((valor_cy - valor_py) / valor_py) * 100


def calcular_kpis(df: pd.DataFrame, data_referencia: pd.Timestamp, coluna_data: str = 'date', coluna_metrica: str = 'metric_value'):
    """Calcula os KPIs (LastWk, WOW, YOY etc.) com alinhamento de semanas ISO."""
    # Lida com casos onde a data pode já ser o índice ou uma coluna
    df = df.copy()
    if coluna_data in df.columns:
        df = df.set_index(coluna_data)
    else:
        # Se não há coluna, mas o índice é temporal, seguimos com ele
        if not isinstance(df.index, pd.DatetimeIndex):
            # Última tentativa: se existir coluna com mesmo significado mas nome diferente, erro explícito
            raise ValueError(f"Column '{coluna_data}' not found and index is not DatetimeIndex. Available columns: {df.columns.tolist()}")
    # Garante que o índice é DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Garante que a data de referência é Timestamp (evita comparações date vs datetime)
    data_ref_ts = pd.Timestamp(data_referencia)

    metrica = coluna_metrica
    if metrica not in df.columns:
        raise ValueError(f"Column '{metrica}' not found in DataFrame columns: {df.columns.tolist()}")
    from pandas.tseries.offsets import DateOffset
    from datetime import date

    def _to_float(x):
        try:
            if pd.isna(x):
                return 0.0
            return float(x)
        except Exception:
            return 0.0

    def _safe_div(num, den):
        n = _to_float(num)
        d = _to_float(den)
        return (n / d) if d > 0 else 0.0

    fim_semana_calendario = data_ref_ts.to_period('W-SUN').end_time.normalize()
    inicio_semana_calendario = (fim_semana_calendario - timedelta(days=6)).normalize()
    fim_periodo_atual = data_ref_ts.normalize()
    ultima_semana = _to_float(df[(df.index >= inicio_semana_calendario) & (df.index <= fim_periodo_atual)][metrica].sum())

    dias_decorridos_na_semana = (fim_periodo_atual - inicio_semana_calendario).days

    inicio_semana_anterior = inicio_semana_calendario - timedelta(weeks=1)
    fim_periodo_anterior = inicio_semana_anterior + timedelta(days=dias_decorridos_na_semana)
    semana_anterior = _to_float(df[(df.index >= inicio_semana_anterior) & (df.index <= fim_periodo_anterior)][metrica].sum())

    semana_atual_iso = fim_semana_calendario.isocalendar()[1]
    ano_anterior = data_ref_ts.year - 1
    try:
        fim_semana_py = pd.Timestamp(date.fromisocalendar(ano_anterior, semana_atual_iso, 7))
    except ValueError:
        fim_semana_py = pd.Timestamp(date.fromisocalendar(ano_anterior, 52, 7))

    inicio_semana_py = (fim_semana_py - timedelta(days=6)).normalize()
    fim_periodo_py = inicio_semana_py + timedelta(days=dias_decorridos_na_semana)
    semana_py = _to_float(df[(df.index >= inicio_semana_py) & (df.index <= fim_periodo_py)][metrica].sum())

    inicio_mes = data_ref_ts.replace(day=1)
    mes_atual = _to_float(df[(df.index >= inicio_mes) & (df.index <= data_ref_ts)][metrica].sum())
    inicio_mes_py = inicio_mes - DateOffset(years=1)
    fim_mes_py = data_ref_ts - DateOffset(years=1)
    mes_py = _to_float(df[(df.index >= inicio_mes_py) & (df.index <= fim_mes_py)][metrica].sum())

    inicio_trimestre = data_ref_ts.replace(day=1, month=((data_ref_ts.month-1)//3)*3 + 1)
    trimestre_atual = _to_float(df[(df.index >= inicio_trimestre) & (df.index <= data_ref_ts)][metrica].sum())
    inicio_trimestre_py = inicio_trimestre - DateOffset(years=1)
    fim_trimestre_py = data_ref_ts - DateOffset(years=1)
    trimestre_py = _to_float(df[(df.index >= inicio_trimestre_py) & (df.index <= fim_trimestre_py)][metrica].sum())

    inicio_ano = data_ref_ts.replace(month=1, day=1)
    ano_atual = _to_float(df[(df.index >= inicio_ano) & (df.index <= data_ref_ts)][metrica].sum())
    inicio_ano_py = inicio_ano - DateOffset(years=1)
    fim_ano_py = data_ref_ts - DateOffset(years=1)
    ano_py = _to_float(df[(df.index >= inicio_ano_py) & (df.index <= fim_ano_py)][metrica].sum())

    return {
        'ultima_semana': ultima_semana,
        'mes_atual': mes_atual,
        'trimestre_atual': trimestre_atual,
        'ano_atual': ano_atual,
        'var_semanal': _safe_div((ultima_semana - semana_anterior), semana_anterior) * 100,
        'yoy_semanal': _safe_div((ultima_semana - semana_py), semana_py) * 100,
        'yoy_mensal': _safe_div((mes_atual - mes_py), mes_py) * 100,
        'yoy_trimestral': _safe_div((trimestre_atual - trimestre_py), trimestre_py) * 100,
        'yoy_anual': _safe_div((ano_atual - ano_py), ano_py) * 100,
        # Adicionar keys esperadas pelo streamlit_app.py
        'yoy_pct': _safe_div((ultima_semana - semana_py), semana_py) * 100,
        'yoy_abs': ultima_semana - semana_py,
        'wow_pct': _safe_div((ultima_semana - semana_anterior), semana_anterior) * 100,
        'wow_abs': ultima_semana - semana_anterior,
        'mtd_atual': mes_atual,
        'mtd_pct': _safe_div((mes_atual - mes_py), mes_py) * 100
    }