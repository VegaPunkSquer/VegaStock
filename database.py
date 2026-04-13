import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carrega o cofre (.env)
load_dotenv()

# Puxa o link gigante do Neon
DATABASE_URL = os.getenv("DATABASE_URL")

# Motor do PostgreSQL (Não precisa mais do connect_args)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() 