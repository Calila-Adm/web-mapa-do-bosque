import pandas as pd
import plotly.graph_objects as go
from decimal import Decimal

from .processing import COLUNA_METRICA as _COLUNA_METRICA


def formatar_valor(valor, tipo='numero'):
    if pd.isna(valor):
        return ""
    
    # Converter Decimal para float para formatação
    if isinstance(valor, Decimal):
        valor = float(valor)
    
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
    def _to_decimal(x):
        """Convert to Decimal for calculations"""
        try:
            if pd.isna(x):
                return None
            return Decimal(str(x))
        except Exception:
            return None
    
    def _decimal_to_float(x):
        """Convert Decimal to float for Plotly"""
        if x is None:
            return None
        if isinstance(x, Decimal):
            return float(x)
        return float(x) if x is not None else None

    def _is_positive(x):
        v = _to_decimal(x)
        return v is not None and v > 0
    metrica = _COLUNA_METRICA

    valores_cy_semanas = list(dados['semanas_cy'][metrica].values)
    valores_py_semanas = list(dados['semanas_py'][metrica].values)
    # X dinâmico para semanas (quantas existirem)
    x_semanas = list(range(len(valores_cy_semanas)))

    valores_cy_meses = list(dados['meses_cy'][metrica].values)
    valores_py_meses = list(dados['meses_py'][metrica].values)
    # Garantir sempre 12 meses (Jan–Dez)
    if len(valores_cy_meses) < 12:
        valores_cy_meses += [None] * (12 - len(valores_cy_meses))
    if len(valores_py_meses) < 12:
        valores_py_meses += [None] * (12 - len(valores_py_meses))
    # Começo dos meses = quantidade de semanas + 1 (há um espaçador entre blocos)
    semanas_count = len(x_semanas)
    meses_offset = semanas_count + 1
    x_meses = list(range(meses_offset, meses_offset + 12))

    def _yoy(cy, py):
        cyf = _to_decimal(cy)
        pyf = _to_decimal(py)
        if pyf is None or pyf == 0 or cyf is None:
            return None
        return ((cyf - pyf) / pyf) * 100

    yoy_semanas = [_yoy(cy, py) for cy, py in zip(valores_cy_semanas, valores_py_semanas)]
    yoy_meses = [_yoy(cy, py) for cy, py in zip(valores_cy_meses, valores_py_meses)]

    # Convert to Decimal for calculations, then to float for Plotly
    valores_cy_semanas_clean = [_decimal_to_float(_to_decimal(v)) for v in valores_cy_semanas]
    valores_py_semanas_clean = [_decimal_to_float(_to_decimal(v)) for v in valores_py_semanas]
    valores_cy_meses_clean = [_decimal_to_float(_to_decimal(v)) for v in valores_cy_meses]
    valores_py_meses_clean = [_decimal_to_float(_to_decimal(v)) for v in valores_py_meses]
    yoy_semanas_clean = [_decimal_to_float(_to_decimal(v)) for v in yoy_semanas]
    yoy_meses_clean = [_decimal_to_float(_to_decimal(v)) for v in yoy_meses]

    semanas_do_ano = dados['semanas_cy'].index.isocalendar().week.tolist()
    labels_semanas = [f'Wk {sem}' for sem in semanas_do_ano]

    # Labels de meses baseados no índice para garantir alinhamento 1:1 com os valores
    meses_map = {1: 'JAN', 2: 'FEV', 3: 'MAR', 4: 'ABR', 5: 'MAI', 6: 'JUN', 7: 'JUL', 8: 'AGO', 9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'}
    labels_meses = [meses_map.get(ts.month, ts.strftime('%b').upper()) for ts in dados['meses_cy'].index]

    # Preenche YOY mensal até 12 itens
    while len(yoy_meses) < 12:
        yoy_meses.append(None)

    labels_x = labels_semanas + [''] + labels_meses
    ano_atual = dados.get('ano_atual', data_ref.year)
    ano_anterior = dados.get('ano_anterior', data_ref.year - 1)

    fig = go.Figure()

    # Adiciona trace PY para semanas, considerando se há semana parcial
    semana_parcial = dados.get('semana_parcial', False)
    if semana_parcial and len(valores_py_semanas_clean) > 0:
        # Separa semanas completas da parcial
        x_completo_sem = x_semanas[:-1] if len(x_semanas) > 1 else []
        y_completo_sem = valores_py_semanas_clean[:-1] if len(valores_py_semanas_clean) > 1 else []
        x_parcial_sem = x_semanas[-1:] if len(x_semanas) > 0 else []
        y_parcial_sem = valores_py_semanas_clean[-1:] if len(valores_py_semanas_clean) > 0 else []
        
        # Trace para semanas completas PY
        if len(x_completo_sem) > 0:
            fig.add_trace(go.Scatter(
                x=x_completo_sem,
                y=y_completo_sem,
                name=f'{unidade.upper()} {ano_anterior} (Semanas)',
                line=dict(color="#D685AB", width=1.5),
                mode='lines',
                connectgaps=False,
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y'
            ))
        
        # Trace para semana parcial PY (tracejado)
        if len(x_parcial_sem) > 0:
            # Adiciona apenas o ponto parcial
            fig.add_trace(go.Scatter(
                x=x_parcial_sem,
                y=y_parcial_sem,
                name=f'{unidade.upper()} {ano_anterior}',  # Removido "(Semana Parcial)"
                mode='markers',  # Apenas marcador
                marker=dict(color="#D685AB", size=6),
                connectgaps=False,
                hovertemplate='%{y:,.0f} (parcial)<extra></extra>',
                yaxis='y',
                showlegend=False
            ))
            
            # Linha tracejada conectando
            if len(x_completo_sem) > 0:
                fig.add_trace(go.Scatter(
                    x=[x_completo_sem[-1], x_parcial_sem[0]],
                    y=[y_completo_sem[-1], y_parcial_sem[0]],
                    line=dict(color="#D685AB", width=1.5, dash='dash'),
                    mode='lines',
                    connectgaps=False,
                    hoverinfo='skip',
                    yaxis='y',
                    showlegend=False
                ))
    else:
        # Sem semana parcial - trace normal
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

    # Adiciona trace CY para semanas, considerando se há semana parcial
    if semana_parcial and len(valores_cy_semanas_clean) > 0:
        # Separa semanas completas da parcial
        x_completo_cy = x_semanas[:-1] if len(x_semanas) > 1 else []
        y_completo_cy = valores_cy_semanas_clean[:-1] if len(valores_cy_semanas_clean) > 1 else []
        x_parcial_cy = x_semanas[-1:] if len(x_semanas) > 0 else []
        y_parcial_cy = valores_cy_semanas_clean[-1:] if len(valores_cy_semanas_clean) > 0 else []
        
        # Trace para semanas completas CY
        if len(x_completo_cy) > 0:
            fig.add_trace(go.Scatter(
                x=x_completo_cy,
                y=y_completo_cy,
                name=f'{unidade.upper()} {ano_atual} (Semanas)',
                line=dict(color="#000075", width=2.5, shape='spline', smoothing=1.3),
                mode='lines+markers',
                marker=dict(color='#00008B', size=8, symbol='diamond'),
                connectgaps=False,
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y'
            ))
        
        # Trace para semana parcial CY (tracejado com marcador aberto)
        if len(x_parcial_cy) > 0:
            # Para evitar tooltip duplicado, só adiciona o ponto parcial
            fig.add_trace(go.Scatter(
                x=x_parcial_cy,
                y=y_parcial_cy,
                name=f'{unidade.upper()} {ano_atual}',  # Removido "(Semana Parcial)"
                line=dict(color="#000075", width=2.5, dash='dash'),
                mode='markers',  # Apenas marcador, sem linha
                marker=dict(color='#00008B', size=8, symbol='diamond-open'),
                connectgaps=False,
                hovertemplate='%{y:,.0f} (parcial)<extra></extra>',
                yaxis='y',
                showlegend=False  # Oculta da legenda para não duplicar
            ))
            
            # Adiciona linha tracejada conectando com a semana anterior
            if len(x_completo_cy) > 0:
                fig.add_trace(go.Scatter(
                    x=[x_completo_cy[-1], x_parcial_cy[0]],
                    y=[y_completo_cy[-1], y_parcial_cy[0]],
                    line=dict(color="#000075", width=2.5, dash='dash'),
                    mode='lines',
                    connectgaps=False,
                    hoverinfo='skip',  # Sem hover para evitar duplicação
                    yaxis='y',
                    showlegend=False
                ))
    else:
        # Sem semana parcial - trace normal
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

    # Adiciona trace PY para meses, considerando se há mês parcial
    if dados.get('mes_parcial_py', False) and any(not pd.isna(v) for v in valores_py_meses):
        # Encontra o índice do último mês com dados PY (mês parcial)
        ultimo_mes_com_dados_py = -1
        for i in range(len(valores_py_meses_clean)):
            if valores_py_meses_clean[i] is not None and not pd.isna(valores_py_meses_clean[i]):
                ultimo_mes_com_dados_py = i
        
        if ultimo_mes_com_dados_py >= 0:
            # Separa meses completos do parcial para PY
            x_completo_py = x_meses[:ultimo_mes_com_dados_py]
            y_completo_py = valores_py_meses_clean[:ultimo_mes_com_dados_py]
            x_parcial_py = [x_meses[ultimo_mes_com_dados_py]]
            y_parcial_py = [valores_py_meses_clean[ultimo_mes_com_dados_py]]
            
            # Trace para meses completos PY
            if len(x_completo_py) > 0:
                fig.add_trace(go.Scatter(
                    x=x_completo_py,
                    y=y_completo_py,
                    name=f'{unidade.upper()} {ano_anterior} (Meses)',
                    line=dict(color="#D685AB", width=1.5),
                    mode='lines',
                    connectgaps=False,
                    hovertemplate='%{y:,.0f}<extra></extra>',
                    yaxis='y2'
                ))
            
            # Trace para o mês parcial PY (apenas o ponto)
            if len(x_parcial_py) > 0:
                fig.add_trace(go.Scatter(
                    x=x_parcial_py,
                    y=y_parcial_py,
                    name=f'{unidade.upper()} {ano_anterior} (Meses)',
                    mode='markers',
                    marker=dict(color="#D685AB", size=6),
                    connectgaps=False,
                    hovertemplate='%{y:,.0f} (parcial)<extra></extra>',
                    yaxis='y2',
                    showlegend=False
                ))
                
                # Linha tracejada conectando ao mês anterior
                if len(x_completo_py) > 0:
                    fig.add_trace(go.Scatter(
                        x=[x_completo_py[-1], x_parcial_py[0]],
                        y=[y_completo_py[-1], y_parcial_py[0]],
                        line=dict(color="#D685AB", width=1.5, dash='dash'),
                        mode='lines',
                        connectgaps=False,
                        hoverinfo='skip',
                        yaxis='y2',
                        showlegend=False
                    ))
        else:
            # Sem dados - não adiciona trace
            pass
    else:
        # Sem mês parcial PY - trace normal
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
        # Encontra o índice do último mês com dados (mês parcial)
        ultimo_mes_com_dados = -1
        for i in range(len(valores_cy_meses_clean)):
            if valores_cy_meses_clean[i] is not None and not pd.isna(valores_cy_meses_clean[i]):
                ultimo_mes_com_dados = i
        
        # Separa meses completos do parcial
        if ultimo_mes_com_dados >= 0:
            x_completo = x_meses[:ultimo_mes_com_dados]
            y_completo = valores_cy_meses_clean[:ultimo_mes_com_dados]
            x_parcial = [x_meses[ultimo_mes_com_dados]]  # Apenas o mês parcial
            y_parcial = [valores_cy_meses_clean[ultimo_mes_com_dados]]
        else:
            x_completo = []
            y_completo = []
            x_parcial = []
            y_parcial = []
        
        # Trace para meses completos (sem conectar ao mês parcial)
        if len(x_completo) > 0:
            fig.add_trace(go.Scatter(
                x=x_completo,
                y=y_completo,
                name=f'{unidade.upper()} {ano_atual} (Meses)',
                line=dict(color='#00008B', width=2.5),  # Removido spline para não interferir
                mode='lines+markers',
                marker=dict(color='#00008B', size=8, symbol='diamond'),
                connectgaps=False,
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y2',
                showlegend=True  # Mostra na legenda já que é a linha principal
            ))
        
        # Trace para o mês parcial (apenas o ponto com marcador aberto)
        if len(x_parcial) > 0:
            fig.add_trace(go.Scatter(
                x=x_parcial,
                y=y_parcial,
                name=f'{unidade.upper()} {ano_atual} (Meses)',  # Nome consistente
                mode='markers',  # Apenas marcador
                marker=dict(color='#00008B', size=8, symbol='diamond-open'),
                connectgaps=False,
                hovertemplate='%{y:,.0f} (parcial)<extra></extra>',
                yaxis='y2',
                showlegend=False  # Oculta para não duplicar na legenda
            ))
            
            # Linha tracejada conectando ao mês anterior
            if len(x_completo) > 0:
                fig.add_trace(go.Scatter(
                    x=[x_completo[-1], x_parcial[0]],
                    y=[y_completo[-1], y_parcial[0]],
                    line=dict(color='#00008B', width=2.5, dash='dash'),
                    mode='lines',
                    connectgaps=False,
                    hoverinfo='skip',  # Sem hover para evitar duplicação
                    yaxis='y2',
                    showlegend=False
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
            x_pos = (i + meses_offset + 0.5) if eh_ultimo_com_dados else (i + meses_offset)
            is_parcial = eh_ultimo_com_dados and dados['mes_parcial_cy']
            valor_texto = formatar_valor(cy, 'numero')
            yshift_valor = 15 if eh_ultimo_com_dados else 25
            fig.add_annotation(x=x_pos, y=cy, text=valor_texto, showarrow=False, yshift=yshift_valor, font=dict(size=18, color='gray' if is_parcial else 'black'), yref='y2')
            if yoy is not None:
                yshift_yoy = 30 if eh_ultimo_com_dados else 40
                color = 'darkgreen' if yoy > 0 else 'darkred' if yoy < 0 else 'black'
                fig.add_annotation(x=x_pos, y=cy, text=formatar_valor(yoy, 'percentual'), showarrow=False, yshift=yshift_yoy, font=dict(size=16, color=color), yref='y2')

    # Linha separadora entre semanas e meses na posição dinâmica
    fig.add_vline(x=semanas_count, line_width=1, line_dash="solid", line_color="lightgray", opacity=0.5)

    nota_parcial = ""
    if dados['mes_parcial_cy'] and len(dados['meses_cy']) > 0:
        # Usa o mês da data de referência para a legenda de mês parcial
        meses_pt_num = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        data_ref_ts = pd.Timestamp(data_ref)
        mes_nome_pt = meses_pt_num.get(data_ref_ts.month, data_ref_ts.strftime('%B'))
        ultimo_dia_com_dados = data_ref_ts.strftime('%d/%m/%Y')
        nota_parcial = f"<br><sub>{mes_nome_pt} parcial (até {ultimo_dia_com_dados})</sub>"

    # Faixas de eixo seguras contra listas vazias
    def _range_safe(vals):
        nums = []
        for v in vals:
            # vals já são float devido à conversão anterior
            if v is not None:
                nums.append(v)
        if not nums:
            return [0, 1]
        lo = min(nums)
        hi = max(nums)
        if lo == hi:
            return [0, hi * 1.2 if hi != 0 else 1]
        return [lo * 0.85, hi * 1.15]

    fig.update_layout(
        title={'text': titulo + nota_parcial, 'x': 0.5, 'xanchor': 'center', 'font': dict(size=20, color='black')},
        xaxis=dict(
            ticktext=labels_x,
            tickvals=list(range(len(labels_x))),
            tickangle=-45 if len(labels_x) > 10 else 0,  # Rotaciona labels se muitos pontos
            gridcolor='rgba(240, 240, 240, 0.5)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=11)
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
        height=500,  # Altura menor para caber melhor em layouts múltiplos
        width=None,  # Largura automática
        autosize=True,  # Permite redimensionamento automático
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.16, xanchor="center", x=0.5, bordercolor="lightgray", borderwidth=1, font=dict(size=11)),
        margin=dict(t=60, b=80, l=50, r=50),  # Margem inferior reduzida - KPIs removidos
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Calculate KPIs directly from the same weekly data used in the graph
    # This ensures consistency between graph and KPI values
    
    # Get the last week value from the same data shown in the graph
    ultima_semana = valores_cy_semanas[-1] if valores_cy_semanas else 0
    
    # Previous week for WOW calculation
    semana_anterior = valores_cy_semanas[-2] if len(valores_cy_semanas) > 1 else 0
    
    # Last week from previous year for YOY
    ultima_semana_py = valores_py_semanas[-1] if valores_py_semanas else 0
    
    # Calculate WOW (Week over Week)
    wow_pct = 0
    if semana_anterior and semana_anterior != 0:
        wow_pct = ((ultima_semana / semana_anterior - 1) * 100) if ultima_semana else 0
    
    # Calculate YOY for week
    yoy_semanal = 0
    if ultima_semana_py and ultima_semana_py != 0:
        yoy_semanal = ((ultima_semana / ultima_semana_py - 1) * 100) if ultima_semana else 0
    
    # MTD - Month-to-Date (apenas o mês atual da data de referência)
    mes_ref = data_ref.month
    mtd_atual = valores_cy_meses_clean[mes_ref - 1] if mes_ref <= len(valores_cy_meses_clean) and valores_cy_meses_clean[mes_ref - 1] is not None else 0
    mtd_py = valores_py_meses_clean[mes_ref - 1] if mes_ref <= len(valores_py_meses_clean) and valores_py_meses_clean[mes_ref - 1] is not None else 0
    
    yoy_mensal = 0
    if mtd_py and mtd_py != 0:
        yoy_mensal = ((mtd_atual / mtd_py - 1) * 100) if mtd_atual else 0
    
    # QTD - Quarter-to-Date (soma dos meses do trimestre atual)
    trimestre = (mes_ref - 1) // 3 + 1  # 1, 2, 3 ou 4
    inicio_trim = (trimestre - 1) * 3  # 0, 3, 6 ou 9
    fim_trim = min(inicio_trim + 3, mes_ref)  # Não passar do mês atual
    
    qtd_atual = sum(valores_cy_meses_clean[i] for i in range(inicio_trim, fim_trim) 
                    if i < len(valores_cy_meses_clean) and valores_cy_meses_clean[i] is not None)
    qtd_py = sum(valores_py_meses_clean[i] for i in range(inicio_trim, fim_trim)
                 if i < len(valores_py_meses_clean) and valores_py_meses_clean[i] is not None)
    
    yoy_trimestral = 0
    if qtd_py and qtd_py != 0:
        yoy_trimestral = ((qtd_atual / qtd_py - 1) * 100) if qtd_atual else 0
    
    # YTD - Year-to-Date (soma de todos os meses do ano até o mês atual)
    ytd_atual = sum(v for v in valores_cy_meses_clean[:mes_ref] if v is not None and not pd.isna(v))
    ytd_py = sum(v for v in valores_py_meses_clean[:mes_ref] if v is not None and not pd.isna(v))
    
    yoy_anual = 0
    if ytd_py and ytd_py != 0:
        yoy_anual = ((ytd_atual / ytd_py - 1) * 100) if ytd_atual else 0
    
    kpi_headers = ['LastWk', 'WOW', 'YOY(Semana)', 'MTD', 'YOY(Mês)', 'QTD', 'YOY(Trimestre)', 'YTD', 'YOY(Ano)']
    kpi_values = [
        formatar_valor(ultima_semana),
        formatar_valor(wow_pct, 'percentual'),
        formatar_valor(yoy_semanal, 'percentual'),
        formatar_valor(mtd_atual),
        formatar_valor(yoy_mensal, 'percentual'),
        formatar_valor(qtd_atual),
        formatar_valor(yoy_trimestral, 'percentual'),
        formatar_valor(ytd_atual),
        formatar_valor(yoy_anual, 'percentual')
    ]

    # KPIs removidos do gráfico conforme solicitado
    # Os cálculos são mantidos mas as anotações visuais foram removidas

    return fig