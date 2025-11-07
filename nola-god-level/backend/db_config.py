import os
from dotenv import load_dotenv #bibilioteca p ler o arquivo env sem os dados ficarem nesse arquivo
from sqlalchemy import create_engine #biblioteca para interagir com o banco com python

load_dotenv() #carrega meu arquivo env

DB_USER = os.getenv("DB_USER", "postgres")  # valor padrao caso a variavel nao esteja setada
DB_PASSWORD = os.getenv("DB_PASSWORD", "5432")  # valor padrao caso a variavel nao esteja setada
DB_HOST = os.getenv("DB_HOST", "192.168.15.32")  # valor padrao caso a variavel nao esteja setada
DB_PORT = os.getenv("DB_PORT", "5432")  # valor padrao caso a variavel nao esteja setada
DB_NAME = os.getenv("DB_NAME", "postgres")  # valor padrao caso a variavel nao esteja setada

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine( #objeto central do SQLAlchemy, gerencia as conexoes
    DATABASE_URL, 
    pool_size=10, #minimo de conexoes
    max_overflow=20, #maximo de conexoes temporarias, para nao sobrecarregar
    connect_args={"options": "-c timezone=America/Sao_Paulo"} # Garantir o fuso horário
)

def get_db_engine():  ##FUNCAO PARA CHAMAR A MINHA ENGINE NOS OUTROS CODIGOS
    
    return engine 


####  NESTE ARQUIVO EU CRIO A CONFIGURACAO E A CONEXAO DO MEU BANCO DE DADOS COM O MEU CODIGO ####