import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Ensure the project root is on sys.path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------- Import all models so metadata is populated ---------------
from database import Base, DATABASE_URL  # noqa: E402

# Import every model file so tables register on Base.metadata
import models.auth  # noqa: E402,F401
import models.group_trip  # noqa: E402,F401
import models.document  # noqa: E402,F401
import models.room  # noqa: E402,F401
import models.consent  # noqa: E402,F401
import models.expense  # noqa: E402,F401
import models.communication  # noqa: E402,F401
import models.registration  # noqa: E402,F401
import models.trip_itinerary  # noqa: E402,F401
import models.user_preference  # noqa: E402,F401
import models.trip_document  # noqa: E402,F401
import models.traveller_directory  # noqa: E402,F401
import models.payment  # noqa: E402,F401

target_metadata = Base.metadata

# Set the sqlalchemy.url from our DATABASE_URL env var
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
