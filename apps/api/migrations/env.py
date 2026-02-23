import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from sqlmodel import SQLModel

# -------------------------------------------------------------------------
# 1. IMPORTAR TUS MODELOS AQUÍ PARA QUE ALEMBIC LOS DETECTE
# -------------------------------------------------------------------------
# Agregamos el directorio raíz al path para poder importar 'src'
sys.path.append(os.getcwd())

from src.models.match import Match
from src.models.user import User  # Importamos User también por si acaso

# -------------------------------------------------------------------------
# 2. CONFIGURACIÓN DE ALEMBIC
# -------------------------------------------------------------------------
config = context.config

# Interpretar el archivo de configuración para el log
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Asignamos los metadatos de SQLModel (donde están tus tablas definidas)
target_metadata = SQLModel.metadata

# -------------------------------------------------------------------------
# 3. OBTENER URL DE LA BASE DE DATOS DESDE EL ENTORNO
# -------------------------------------------------------------------------
def get_url():
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    server = os.getenv("POSTGRES_SERVER", "db")
    db = os.getenv("POSTGRES_DB", "goalos")
    return f"postgresql://{user}:{password}@{server}/{db}"

def run_migrations_offline() -> None:
    """Correr migraciones en modo 'offline' (sin conexión)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Correr migraciones en modo 'online' (conectado a la DB)."""
    # Sobrescribimos la URL del archivo .ini con la real de Docker
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()