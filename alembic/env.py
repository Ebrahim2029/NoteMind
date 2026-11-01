
 # تحميل المتغيرات من ملف .env
import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app_config import app_settings

# Add this to import your models
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__), '..')))

# Import your Base and models
from core.repositories.models.base import Base
from core.repositories.models.user_models import UserModel
from core.repositories.models.notebook_models import NotebookModel
from core.repositories.models.note_models import NoteModel


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# استبدال رابط الاتصال في config برابط من متغيرات البيئة
db_user = app_settings.POSTGRES_USER
db_password = app_settings.POSTGRES_PASSWORD 
db_host = app_settings.POSTGRES_HOST 
db_name = app_settings.POSTGRES_DB
db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"

config.set_main_option("sqlalchemy.url", db_url)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,          # Add these for better migration detection
            compare_server_default=True,
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
