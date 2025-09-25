# WBR Dashboard - Mapa do Bosque

Dashboard modular e interativo para análise de métricas WBR (Working Backwards Reporting) com integração completa ao Supabase/PostgreSQL. Sistema empresarial para análise de dados de shopping centers com visualizações avançadas de fluxo de pessoas, veículos, vendas e métricas do Instagram.

## 🎯 Visão Geral

Sistema desenvolvido em Python/Streamlit para análise de dados operacionais de shopping centers, fornecendo insights através de:
- **Análise WBR Completa**: Comparações YoY (Year-over-Year), WoW (Week-over-Week), MTD (Month-to-Date), QTD (Quarter-to-Date) e YTD (Year-to-Date)
- **Visualizações Interativas**: Gráficos Plotly com múltiplas séries temporais e comparações dinâmicas
- **Métricas do Instagram**: Integração com dados de redes sociais para análise de engajamento
- **Sistema de Autenticação**: Controle de acesso seguro com gestão de tokens
- **Arquitetura Modular**: Design pattern MVC com serviços desacoplados

## 📁 Estrutura do Projeto

```
web-mapa-do-bosque/
├── src/
│   ├── main.py                       # Aplicação principal Streamlit
│   ├── auth/
│   │   ├── __init__.py              # Sistema de autenticação principal
│   │   └── credentials.py           # Gestão de credenciais e tokens
│   ├── clients/
│   │   ├── database/
│   │   │   ├── factory.py           # Factory pattern para criação de DB clients
│   │   │   ├── supabase_postgres.py # Cliente especializado Supabase/PostgreSQL
│   │   │   └── postgresql.py        # Cliente PostgreSQL genérico
│   │   └── sql/
│   │       ├── instagram_queries.py # Queries otimizadas para Instagram
│   │       └── queries.sql          # Biblioteca de queries SQL
│   ├── config/
│   │   ├── database.py              # Configurações de banco de dados
│   │   └── settings.py              # Configurações globais da aplicação
│   ├── core/
│   │   ├── wbr.py                   # Motor principal de cálculos WBR
│   │   ├── wbr_metrics.py           # Classe WBRCalculator com métricas avançadas
│   │   ├── wbr_utility.py           # Utilitários e helpers WBR
│   │   ├── wbr_charts_modular.py    # Sistema modular de geração de gráficos
│   │   ├── processing.py            # Pipeline de processamento de dados
│   │   └── charts.py                # Biblioteca de gráficos Plotly
│   ├── services/
│   │   ├── data_service.py          # Serviço de acesso e cache de dados
│   │   ├── filter_service.py        # Serviço de filtragem e validação
│   │   ├── instagram_service.py     # Serviço especializado Instagram
│   │   └── metrics_service.py       # Serviço de cálculo de métricas
│   ├── ui/
│   │   ├── login.py                 # Interface de autenticação
│   │   ├── styles/                  # Estilos CSS customizados
│   │   │   └── user_menu.py        # Estilos do menu de usuário
│   │   ├── pages/
│   │   │   ├── __init__.py         # Registry de páginas disponíveis
│   │   │   ├── dashboard.py        # Dashboard principal com métricas WBR
│   │   │   ├── instagram.py        # Dashboard de métricas do Instagram
│   │   │   └── advanced_metrics.py # Página de métricas avançadas
│   │   └── components/
│   │       ├── sidebar.py          # Sidebar com filtros dinâmicos
│   │       ├── charts.py           # Componentes de visualização
│   │       ├── metrics.py          # Cards de KPIs e métricas
│   │       └── data_preview.py     # Preview e exploração de dados
│   └── utils/
│       ├── env.py                   # Gerenciamento de variáveis de ambiente
│       └── logging.py               # Sistema de logging centralizado
├── scripts/
│   ├── sync_td_to_supabase.sh      # Script de sincronização TD→Supabase
│   └── check_database.py            # Diagnóstico de conexão com DB
├── docs/
│   ├── authentication.md            # Documentação do sistema de autenticação
│   └── NGROK_DOCKER_GUIDE.md       # Guia de deploy com Docker/ngrok
├── config/
│   └── wbr_config.yaml             # Configurações WBR em YAML
├── .secrets/
│   └── .env                        # Variáveis de ambiente sensíveis
├── .streamlit/
│   └── config.toml                 # Configurações do Streamlit
├── pyproject.toml                  # Dependências do projeto (UV/Poetry)
├── uv.lock                         # Lock file do UV
├── credentials.json                # Credenciais de autenticação (gitignored)
├── Dockerfile                      # Imagem Docker otimizada
├── docker-compose.yml              # Orquestração padrão
├── docker-compose-ngrok.yml        # Orquestração com túnel ngrok
├── .env.example                    # Template de configuração
└── README.md                       # Esta documentação
```

## 🚀 Funcionalidades Principais

