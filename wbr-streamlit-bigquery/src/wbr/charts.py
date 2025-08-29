import pandas as pd
import plotly.graph_objects as go

from .kpis import calcular_kpis
from .processing import COLUNA_METRICA as _COLUNA_METRICA


def formatar_valor(valor, tipo='numero'):
    if pd.isna(valor):
        return ""
    if tipo == 'numero':
        if valor >= 1_000_000_000:
            return f"{valor/1_000_000_000:.1f}B"
        elif valor >= 1_000_000:
            return f"{valor/1_000_000:.1f}M"
        elif valor >= 1_000:
            return f"{valor/1_000:.1f}k"
        else:
            return f"{valor:.0f}"
    elif tipo == 'percentual':
        return f"{valor:+.1f}%"
    return str(valor)


def criar_grafico_wbr(dados: dict, df: pd.DataFrame, data_ref: pd.Timestamp, titulo: str, unidade: str):
    def _to_float(x):
        try:
            if pd.isna(x):
                return None
            return float(x)
        except Exception:
            return None

    def _is_positive(x):
        v = _to_float(x)
        return v is not None and v > 0
    metrica = _COLUNA_METRICA

    valores_cy_semanas = list(dados['semanas_cy'][metrica].values)
    valores_py_semanas = list(dados['semanas_py'][metrica].values)
    x_semanas = list(range(6))

    valores_cy_meses = list(dados['meses_cy'][metrica].values)
    valores_py_meses = list(dados['meses_py'][metrica].values)
    # Garantir sempre 12 meses (Jan–Dez)
    if len(valores_cy_meses) < 12:
        valores_cy_meses += [None] * (12 - len(valores_cy_meses))
    if len(valores_py_meses) < 12:
        valores_py_meses += [None] * (12 - len(valores_py_meses))
    x_meses = list(range(7, 7 + 12))

    def _yoy(cy, py):
        cyf = _to_float(cy)
        pyf = _to_float(py)
        if pyf is None or pyf == 0 or cyf is None:
            return None
        return ((cyf - pyf) / pyf) * 100

    yoy_semanas = [_yoy(cy, py) for cy, py in zip(valores_cy_semanas, valores_py_semanas)]
    yoy_meses = [_yoy(cy, py) for cy, py in zip(valores_cy_meses, valores_py_meses)]

    # Convert all possible pandas.NA values to native floats/None upfront
    valores_cy_semanas_clean = [_to_float(v) for v in valores_cy_semanas]
    valores_py_semanas_clean = [_to_float(v) for v in valores_py_semanas]
    valores_cy_meses_clean = [_to_float(v) for v in valores_cy_meses]
    valores_py_meses_clean = [_to_float(v) for v in valores_py_meses]
    yoy_semanas_clean = [_to_float(v) for v in yoy_semanas]
    yoy_meses_clean = [_to_float(v) for v in yoy_meses]

    semanas_do_ano = dados['semanas_cy'].index.isocalendar().week.tolist()
    labels_semanas = [f'Wk {sem}' for sem in semanas_do_ano]

    meses_ordenados = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    labels_meses = []
    # Labels fixos Jan–Dez
    labels_meses = meses_ordenados.copy()

    # Preenche YOY mensal até 12 itens
    while len(yoy_meses) < 12:
        yoy_meses.append(None)

    labels_x = labels_semanas + [''] + labels_meses
    ano_atual = dados.get('ano_atual', data_ref.year)
    ano_anterior = dados.get('ano_anterior', data_ref.year - 1)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_semanas,
        y=valores_py_semanas_clean,
        name=f'{unidade.upper()} {ano_anterior} (Semanas)',
        line=dict(color="#D685AB", width=1.5),
        mode='lines',
        connectgaps=False,
        hovertemplate='%{y:,.0f}<extra></extra>',
        yaxis='y'
    ))

    fig.add_trace(go.Scatter(
        x=x_semanas,
        y=valores_cy_semanas_clean,
        name=f'{unidade.upper()} {ano_atual} (Semanas)',
        line=dict(color="#000075", width=2.5, shape='spline', smoothing=1.3),
        mode='lines+markers',
        marker=dict(color='#00008B', size=8, symbol='diamond'),
        connectgaps=False,
        hovertemplate='%{y:,.0f}<extra></extra>',
        yaxis='y'
    ))

    fig.add_trace(go.Scatter(
        x=x_meses,
        y=valores_py_meses_clean,
        name=f'{unidade.upper()} {ano_anterior} (Meses)',
        line=dict(color="#D685AB", width=1.5),
        mode='lines',
        connectgaps=False,
        hovertemplate='%{y:,.0f}<extra></extra>',
        yaxis='y2'
    ))

    if dados['mes_parcial_cy'] and any(not pd.isna(v) for v in valores_cy_meses):
        x_completo = x_meses[:-1]
        y_completo = valores_cy_meses_clean[:-1]
        x_parcial = x_meses[-2:] if len(x_meses) > 1 else x_meses
        y_parcial = valores_cy_meses_clean[-2:] if len(valores_cy_meses_clean) > 1 else valores_cy_meses_clean
        if len(x_completo) > 0:
            fig.add_trace(go.Scatter(
                x=x_completo,
                y=y_completo,
                name=f'{unidade.upper()} {ano_atual} (Meses)',
                line=dict(color='#00008B', width=2.5, shape='spline', smoothing=1.3),
                mode='lines+markers',
                marker=dict(color='#00008B', size=8, symbol='diamond'),
                connectgaps=False,
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y2',
                showlegend=False
            ))
        fig.add_trace(go.Scatter(
            x=x_parcial,
            y=y_parcial,
            name=f'{unidade.upper()} {ano_atual} (Mês Parcial)',
            line=dict(color='#00008B', width=2.5, dash='dash', shape='spline', smoothing=1.3),
            mode='lines+markers',
            marker=dict(color='#00008B', size=8, symbol='diamond-open'),
            connectgaps=False,
            hovertemplate='%{y:,.0f} (parcial)<extra></extra>',
            yaxis='y2'
        ))
    else:
        fig.add_trace(go.Scatter(
            x=x_meses,
            y=valores_cy_meses_clean,
            name=f'{unidade.upper()} {ano_atual} (Meses)',
            line=dict(color="#0F0F52", width=2.5, shape='spline', smoothing=1.3),
            mode='lines+markers',
            marker=dict(color='#00008B', size=8, symbol='diamond'),
            connectgaps=False,
            hovertemplate='%{y:,.0f}<extra></extra>',
            yaxis='y2'
        ))

    for i, (cy, py, yoy) in enumerate(zip(valores_cy_semanas_clean, valores_py_semanas_clean, yoy_semanas_clean)):
        if cy is not None:
            x_pos = i + 0.5 if i == len(valores_cy_semanas_clean) - 1 else i
            eh_ultima_semana = i == len(valores_cy_semanas_clean) - 1
            yshift_valor = 15 if eh_ultima_semana else 25
            fig.add_annotation(x=x_pos, y=cy, text=formatar_valor(cy, 'numero'), showarrow=False, yshift=yshift_valor, font=dict(size=18, color='black'), yref='y')
            if yoy is not None:
                yshift_yoy = 30 if eh_ultima_semana else 40
                color = 'darkgreen' if yoy > 0 else 'darkred' if yoy < 0 else 'black'
                fig.add_annotation(x=x_pos, y=cy, text=formatar_valor(yoy, 'percentual'), showarrow=False, yshift=yshift_yoy, font=dict(size=16, color=color), yref='y')

    for i, (cy, py, yoy) in enumerate(zip(valores_cy_meses_clean, valores_py_meses_clean, yoy_meses_clean)):
        if cy is not None:
            tem_dados = _is_positive(cy)
            eh_ultimo_com_dados = tem_dados and (i == len([x for x in valores_cy_meses_clean if _is_positive(x)]) - 1)
            x_pos = (i + 7.5) if eh_ultimo_com_dados else (i + 7)
            is_parcial = eh_ultimo_com_dados and dados['mes_parcial_cy']
            valor_texto = formatar_valor(cy, 'numero')
            yshift_valor = 15 if eh_ultimo_com_dados else 25
            fig.add_annotation(x=x_pos, y=cy, text=valor_texto, showarrow=False, yshift=yshift_valor, font=dict(size=18, color='gray' if is_parcial else 'black'), yref='y2')
            if yoy is not None:
                yshift_yoy = 30 if eh_ultimo_com_dados else 40
                color = 'darkgreen' if yoy > 0 else 'darkred' if yoy < 0 else 'black'
                fig.add_annotation(x=x_pos, y=cy, text=formatar_valor(yoy, 'percentual'), showarrow=False, yshift=yshift_yoy, font=dict(size=16, color=color), yref='y2')

    fig.add_vline(x=6, line_width=1, line_dash="solid", line_color="lightgray", opacity=0.5)

    nota_parcial = ""
    if dados['mes_parcial_cy'] and len(dados['meses_cy']) > 0:
        meses_pt = {'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril', 'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'}
        mes_nome_en = dados['meses_cy'].index[-1].strftime('%B')
        mes_nome_pt = meses_pt.get(mes_nome_en, mes_nome_en)
        ultimo_dia_com_dados = pd.Timestamp(data_ref).strftime('%d/%m/%Y')
        nota_parcial = f"<br><sub>{mes_nome_pt} parcial (até {ultimo_dia_com_dados})</sub>"

    # Faixas de eixo seguras contra listas vazias
    def _range_safe(vals):
        nums = []
        for v in vals:
            vf = _to_float(v)
            if vf is not None:
                nums.append(vf)
        if not nums:
            return [0, 1]
        lo = min(nums)
        hi = max(nums)
        if lo == hi:
            return [0, hi * 1.2 if hi != 0 else 1]
        return [lo * 0.85, hi * 1.15]

    fig.update_layout(
        title={'text': titulo + nota_parcial, 'x': 0.5, 'xanchor': 'center', 'font': dict(size=26, color='black')},
        xaxis=dict(
            ticktext=labels_x,
            tickvals=list(range(len(labels_x))),
            tickangle=0,
            gridcolor='rgba(240, 240, 240, 0.5)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=15)
        ),
        yaxis=dict(
            title=dict(text=f'{unidade} Semanais', font=dict(size=16)),
            tickformat='.1s',
            gridcolor='rgba(240, 240, 240, 0.5)',
            showgrid=True,
            zeroline=False,
            range=_range_safe(valores_cy_semanas_clean + valores_py_semanas_clean),
            tickfont=dict(size=14)
        ),
        yaxis2=dict(
            title=dict(text=f'{unidade} Mensais', font=dict(size=16)),
            tickformat='.1s',
            gridcolor='rgba(240, 240, 240, 0.5)',
            showgrid=True,
            zeroline=False,
            overlaying='y',
            side='right',
            range=_range_safe(valores_cy_meses_clean + valores_py_meses_clean),
            tickfont=dict(size=14)
        ),
        hovermode='x unified',
        template='plotly_white',
        height=620,
        width=None,
        autosize=True,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.16, xanchor="center", x=0.5, bordercolor="lightgray", borderwidth=1, font=dict(size=15)),
        margin=dict(t=100, b=220, l=80, r=80),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    kpis = calcular_kpis(df, data_ref)
    kpi_headers = ['LastWk', 'WOW', 'YOY(Semana)', 'MTD', 'YOY(Mês)', 'QTD', 'YOY(Trimestre)', 'YTD', 'YOY(Ano)']
    kpi_values = [
        formatar_valor(kpis['ultima_semana']),
        formatar_valor(kpis['var_semanal'], 'percentual'),
        formatar_valor(kpis['yoy_semanal'], 'percentual'),
        formatar_valor(kpis['mes_atual']),
        formatar_valor(kpis['yoy_mensal'], 'percentual'),
        formatar_valor(kpis['trimestre_atual']),
        formatar_valor(kpis['yoy_trimestral'], 'percentual'),
        formatar_valor(kpis['ano_atual']),
        formatar_valor(kpis['yoy_anual'], 'percentual')
    ]

    for i, (header, value) in enumerate(zip(kpi_headers, kpi_values)):
        x_position = (i + 0.5) / 9
        fig.add_annotation(x=x_position, y=-0.38, xref='paper', yref='paper', text=f"<b>{header}</b>", showarrow=False, font=dict(size=19, color='Black', family='Arial'), align='center', xanchor='center')
        color = 'black'
        if 'YOY' in header or 'WOW' in header:
            try:
                val_num = float(str(value).replace('%', '').replace('+', ''))
                color = 'darkgreen' if val_num > 0 else 'darkred' if val_num < 0 else 'black'
            except Exception:
                pass
        fig.add_annotation(x=x_position, y=-0.44, xref='paper', yref='paper', text=value, showarrow=False, font=dict(size=18, color=color, family='Arial'), align='center', xanchor='center')

    return fig