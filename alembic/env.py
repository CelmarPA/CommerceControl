from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# --- Caminho raiz ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# --- Import do Base e dos modelos ---
from app.database import Base
from app.models import *     # IMPORTANTE: importa todos os models

# --- Config padrão ---
config = context.config

# Interpreta o arquivo alembic.ini
fileConfig(config.config_file_name)

# Metadata usada para autogenerate
target_metadata = Base.metadata


def run_migrations_offline():
    """Rodar as migrações offline (gera SQL sem conectar ao DB)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,          # detecta mudança nos tipos
        compare_server_default=True # detecta defaults
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Rodar migrações conectado ao banco."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            compare_column=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