### Dashboard Principal
- **Fluxo de Pessoas**: Análise detalhada do tráfego de visitantes com comparações temporais
- **Fluxo de Veículos**: Monitoramento de entrada/saída de veículos com métricas de ocupação
- **Vendas**: Análise de performance de vendas com breakdown por período
- **Comparações WBR**: Visualizações side-by-side de métricas YoY, WoW, MTD, QTD, YTD
- **Filtros Dinâmicos**: Seleção por shopping (SCIB, SBGP, SBI), período e data de referência

### Métricas do Instagram
- **Engajamento Total**: Soma de likes, comentários, compartilhamentos e salvamentos
- **Impressões e Alcance**: Análise de visibilidade e audiência
- **Análise por Shopping**: Comparação de performance entre diferentes unidades
- **Tendências Temporais**: Identificação de padrões e sazonalidades
- **Posts Publicados**: Tracking de frequência de publicação

### Sistema de Autenticação
- Login seguro com validação de credenciais
- Gestão de sessão com tokens persistentes
- Menu de usuário com opção de logout
- Suporte para múltiplos usuários

## ⚙️ Configuração

### Pré-requisitos
- Python 3.10 ou superior
- Conta Supabase com banco PostgreSQL configurado (ou PostgreSQL local)
- Credenciais de acesso ao banco de dados
- (Opcional) Conta ngrok para exposição pública

### Opção 1: Usando uv (Recomendado - Mais rápido)

1. **Clone o Repositório**
   ```bash
   git clone <repository-url>
   cd web-mapa-do-bosque
   ```

2. **Instalar uv** (se ainda não tiver)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Instalar Dependências com uv**
   ```bash
   uv sync
   ```

4. **Configurar Variáveis de Ambiente**
   - Copie `.env.example` para `.secrets/.env`
   - Configure as seguintes variáveis principais:
     - `SUPABASE_DATABASE_URL`: URL de conexão do Supabase
     - `SUPABASE_SCHEMA_MAPA`: Schema principal (default: mapa_do_bosque)
     - `SUPABASE_METRIC_COL`: Nome da coluna de métrica (default: value)
     - Credenciais de autenticação do dashboard

5. **Executar a Aplicação**
   ```bash
   uv run streamlit run src/main.py
   ```

### Opção 2: Usando pip tradicional

1. **Clone o Repositório**
   ```bash
   git clone <repository-url>
   cd web-mapa-do-bosque
   ```

2. **Criar Ambiente Virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows use `venv\Scripts\activate`
   ```

3. **Instalar Dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variáveis de Ambiente**
   - Copie `.env.example` para `.secrets/.env`
   - Configure as variáveis conforme descrito na Opção 1

5. **Executar a Aplicação**
   ```bash
   streamlit run src/main.py
   ```


## Deploy com Docker + ngrok

O projeto inclui suporte completo para Docker com exposição pública via ngrok.

### Configuração Docker

1. **Preparar Variáveis de Ambiente**
   ```bash
   cp .env.example .secrets/.env
   ```
   Configure em `.secrets/.env`:
   - `SUPABASE_DATABASE_URL`: URL de conexão do Supabase
   - `NGROK_AUTHTOKEN`: Token do ngrok (para exposição pública)

2. **Build e Execução**
   ```bash
   docker-compose up --build
   ```

3. **Acessar a Aplicação**
   - Local: http://localhost:8501
   - Público (ngrok): http://localhost:4040 (interface do ngrok)
   - A URL pública será exibida na interface do ngrok

## Uso do Sistema

### Funcionalidades Principais

1. **Dashboard Principal**
   - Visualização de fluxo de pessoas
   - Análise de fluxo de veículos
   - Métricas de vendas
   - Gráficos WBR com comparações YoY, WoW, MTD, QTD, YTD

2. **Métricas do Instagram**
   - Engajamento total (likes, comentários, compartilhamentos)
   - Alcance e impressões
   - Análise por shopping (SCIB, SBGP, SBI)
   - Tendências temporais

3. **Filtros Disponíveis**
   - Por período (data inicial e final)
   - Por shopping específico
   - Por ano de comparação

### Sincronização de Dados

Para sincronizar dados de um banco PostgreSQL local para o Supabase:

```bash
sh scripts/sync_td_to_supabase.sh
```

**Configuração necessária em `.secrets/.env`:**
- Origem: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Destino: `SUPABASE_DATABASE_URL`

**Tabelas sincronizadas** (configuráveis no script):
- `mapa_do_bosque.fluxo_de_pessoas`
- `mapa_do_bosque.fluxo_de_veiculos`
- `mapa_do_bosque.vendas_gshop`

## Testes

Para executar os testes:
```bash
pytest tests/
```

## 🛠️ Stack Tecnológica

### Frontend & Visualização
- **Streamlit** (v1.28+): Framework principal para interface web
- **Plotly** (v5.14+): Gráficos interativos e visualizações avançadas
- **Extra Streamlit Components**: Componentes adicionais para UI

### Backend & Processamento
- **Python** (3.10+): Linguagem base
- **Pandas** (v2.0+): Manipulação e análise de dados
- **NumPy** (v1.24+): Computação numérica
- **SQLAlchemy** (v2.0+): ORM e abstração de banco de dados

### Banco de Dados
- **Supabase**: Backend as a Service com PostgreSQL
- **PostgreSQL**: Banco de dados relacional principal
- **psycopg2-binary**: Driver PostgreSQL para Python

### Infraestrutura & Deploy
- **Docker**: Containerização da aplicação
- **Docker Compose**: Orquestração de serviços
- **ngrok**: Túnel para exposição pública (opcional)
- **UV**: Gerenciador de dependências Python (mais rápido que pip)

## 🏗️ Arquitetura do Sistema

### Design Patterns
- **MVC (Model-View-Controller)**: Separação clara entre lógica, dados e apresentação
- **Factory Pattern**: Criação de clientes de banco de dados
- **Service Layer**: Camada de serviços para lógica de negócio
- **Component-Based UI**: Interface construída com componentes reutilizáveis

### Fluxo de Dados
1. **Entrada**: Usuário define filtros via sidebar
2. **Processamento**: Services aplicam filtros e processam dados
3. **Cálculo WBR**: Core calcula métricas e comparações
4. **Visualização**: Components renderizam gráficos e KPIs
5. **Cache**: Streamlit cache otimiza performance

### Segurança
- Credenciais armazenadas em arquivos `.env` (não versionados)
- Autenticação obrigatória para acesso ao sistema
- Conexões SSL/TLS com banco de dados
- Sanitização de inputs e queries parametrizadas

## 📊 Métricas WBR Suportadas

### Comparações Temporais
- **YoY (Year-over-Year)**: Comparação com mesmo período do ano anterior
- **WoW (Week-over-Week)**: Comparação com semana anterior
- **MTD (Month-to-Date)**: Acumulado do mês até a data de referência
- **QTD (Quarter-to-Date)**: Acumulado do trimestre
- **YTD (Year-to-Date)**: Acumulado do ano

### Métricas Derivadas
- **Taxa de Conversão**: Vendas / Fluxo de Pessoas
- **Ticket Médio**: Vendas Totais / Número de Transações
- **Taxa de Engajamento**: Engajamento Total / Impressões
- **Performance Index**: Métrica customizável por shopping

## 🔧 Variáveis de Ambiente

### Configuração Principal (`.env`)
```bash
# Banco de Dados Principal
DATABASE_URL=postgresql://user:password@host:port/dbname
DB_TYPE=postgresql  # Opções: postgresql, supabase, bigquery

