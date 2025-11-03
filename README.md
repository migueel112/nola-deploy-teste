📊 Nola God-Level: Aplicação de Análise de Vendas com IA

Este projeto é um framework completo de Business Intelligence (BI) construído em Python. Ele combina um backend robusto para carregamento eficiente de dados transacionais de um banco de dados SQL com um frontend interativo baseado em Streamlit, otimizado para análise de múltiplas páginas e enriquecido com capacidades de Inteligência Artificial para interpretação de dados.

🔗 Repositório

O código-fonte completo pode ser encontrado no GitHub:

https://github.com/migueel112/nola-god-level

🌟 Funcionalidades Principais

Arquitetura Otimizada (Backend): Utiliza o mecanismo de cache (st.cache_data) para otimizar o desempenho, minimizando a latência e evitando consultas repetidas ao banco de dados.

Navegação Multi-página: Organiza a aplicação em quatro visões de análise distintas para uma experiência de usuário mais estruturada.

Análise com Geração de Linguagem (IA): Possui um módulo avançado de IA que permite aos usuários obterem insights e explicações complexas sobre os dados em linguagem natural.

Integridade de Dados: Garante a consistência dos dados com a correção de aliases SQL para o sales_channel.

🏗️ Estrutura do Projeto

O projeto adota uma arquitetura limpa e modular, separando a lógica de dados, a orquestração da aplicação e a interface.

app.py: Ponto de entrada principal do Streamlit (Rodar este arquivo).

.gitignore

README.md

backend/

carregador_dados.py: Lógica de extração e caching dos dados.

db_config.py: Configuração da conexão com o DB.

logica_ia.py: Implementação da comunicação com o modelo de IA (Gemini).

frontend/

paginas/ (Diretório contendo as 4 páginas da aplicação)

1_Marca.py: Análise de desempenho por Marca.

2_Lojas.py: Análise de desempenho por Unidade/Loja.

3_Clientes.py: Análise de perfis e comportamento de Clientes.


💻 Tecnologias Envolvidas

Categoria

Tecnologia

Função

Frontend/UX

Streamlit

Framework para construção de dashboards web interativos.

Análise/Insights

Gemini API

Módulo de Inteligência Artificial para análise e geração de texto.

Backend/Dados

Pandas

Manipulação e transformação de DataFrames.

Backend/DB

SQLAlchemy

Gerenciamento da conexão com o banco de dados SQL.

🧠 Recurso Avançado: Análise com Geração de Linguagem (IA)

O destaque deste projeto é o módulo de Inteligência Artificial, implementado na página 4_IA.py.

Este componente utiliza a Gemini API para fornecer aos usuários uma ferramenta de BI de próxima geração:

Geração de Relatórios: O usuário pode solicitar resumos e interpretações dos dados de vendas e itens carregados.

Consulta em Linguagem Natural: O assistente de IA traduz perguntas complexas sobre os dados (ex: "Por que as vendas caíram na região X no último trimestre?") em insights acionáveis baseados nos DataFrames carregados.

Explicação de Tendências: O modelo de linguagem auxilia na explicação de padrões e anomalias identificados nas visualizações do dashboard.

🚀 Como Executar o Projeto

1: Clone o repositório:

git clone [https://github.com/migueel112/nola-god-level](https://github.com/migueel112/nola-god-level)
cd nola-god-level


2: Configuração do Ambiente Virtual:

python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows


3: Instale as dependências:
Certifique-se de instalar pandas, sqlalchemy e streamlit (e quaisquer outras libs de visualização que você use).

pip install -r requirements.txt


4: Configuração do Banco de Dados:
Ajuste as credenciais de conexão no módulo db_config.py para que a função get_db_engine() funcione corretamente.

5: Inicie a Aplicação Streamlit:

python -m streamlit run frontend\app.py


O aplicativo será aberto automaticamente no seu navegador.
