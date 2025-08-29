# Checklist de Melhorias do Dashboard WBR

## Status atual
- [x] Filtro de Shopping (input de texto)
- [x] Filtro de Ano (input numérico)
- [x] Toggle de métrica (Fluxo de Pessoas/Veículos) com reconsulta quando ambas as colunas existem
- [x] Janela de dados ampla (1º jan do ano passado → hoje)
- [x] Tratamento de pandas.NA/NaN no gráfico
- [x] Expander de debug com séries agregadas (semanas/meses) e KPIs

## Próximas melhorias (To do)
- [ ] Selectbox de Shopping
  - [ ] Trocar "Shopping (opcional)" por um selectbox com opções únicas vindas do DataFrame (`df['shopping']`)
  - [ ] Incluir opção "Todos" (sem filtro)
  - [ ] Cachear a lista com `@st.cache_data` e ordenar alfabeticamente
- [ ] Selectbox de Ano
  - [ ] Substituir o input numérico por um selectbox com anos distintos presentes em `df['date']`
  - [ ] Incluir opção "Todos" (sem filtro)
- [ ] Seleção de métrica sem reconsulta (quando possível)
  - [ ] Se a tabela tiver Pessoas e Veículos simultaneamente, carregar ambas e alternar client-side
  - [ ] Caso não seja possível, manter fallback de reconsulta por coluna
- [ ] Parametrizar período da consulta
  - [ ] Permitir selecionar data inicial/final na UI e refletir na SQL
  - [ ] Validar limites (ex.: máximo de 2 anos para manter performance)
- [ ] Melhorias de rótulos/anotações no gráfico
  - [ ] Evitar sobreposição (ajuste dinâmico de yshift e/ou smart layout)
  - [ ] Mostrar YOY com ícone/cores consistentes (positivo/negativo)
- [ ] KPIs mais ricos
  - [ ] Tooltip com fórmula (WOW/YOY)
  - [ ] Sinalização de parcial no mês/trim/ano
- [ ] Testes automatizados
  - [ ] Unit para `processar_dados_wbr` (semanas/mês/YOY)
  - [ ] Unit/smoke para `criar_grafico_wbr` (sem exceções e contagem de traces)
  - [ ] Integração para o BigQueryClient com schema sintético (mock)
- [ ] Observabilidade
  - [ ] Logs estruturados (período carregado, filtros aplicados, tempo de consulta/render)
  - [ ] Métricas simples de desempenho na UI (ex.: time to render)
- [ ] Documentação e config
  - [ ] Documentar variáveis .env (`WBR_DATE_COL`, `WBR_METRIC_COL`, `WBR_SHOPPING_COL`, `WBR_METRIC_COL_PESSOAS`, `WBR_METRIC_COL_VEICULOS`)
  - [ ] Atualizar `.env.example` com exemplos reais e comentários