# Supabase (para dados do Instagram)
SUPABASE_DATABASE_URL=postgresql://...
SUPABASE_SCHEMA_MAPA=mapa_do_bosque

# Schemas do Instagram por Shopping
SUPABASE_SCHEMA_1=instagram-data-fetch-scib
SUPABASE_SCHEMA_2=instagram-data-fetch-sbgp
SUPABASE_SCHEMA_3=instagram-data-fetch-sbi

# Configuração de Colunas
WBR_DATE_COL=date
WBR_METRIC_COL=metric_value
WBR_SHOPPING_COL=shopping

# Deploy (Opcional)
NGROK_AUTHTOKEN=seu_token_aqui
```

### Credenciais de Autenticação (`credentials.json`)
```json
{
  "users": [
    {
      "username": "admin",
      "password": "hashed_password",
      "role": "admin"
    }
  ]
}
```

## 📈 Performance e Otimizações

### Cache Strategy
- **Data Cache**: TTL de 1 hora para dados do banco
- **Computation Cache**: Cache de cálculos WBR por sessão
- **Component Cache**: Reutilização de componentes UI

### Otimizações de Query
- Índices em colunas de data e shopping
- Queries agregadas no banco (não em memória)
- Lazy loading de dados do Instagram
- Batch processing para múltiplas métricas

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de Conexão com Banco**
   - Verificar credenciais em `.env`
   - Testar conexão: `python scripts/check_database.py`
   - Verificar firewall/VPN

2. **Dados do Instagram não Aparecem**
   - Confirmar SUPABASE_DATABASE_URL
   - Verificar schemas configurados
   - Validar período de dados disponíveis

3. **Performance Lenta**
   - Limpar cache: Settings → Clear Cache
   - Reduzir período de análise
   - Verificar índices no banco

4. **Erro de Autenticação**
   - Regenerar `credentials.json`
   - Limpar cookies do navegador
   - Verificar permissões de arquivo

## 🚦 Roadmap

### Versão 2.1 (Em Desenvolvimento)
- [ ] Integração com Google Analytics
- [ ] Dashboard de métricas avançadas
- [ ] Export de relatórios em PDF
- [ ] API REST para integração externa

### Versão 3.0 (Planejado)
- [ ] Machine Learning para previsões
- [ ] Real-time data streaming
- [ ] Mobile app companion
- [ ] Multi-tenant support

## 👥 Contribuições

Contribuições são bem-vindas! Por favor:
1. Fork o projeto
2. Crie uma feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

Para suporte e questões:
- Abra uma issue no GitHub
- Consulte a documentação em `/docs`
- Entre em contato com a equipe de desenvolvimento