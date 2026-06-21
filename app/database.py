"""Configuração do banco (SQLite) com SQLAlchemy.

Mantém o `engine`, a fábrica de sessões e a `Base` declarativa usados em todo o app.
O arquivo do banco fica na raiz do projeto (`study.db`) — uso local, single-user.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# study.db na raiz do projeto (um nível acima de app/)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "study.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False: o SQLite é acessado por threads diferentes do servidor.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa para todos os models ORM."""


def get_db():
    """Dependência do FastAPI: fornece uma sessão e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
