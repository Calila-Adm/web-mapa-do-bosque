"""
Módulo de funções modulares para criação de gráficos WBR
Separa a lógica de visualização semanal e mensal em funções distintas
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal
import numpy as np


def formatar_valor(valor: float, tipo: str = 'numero') -> str:
    """
    Formata valores para exibição no gráfico.

    Args:
        valor: Valor numérico a ser formatado
        tipo: Tipo de formatação ('numero' ou 'percentual')

    Returns:
        String formatada do valor
    """
    if pd.isna(valor):
        return ""

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


def calcular_yoy(valor_cy: float, valor_py: float) -> Optional[float]:
    """
    Calcula variação Year-over-Year.

    Args:
        valor_cy: Valor do ano atual
        valor_py: Valor do ano anterior

    Returns:
        Percentual YoY ou None se não calculável
    """
    if pd.isna(valor_cy) or pd.isna(valor_py) or valor_py == 0:
        return None
    return ((valor_cy - valor_py) / valor_py) * 100


def criar_grafico_semanal_wbr(
    dados: Dict[str, Any],
    metrica: str = 'metric_value',
    unidade: str = 'valor',
    ano_atual: int = 2024,
    ano_anterior: int = 2023
) -> Tuple[go.Figure, Dict[str, Any]]:
    """
    Cria gráfico WBR para visualização semanal com comparação YoY.

    Args:
        dados: Dicionário com dados processados contendo 'semanas_cy' e 'semanas_py'
        metrica: Nome da coluna de métrica
        unidade: Unidade de medida para labels
        ano_atual: Ano atual para label
        ano_anterior: Ano anterior para label

    Returns:
        Tupla com (Figura Plotly, Dicionário de traces para combinação)
    """
    fig = go.Figure()

    # Extrair dados
    valores_cy = list(dados['semanas_cy'][metrica].values)
    valores_py = list(dados['semanas_py'][metrica].values)

    # Pegar as datas de fim de semana (week ending) para labels DD/MM
    datas_semanas = dados['semanas_cy'].index

    # Labels e posições X - usar formato DD/MM ao invés de Wk XX
    x_semanas = list(range(len(valores_cy)))
    labels_semanas = [data.strftime('%d/%m') for data in datas_semanas]

    # Calcular YoY semanal
    yoy_semanas = [calcular_yoy(cy, py) for cy, py in zip(valores_cy, valores_py)]

    # Detectar semana parcial
    semana_parcial = dados.get('semana_parcial', False)

    # Trace PY (Ano Anterior) - Semanas
    fig.add_trace(go.Scatter(
        x=x_semanas,
        y=valores_py,
        name=f'{unidade.upper()} {ano_anterior} (Semanas)',
        line=dict(color="#D685AB", width=1.5, shape='linear'),  # Mudado de 'spline' para 'linear'
        mode='lines',
        connectgaps=False,
        hovertemplate='%{y:,.0f}<extra></extra>',
        yaxis='y'
    ))

    # Marcador para semana parcial se houver
    if semana_parcial and len(valores_py) > 0:
        fig.add_trace(go.Scatter(
            x=x_semanas[-1:],
            y=valores_py[-1:],
            mode='markers',
            marker=dict(color="#D685AB", size=6, symbol='circle-open'),
            hoverinfo='skip',  # Não mostra tooltip para o marcador parcial
            yaxis='y',
            showlegend=False
        ))

    # Trace CY (Ano Atual) - Semanas
    fig.add_trace(go.Scatter(
        x=x_semanas,
        y=valores_cy,
        name=f'{unidade.upper()} {ano_atual} (Semanas)',
        line=dict(color="#000075", width=2.5, shape='spline', smoothing=1.0),
        mode='lines+markers',
        marker=dict(color='#00008B', size=8, symbol='diamond'),
        connectgaps=False,
        hovertemplate='%{y:,.0f}<extra></extra>',
        yaxis='y'
    ))

    # Marcador especial para semana parcial se houver
    if semana_parcial and len(valores_cy) > 0:
        fig.add_trace(go.Scatter(
            x=x_semanas[-1:],
            y=valores_cy[-1:],
            mode='markers',
            marker=dict(color='#00008B', size=8, symbol='diamond-open'),
            hoverinfo='skip',  # Não mostra tooltip para o marcador parcial
            yaxis='y',
            showlegend=False
        ))

    # Adicionar anotações de valores e YoY
    for i, (cy, py, yoy) in enumerate(zip(valores_cy, valores_py, yoy_semanas)):
        if cy is not None and not pd.isna(cy):
            # Ajuste de posição para última semana parcial
            eh_ultima = i == len(valores_cy) - 1
            x_pos = i + 0.5 if eh_ultima and semana_parcial else i
            yshift_valor = 15 if eh_ultima else 25

            # Valor absoluto
            fig.add_annotation(
                x=x_pos,
                y=cy,
                text=formatar_valor(cy, 'numero'),
                showarrow=False,
                yshift=yshift_valor,
                font=dict(size=18, color='black'),
                yref='y'
            )

            # YoY
            if yoy is not None:
                yshift_yoy = 30 if eh_ultima else 40
                color = 'darkgreen' if yoy > 0 else 'darkred' if yoy < 0 else 'black'
                fig.add_annotation(
                    x=x_pos,
                    y=cy,
                    text=formatar_valor(yoy, 'percentual'),
                    showarrow=False,
                    yshift=yshift_yoy,
                    font=dict(size=16, color=color),
                    yref='y'
                )

    # Calcular range seguro para eixo Y
    todos_valores = valores_cy + valores_py
    valores_validos = [v for v in todos_valores if v is not None and not pd.isna(v)]
    if valores_validos:
        min_val = min(valores_validos)
        max_val = max(valores_validos)
        y_range = [min_val * 0.85, max_val * 1.15]
    else:
        y_range = [0, 1]

    # Configuração do layout
    fig.update_layout(
        xaxis=dict(
            ticktext=labels_semanas,
            tickvals=x_semanas,
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
            range=y_range,
            tickfont=dict(size=14)
        ),
        hovermode='x unified',
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            xanchor="center",
            x=0.5,
            bordercolor="lightgray",
            borderwidth=1,
            font=dict(size=11)
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Retornar dados para KPIs
    kpis_semanas = {
        'ultima_semana_cy': valores_cy[-1] if valores_cy else 0,
        'ultima_semana_py': valores_py[-1] if valores_py else 0,
        'penultima_semana_cy': valores_cy[-2] if len(valores_cy) > 1 else 0,
        'yoy_semanal': yoy_semanas[-1] if yoy_semanas else 0
    }

    return fig, kpis_semanas


def criar_grafico_mensal_wbr(
    dados: Dict[str, Any],
    metrica: str = 'metric_value',
    unidade: str = 'valor',
    ano_atual: int = 2024,
    ano_anterior: int = 2023,
    offset_x: int = 7
) -> Tuple[go.Figure, Dict[str, Any]]:
    """
    Cria gráfico WBR para visualização mensal com comparação YoY.

    Args:
        dados: Dicionário com dados processados contendo 'meses_cy' e 'meses_py'
        metrica: Nome da coluna de métrica
        unidade: Unidade de medida para labels
        ano_atual: Ano atual para label
        ano_anterior: Ano anterior para label
        offset_x: Deslocamento no eixo X para separar de gráfico semanal

    Returns:
        Tupla com (Figura Plotly, Dicionário de KPIs mensais)
    """
    fig = go.Figure()

    # Extrair dados
    valores_cy_meses = list(dados['meses_cy'][metrica].values)
    valores_py_meses = list(dados['meses_py'][metrica].values)

    # Garantir 12 meses
    while len(valores_cy_meses) < 12:
        valores_cy_meses.append(None)
    while len(valores_py_meses) < 12:
        valores_py_meses.append(None)

    # Posições X e labels
    x_meses = list(range(offset_x, offset_x + 12))
    meses_map = {
        1: 'JAN', 2: 'FEV', 3: 'MAR', 4: 'ABR',
        5: 'MAI', 6: 'JUN', 7: 'JUL', 8: 'AGO',
        9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'
    }
    labels_meses = [meses_map.get(i+1) for i in range(12)]

    # Calcular YoY mensal
    yoy_meses = [calcular_yoy(cy, py) for cy, py in zip(valores_cy_meses, valores_py_meses)]

    # Detectar mês parcial
    mes_parcial_cy = dados.get('mes_parcial_cy', False)
    mes_parcial_py = dados.get('mes_parcial_py', False)

    # Encontrar último mês com dados
    ultimo_mes_cy = -1
    for i in range(len(valores_cy_meses)):
        if valores_cy_meses[i] is not None and not pd.isna(valores_cy_meses[i]):
            ultimo_mes_cy = i

    ultimo_mes_py = -1
    for i in range(len(valores_py_meses)):
        if valores_py_meses[i] is not None and not pd.isna(valores_py_meses[i]):
            ultimo_mes_py = i

    # Trace PY (Ano Anterior) - Meses
    # Filtrar apenas valores não-nulos para desenhar a linha
    indices_validos_py = [i for i, v in enumerate(valores_py_meses) if v is not None and not pd.isna(v)]

    if mes_parcial_py and ultimo_mes_py >= 0 and len(indices_validos_py) > 0:
        # Se há mês parcial, desenha linha até o mês anterior completo
        if ultimo_mes_py > 0:
            # Linha sólida até o penúltimo mês
            x_validos = [x_meses[i] for i in indices_validos_py if i < ultimo_mes_py]
            y_validos = [valores_py_meses[i] for i in indices_validos_py if i < ultimo_mes_py]

            if x_validos:
                fig.add_trace(go.Scatter(
                    x=x_validos,
                    y=y_validos,
                    name=f'{unidade.upper()} {ano_anterior} (Meses)',
                    line=dict(color="#D685AB", width=1.5, shape='linear'),  # Mudado para linear
                    mode='lines',
                    connectgaps=False,
                    hovertemplate='%{y:,.0f}<extra></extra>',
                    yaxis='y2'
                ))

            # Linha tracejada para o último mês (parcial)
            fig.add_trace(go.Scatter(
                x=[x_meses[ultimo_mes_py-1], x_meses[ultimo_mes_py]],
                y=[valores_py_meses[ultimo_mes_py-1], valores_py_meses[ultimo_mes_py]],
                line=dict(color="#D685AB", width=1.5, dash='dash'),
                mode='lines',
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y2',
                showlegend=False
            ))
        else:
            # Se só há um mês e é parcial, mostra apenas como tracejado
            fig.add_trace(go.Scatter(
                x=[x_meses[0]],
                y=[valores_py_meses[0]],
                mode='markers',
                marker=dict(color="#D685AB", size=6),
                hovertemplate='%{y:,.0f} (parcial)<extra></extra>',
                yaxis='y2',
                showlegend=False
            ))
    else:
        # Linha completa se não há mês parcial
        # Filtrar apenas valores não-nulos para desenhar a linha
        x_validos = [x_meses[i] for i in indices_validos_py]
        y_validos = [valores_py_meses[i] for i in indices_validos_py]

        if x_validos:
            fig.add_trace(go.Scatter(
                x=x_validos,
                y=y_validos,
                name=f'{unidade.upper()} {ano_anterior} (Meses)',
                line=dict(color="#D685AB", width=1.5, shape='linear'),  # Mudado para linear
                mode='lines',
                connectgaps=False,
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y2'
            ))

    # Trace CY (Ano Atual) - Meses
    # Filtrar apenas valores não-nulos para desenhar a linha
    indices_validos_cy = [i for i, v in enumerate(valores_cy_meses) if v is not None and not pd.isna(v)]

    if mes_parcial_cy and ultimo_mes_cy >= 0 and len(indices_validos_cy) > 0:
        # Se há mês parcial, desenha linha até o mês anterior completo
        if ultimo_mes_cy > 0:
            # Linha sólida até o penúltimo mês
            x_validos = [x_meses[i] for i in indices_validos_cy if i < ultimo_mes_cy]
            y_validos = [valores_cy_meses[i] for i in indices_validos_cy if i < ultimo_mes_cy]

            if x_validos:
                fig.add_trace(go.Scatter(
                    x=x_validos,
                    y=y_validos,
                    name=f'{unidade.upper()} {ano_atual} (Meses)',
                    line=dict(color="#00008B", width=2.5, shape='spline', smoothing=1.0),
                    mode='lines+markers',
                    marker=dict(color='#00008B', size=8, symbol='diamond'),
                    connectgaps=False,
                    hovertemplate='%{y:,.0f}<extra></extra>',
                    yaxis='y2'
                ))

            # Linha tracejada para o último mês (parcial)
            fig.add_trace(go.Scatter(
                x=[x_meses[ultimo_mes_cy-1], x_meses[ultimo_mes_cy]],
                y=[valores_cy_meses[ultimo_mes_cy-1], valores_cy_meses[ultimo_mes_cy]],
                line=dict(color='#00008B', width=2.5, dash='dash'),
                mode='lines+markers',
                marker=dict(color='#00008B', size=8, symbol='diamond-open'),
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y2',
                showlegend=False
            ))
        else:
            # Se só há um mês e é parcial, mostra apenas como marcador
            fig.add_trace(go.Scatter(
                x=[x_meses[0]],
                y=[valores_cy_meses[0]],
                mode='markers',
                marker=dict(color='#00008B', size=8, symbol='diamond-open'),
                hovertemplate='%{y:,.0f} (parcial)<extra></extra>',
                yaxis='y2',
                showlegend=False
            ))
    else:
        # Linha completa se não há mês parcial (data de referência é o último dia do mês)
        # Filtrar apenas valores não-nulos para desenhar a linha
        x_validos = [x_meses[i] for i in indices_validos_cy]
        y_validos = [valores_cy_meses[i] for i in indices_validos_cy]

        if x_validos:
            fig.add_trace(go.Scatter(
                x=x_validos,
                y=y_validos,
                name=f'{unidade.upper()} {ano_atual} (Meses)',
                line=dict(color="#00008B", width=2.5, shape='spline', smoothing=1.0),
                mode='lines+markers',
                marker=dict(color='#00008B', size=8, symbol='diamond'),
                connectgaps=False,
                hovertemplate='%{y:,.0f}<extra></extra>',
                yaxis='y2'
            ))

    # Adicionar anotações mensais
    for i, (cy, py, yoy) in enumerate(zip(valores_cy_meses, valores_py_meses, yoy_meses)):
        if cy is not None and not pd.isna(cy):
            eh_ultimo = i == ultimo_mes_cy and mes_parcial_cy
            x_pos = x_meses[i] + 0.5 if eh_ultimo else x_meses[i]
            yshift_valor = 15 if eh_ultimo else 25

            # Valor absoluto
            fig.add_annotation(
                x=x_pos,
                y=cy,
                text=formatar_valor(cy, 'numero'),
                showarrow=False,
                yshift=yshift_valor,
                font=dict(size=18, color='gray' if eh_ultimo else 'black'),
                yref='y2'
            )

            # YoY
            if yoy is not None:
                yshift_yoy = 30 if eh_ultimo else 40
                color = 'darkgreen' if yoy > 0 else 'darkred' if yoy < 0 else 'black'
                fig.add_annotation(
                    x=x_pos,
                    y=cy,
                    text=formatar_valor(yoy, 'percentual'),
                    showarrow=False,
                    yshift=yshift_yoy,
                    font=dict(size=16, color=color),
                    yref='y2'
                )

    # Calcular range para eixo Y2
    todos_valores = valores_cy_meses + valores_py_meses
    valores_validos = [v for v in todos_valores if v is not None and not pd.isna(v)]
    if valores_validos:
        min_val = min(valores_validos)
        max_val = max(valores_validos)
        y_range = [min_val * 0.85, max_val * 1.15]
    else:
        y_range = [0, 1]

    # Configuração do layout
    fig.update_layout(
        xaxis=dict(
            ticktext=labels_meses,
            tickvals=x_meses,
            gridcolor='rgba(240, 240, 240, 0.5)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=11)
        ),
        yaxis2=dict(
            title=dict(text=f'{unidade} Mensais', font=dict(size=16)),
            tickformat='.1s',
            gridcolor='rgba(240, 240, 240, 0.5)',
            showgrid=True,
            zeroline=False,
            overlaying='y',
            side='right',
            range=y_range,
            tickfont=dict(size=14)
        ),
        hovermode='x unified',
        template='plotly_white',
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Calcular KPIs mensais
    mes_atual = ultimo_mes_cy + 1 if ultimo_mes_cy >= 0 else 0

    # MTD (Month-to-Date)
    mtd_cy = valores_cy_meses[ultimo_mes_cy] if ultimo_mes_cy >= 0 else 0
    mtd_py = valores_py_meses[ultimo_mes_cy] if ultimo_mes_cy >= 0 and ultimo_mes_cy < len(valores_py_meses) else 0

    # QTD (Quarter-to-Date)
    trimestre = (mes_atual - 1) // 3 + 1
    inicio_trim = (trimestre - 1) * 3
    fim_trim = min(inicio_trim + 3, mes_atual)

    qtd_cy = sum(valores_cy_meses[i] for i in range(inicio_trim, fim_trim)
                 if i < len(valores_cy_meses) and valores_cy_meses[i] is not None)
    qtd_py = sum(valores_py_meses[i] for i in range(inicio_trim, fim_trim)
                 if i < len(valores_py_meses) and valores_py_meses[i] is not None)

    # YTD (Year-to-Date)
    ytd_cy = sum(v for v in valores_cy_meses[:mes_atual] if v is not None and not pd.isna(v))
    ytd_py = sum(v for v in valores_py_meses[:mes_atual] if v is not None and not pd.isna(v))

    kpis_meses = {
        'mtd_cy': mtd_cy,
        'mtd_py': mtd_py,
        'mtd_yoy': calcular_yoy(mtd_cy, mtd_py),
        'qtd_cy': qtd_cy,
        'qtd_py': qtd_py,
        'qtd_yoy': calcular_yoy(qtd_cy, qtd_py),
        'ytd_cy': ytd_cy,
        'ytd_py': ytd_py,
        'ytd_yoy': calcular_yoy(ytd_cy, ytd_py),
        'mes_atual': mes_atual
    }

    return fig, kpis_meses


def combinar_graficos_wbr(
    fig_semanal: go.Figure,
    fig_mensal: go.Figure,
    titulo: str,
    data_referencia: pd.Timestamp,
    kpis_semanas: Dict[str, Any],
    kpis_meses: Dict[str, Any]
) -> go.Figure:
    """
    Combina os gráficos semanal e mensal em uma única visualização.

    Args:
        fig_semanal: Figura com gráfico semanal
        fig_mensal: Figura com gráfico mensal
        titulo: Título do gráfico combinado
        data_referencia: Data para análise
        kpis_semanas: KPIs calculados da visualização semanal
        kpis_meses: KPIs calculados da visualização mensal

    Returns:
        Figura Plotly combinada com ambas visualizações
    """
    # Criar nova figura combinada
    fig_combinado = go.Figure()

    # Adicionar todos os traces do gráfico semanal
    for trace in fig_semanal.data:
        fig_combinado.add_trace(trace)

    # Adicionar todos os traces do gráfico mensal
    for trace in fig_mensal.data:
        fig_combinado.add_trace(trace)

    # IMPORTANTE: Adicionar as anotações das figuras originais
    # Copiar anotações do gráfico semanal
    if hasattr(fig_semanal.layout, 'annotations') and fig_semanal.layout.annotations:
        for annotation in fig_semanal.layout.annotations:
            # Converter annotation para dicionário corretamente
            annotation_dict = annotation.to_plotly_json()
            fig_combinado.add_annotation(annotation_dict)

    # Copiar anotações do gráfico mensal
    if hasattr(fig_mensal.layout, 'annotations') and fig_mensal.layout.annotations:
        for annotation in fig_mensal.layout.annotations:
            # Converter annotation para dicionário corretamente
            annotation_dict = annotation.to_plotly_json()
            fig_combinado.add_annotation(annotation_dict)

    # Adicionar linha separadora entre semanas e meses
    fig_combinado.add_vline(
        x=6,  # Posição após as 6 semanas
        line_width=1,
        line_dash="solid",
        line_color="lightgray",
        opacity=0.5
    )

    # Preparar título com nota de período
    nota_parcial = ""
    if kpis_meses.get('mes_atual') and data_referencia:
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        mes_nome = meses_pt.get(data_referencia.month, data_referencia.strftime('%B'))

        # Verificar se é o último dia do mês
        ultimo_dia_mes = (data_referencia.replace(day=1) + pd.offsets.MonthEnd(1)).day
        dia_atual = data_referencia.day

        if dia_atual == ultimo_dia_mes:
            # É o fechamento do mês - não mostrar nada
            nota_parcial = ""
        else:
            # É um mês parcial
            data_formatada = data_referencia.strftime('%d/%m/%Y')
            nota_parcial = f"<br><sub>{mes_nome} parcial (até {data_formatada})</sub>"

    # Combinar labels do eixo X
    labels_semanas = fig_semanal.layout.xaxis.ticktext
    labels_meses = fig_mensal.layout.xaxis.ticktext

    # Garantir que sempre temos 12 meses nos labels
    if labels_meses is None or len(labels_meses) < 12:
        meses_map = {
            1: 'JAN', 2: 'FEV', 3: 'MAR', 4: 'ABR',
            5: 'MAI', 6: 'JUN', 7: 'JUL', 8: 'AGO',
            9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'
        }
        labels_meses = [meses_map[i] for i in range(1, 13)]

    # Combinar labels: 6 semanas + espaço + 12 meses
    labels_combinados = list(labels_semanas) + [''] + list(labels_meses)
    tickvals_combinados = list(range(len(labels_combinados)))

    # Configuração do layout combinado
    fig_combinado.update_layout(
        title={
            'text': titulo + nota_parcial,
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=20, color='black')
        },
        xaxis=dict(
            ticktext=labels_combinados,
            tickvals=tickvals_combinados,
            tickangle=-45 if len(labels_combinados) > 10 else 0,
            gridcolor='rgba(240, 240, 240, 0.5)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=11)
        ),
        yaxis=fig_semanal.layout.yaxis,
        yaxis2=fig_mensal.layout.yaxis2,
        hovermode='x unified',
        template='plotly_white',
        height=500,
        autosize=True,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            xanchor="center",
            x=0.5,
            bordercolor="lightgray",
            borderwidth=1,
            font=dict(size=11)
        ),
        margin=dict(t=60, b=150, l=50, r=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Adicionar KPIs na barra inferior
    kpis_headers = ['LastWk', 'WOW', 'YOY(Sem)', 'MTD', 'YOY(Mês)', 'QTD', 'YOY(Tri)', 'YTD', 'YOY(Ano)']

    # Calcular WOW
    wow_pct = 0
    if kpis_semanas.get('penultima_semana_cy') and kpis_semanas['penultima_semana_cy'] != 0:
        wow_pct = ((kpis_semanas['ultima_semana_cy'] / kpis_semanas['penultima_semana_cy'] - 1) * 100)

    kpis_values = [
        formatar_valor(kpis_semanas.get('ultima_semana_cy', 0)),
        formatar_valor(wow_pct, 'percentual'),
        formatar_valor(kpis_semanas.get('yoy_semanal', 0), 'percentual'),
        formatar_valor(kpis_meses.get('mtd_cy', 0)),
        formatar_valor(kpis_meses.get('mtd_yoy', 0), 'percentual'),
        formatar_valor(kpis_meses.get('qtd_cy', 0)),
        formatar_valor(kpis_meses.get('qtd_yoy', 0), 'percentual'),
        formatar_valor(kpis_meses.get('ytd_cy', 0)),
        formatar_valor(kpis_meses.get('ytd_yoy', 0), 'percentual')
    ]

    # Adicionar anotações de KPIs
    for i, (header, value) in enumerate(zip(kpis_headers, kpis_values)):
        x_position = (i + 0.5) / 9

        # Header
        fig_combinado.add_annotation(
            x=x_position,
            y=-0.38,
            xref='paper',
            yref='paper',
            text=f"<b>{header}</b>",
            showarrow=False,
            font=dict(size=19, color='Black', family='Arial'),
            align='center',
            xanchor='center'
        )

        # Valor
        color = 'black'
        if 'YOY' in header or 'WOW' in header:
            try:
                val_num = float(value.replace('%', '').replace('+', ''))
                color = 'darkgreen' if val_num > 0 else 'darkred' if val_num < 0 else 'black'
            except:
                pass

        fig_combinado.add_annotation(
            x=x_position,
            y=-0.44,
            xref='paper',
            yref='paper',
            text=value,
            showarrow=False,
            font=dict(size=18, color=color, family='Arial'),
            align='center',
            xanchor='center'
        )

    return fig_combinado


# Função principal de integração
def criar_grafico_wbr_modular(
    dados: Dict[str, Any],
    titulo: str = "Dashboard WBR",
    unidade: str = "valor",
    metrica: str = "metric_value",
    data_referencia: Optional[pd.Timestamp] = None
) -> go.Figure:
    """
    Função principal que cria o gráfico WBR completo usando as funções modulares.

    Args:
        dados: Dicionário com dados processados
        titulo: Título do gráfico
        unidade: Unidade de medida
        metrica: Nome da coluna de métrica
        data_referencia: Data para análise

    Returns:
        Figura Plotly com gráfico WBR completo
    """
    # Obter anos
    ano_atual = dados.get('ano_atual', data_referencia.year if data_referencia else 2024)
    ano_anterior = dados.get('ano_anterior', ano_atual - 1)

    # Criar gráfico semanal
    fig_semanal, kpis_semanas = criar_grafico_semanal_wbr(
        dados=dados,
        metrica=metrica,
        unidade=unidade,
        ano_atual=ano_atual,
        ano_anterior=ano_anterior
    )

    # Criar gráfico mensal
    fig_mensal, kpis_meses = criar_grafico_mensal_wbr(
        dados=dados,
        metrica=metrica,
        unidade=unidade,
        ano_atual=ano_atual,
        ano_anterior=ano_anterior,
        offset_x=7  # Começa após as 6 semanas + espaçador
    )

    # Combinar gráficos
    fig_combinado = combinar_graficos_wbr(
        fig_semanal=fig_semanal,
        fig_mensal=fig_mensal,
        titulo=titulo,
        data_referencia=data_referencia or pd.Timestamp.now(),
        kpis_semanas=kpis_semanas,
        kpis_meses=kpis_meses
    )

    return fig_combinado