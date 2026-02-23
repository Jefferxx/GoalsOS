from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# --- DETECCIÓN DE ENTORNO ---
# Si existe DATABASE_URL, usa PostgreSQL (Nube). Si no, SQLite (Local).
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix para URLs de Railway/Heroku antiguas
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("☁️ MODO NUBE: Conectando a PostgreSQL...")
    engine = create_engine(DATABASE_URL)
else:
    print("💻 MODO LOCAL: Conectando a SQLite...")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./goals.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()