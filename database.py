import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Construindo a raiz do projeto de forma dinâmica e absoluta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Para rodar localmente no começo (Mock) sem precisar subir um servidor SQL agora.
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'estoque_mock.db')}"

# Quando for usar o PostgreSQL definitivo, basta comentar a linha acima e descomentar esta:
# DATABASE_URL = "postgresql://usuario:senha@localhost/b2b_saas"

# connect_args é necessário para o SQLite. No PostgreSQL, pode remover esse parâmetro.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()