from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.orm import sessionmaker # <--- IMPORTANTE
import os

# Usa la variable de entorno o un default para Docker local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://goalos_admin:goalos_secure_pass@db:5432/goalos_v4")

engine = create_engine(DATABASE_URL, echo=True)

# --- DEFINICIÓN DE SESSIONLOCAL ---
# Esto es vital para que las Background Tasks (Workers) puedan conectarse
# independientemente de la petición del usuario.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session