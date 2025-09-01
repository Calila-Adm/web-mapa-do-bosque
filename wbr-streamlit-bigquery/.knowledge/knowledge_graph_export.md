# Knowledge Graph Export - WBR Project
*Exported: 2025-01-01*

## Entities

### WBR Data Pipeline (System)
- [2025-01] Pipeline: BigQuery -> Processing -> KPIs -> Visualização
- [2025-01] Tech Stack: Streamlit + Plotly + pandas
- [CURRENT] Autenticação via service account JSON
- [2025-01-01] Simplificado para single-page app
- [CONFIG] Removida configuração deprecated general.email

### Architecture Decisions (Documentation)
- [ADR-001] Usar BigQuery como fonte única de dados
- [ADR-002] Cache via @st.cache_data para queries repetidas
- [ADR-003] SQL templates com variáveis para flexibilidade
- [ADR-004] Single-page app para simplificar UX - sem navegação entre abas
- [ADR-005] Usar convenção de ponto (.) para ocultar arquivos do Streamlit

### Metric Types (BusinessConcept)
- [ACTIVE] Fluxo de Pessoas - coluna configurável
- [ACTIVE] Fluxo de Veículos - coluna configurável
- [RULE] Toggle exclusivo entre métricas

### Streamlit Configuration (Configuration)
- [2025-01-01] Arquivo config.toml em .streamlit/
- [DEPRECATED-2025-01] general.email removido - opção não mais suportada
- [CURRENT] Configurações mantidas: server (port 8501, CORS, XSRF) e theme
- [CONFIG] Server em modo headless=true para deploy

### UI Architecture (Component)
- [2025-01-01] Convertido de multipage para single-page app
- [REFACTOR-2025-01] 01_Overview.py renomeado para .01_wbr.py (oculto com ponto)
- [CURRENT] Apenas streamlit_app.py ativo como página principal
- [DECISION] Single-page simplifica UX e remove navegação desnecessária

### Page Migration 2025-01 (Refactoring)
- Data: 2025-01-01
- De: Multipage com pages/01_Overview.py
- Para: Single-page ocultando arquivo com .01_wbr.py
- Motivo: Simplificar interface mantendo apenas funcionalidade principal
- Método: Adicionar ponto no início do nome do arquivo para Streamlit ignorar

## Relations

- WBR Data Pipeline --processes--> Metric Types
- Architecture Decisions --governs--> WBR Data Pipeline
- Metric Types --defined_by--> Architecture Decisions
- Page Migration 2025-01 --transforms--> UI Architecture
- Streamlit Configuration --configures--> WBR Data Pipeline
- UI Architecture --defines_interface_for--> WBR Data Pipeline
- Page Migration 2025-01 --implements--> Architecture Decisions