## DOCUMENTAÇÃO TÉCNICA — NOLA God Level

Esta documentação descreve a arquitetura, decisões técnicas e instruções de desenvolvimento do projeto *NOLA God Level* — um painel analítico construído com Streamlit e Python, com suporte a um assistente de IA.

Sumário
- Visão geral
- Arquitetura e divisão de responsabilidades
- Explicação das escolhas de design (por que usar tal estrutura)
- Fluxo de dados
- Configuração local e execução
- Segurança e git (o que ficou fora do versionamento e porquê)
- Notas de implementação / observações técnicas
- Testes, validação e próximos passos


## Visão geral

O projeto fornece um painel BI com páginas focadas em Marca, Lojas e Clientes, além de uma página de Assistente IA que responde perguntas com contexto de vendas. O front-end é uma aplicação Streamlit multi-página. O back-end contém carregadores de dados, lógica que prepara o contexto da IA e configurações de acesso ao banco.


## Arquitetura e divisão de responsabilidades

- `frontend/`: Streamlit app e as páginas. Cada página é um módulo independente: facilita iteração rápida na interface e separação de responsabilidades (UX vs lógica).
- `backend/`: funções responsáveis por conectar ao banco, carregar dados e preparar agregados; também hospeda a lógica de composição do contexto para a IA.
- `generate_data.py` (não versionado): utilitário local para popular/dummificar dados em ambientes de desenvolvimento.

Racional: essa separação (frontend vs backend) torna o código mais testável, facilita reutilização dos carregadores em scripts e permite trocar a UI sem tocar nas regras de negócio.


## Explicação das escolhas de design

- Streamlit multi-página: escolha feita pela rapidez de iteração e simplicidade de deploy para dashboards. Cada página está em `frontend/paginas/` para permitir desenvolvimento isolado.
- Backend com carregadores cacheados (SQLAlchemy): consultas ao banco podem ser relativamente pesadas; usar cache (memória/local) reduz latência na UI. Colocar a lógica de carregamento em `backend/carregador_dados.py` permite centralizar otimizações (joins, índices, filtros).
- Junção com `customers`: para exibir nomes e telefones diretamente no frontend, os carregadores fazem join com `customers` no banco — evita múltiplas consultas no frontend e mantém o UI simples.
- Uso de `.env` + python-dotenv: garante que chaves sensíveis (ex.: `GEMINI_API_KEY`) não fiquem hard-coded nem versionadas. Facilita troca de ambiente (dev/staging/prod).
- `.gitignore` para `venv/`, `.env`, `generate_data.py`: evita commits de arquivos grandes, secretos ou puramente locais.
- Correções de pandas (ex.: evitar SettingWithCopyWarning): foram aplicadas cópias / .loc quando necessário para prevenir comportamentos ambíguos do pandas e garantir que transformações não sejam feitas em views acidentais.


## Fluxo de dados

1. Streamlit (frontend) carrega a página solicitada.
2. Página chama funções em `backend/carregador_dados.py` para obter DataFrames pré-agrupados (com cache).
3. Dados são agregados e formatados no backend quando apropriado (por exemplo, adicionar `customer_name` e `customer_phone`).
4. A UI renderiza gráficos e tabelas (Plotly/Streamlit) com os dados retornados.
5. Para perguntas de IA: `backend/logica_IA.py` monta um contexto (top/bottom performers, canais), `frontend/paginas/4_IA.py` envia para o serviço de IA (Gemini) usando a chave em `.env`.


## Configuração local e execução

- Requisitos: Python 3.10+ (recomendado). Dependências em `requirements.txt`.
- Passos básicos (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# criar .env com GEMINI_API_KEY e (opcional) DATABASE_URL
python -m streamlit run frontend/app.py
```


## Segurança / git / o que não foi versionado

- `GEMINI_API_KEY` em `.env`: por segurança essas chaves não entram no git. A aplicação espera a variável em runtime.
- `venv/` e arquivos do ambiente: são ignorados para evitar commits gigantes e problemas multi-OS.
- `generate_data.py`: utilitário local para popular DB em desenvolvimento — não é versionado por ser apenas uma ferramenta local.

Nota: se você acidentalmente comitou `venv/` no passado, usar `git rm -r --cached venv` remove do índice sem apagar localmente, seguido de commit e push.


## Notas de implementação / observações técnicas

- `backend/carregador_dados.py`:
  - Centraliza queries SQL/SQLAlchemy. Faz joins com `customers` para entregar colunas como `customer_name` e `customer_phone` já prontas para o frontend.
  - É cacheado para reduzir repetição de consultas durante navegação pelo Streamlit.
  - Motivo: reduzir latência e chamadas redundantes ao banco; manter transformação de dados perto da camada que conhece o esquema.

- `backend/logica_IA.py`:
  - Gera blocos de contexto (top/bottom produtos, canais) que aumentam a utilidade das respostas do modelo.
  - Motivo: os LLMs respondem melhor quando fornecidos dados sumarizados; montar o contexto no backend evita transferir grandes payloads e facilita controle sobre privacidade.

- `frontend/paginas/3_Clientes.py` e outras páginas:
  - Tabelas de ranking incluem agora `customer_name` e `customer_phone` (vindo do carregador), e colunas de valores são formatadas como moeda para UX.
  - Pequenas cópias de DataFrames (`.copy()` e `.loc`) foram introduzidas para suprimir warnings e garantir comportamentos determinísticos.

- `frontend/paginas/4_IA.py`:
  - Faz leitura de `GEMINI_API_KEY` do `.env`. Se faltar, a página indica que a integração IA está desabilitada.
  - Motivo: reduzir risco de chamadas não intencionais e tornar comportamento claro para desenvolvedores.


## Edge cases & problemas já tratados

- Pandas SettingWithCopyWarning: resolvido ao usar `.copy()` / `.loc` nas transformações.
- Dados faltantes em `customers`: o carregador trata joins e pode preencher `N/A` quando falta o cliente — assim o frontend não quebra.
- Volume de dados: caching e agregações no backend mitigam problemas de tempo de resposta para dashboards com muitas linhas.

