import os
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# --------------- Database URL (environment-driven) ---------------
# Priority: DATABASE_URL env var → SQLite fallback for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel_memory.db")

# Render.com sometimes provides postgres:// (old scheme) instead of postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# --------------- Engine Configuration ---------------
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_type() -> str:
    """Return 'postgresql' or 'sqlite'."""
    return "sqlite" if _is_sqlite else "postgresql"


def validate_connection() -> bool:
    """Test the database connection and log the result."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_type = get_db_type()
        logger.info(f"✅ Connected to {db_type.upper()} — {_masked_url()}")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def create_tables():
    """Create tables via create_all() for SQLite only.

    For PostgreSQL, tables are managed exclusively by Alembic:
        alembic upgrade head
    """
    if _is_sqlite:
        Base.metadata.create_all(bind=engine)
        _run_sqlite_migrations()
        logger.info("SQLite tables created via create_all()")
    else:
        validate_schema()


def validate_schema():
    """Fail fast if PostgreSQL is missing required tables.

    Raises RuntimeError with clear instructions so operators know
    exactly how to fix the database before the app serves traffic.
    """
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(engine)
    existing = set(inspector.get_table_names())
    expected = set(Base.metadata.tables.keys())
    missing = expected - existing

    if missing:
        logger.error("=" * 60)
        logger.error("PostgreSQL schema not initialized.")
        logger.error(f"Missing {len(missing)} required tables:")
        for table in sorted(missing):
            logger.error(f"  - {table}")
        logger.error("")
        logger.error("Run:")
        logger.error("  alembic upgrade head")
        logger.error("=" * 60)
        raise RuntimeError(
            f"PostgreSQL schema not initialized — {len(missing)} tables missing. "
            f"Run 'alembic upgrade head' to create them."
        )

    logger.info(f"PostgreSQL schema verified — {len(existing)} tables present")

    # Auto-add missing columns (safe for production — ADD COLUMN IF NOT EXISTS)
    _pg_ensure_columns()


def _pg_ensure_columns():
    """Add missing columns and tables to PostgreSQL at startup."""
    from sqlalchemy import text
    column_migrations = [
        "ALTER TABLE trips ADD COLUMN IF NOT EXISTS financial_model VARCHAR NOT NULL DEFAULT 'SPONSORED'",
        "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS receipt_path VARCHAR",
    ]
    table_migrations = [
        """CREATE TABLE IF NOT EXISTS payments (
            payment_id VARCHAR PRIMARY KEY,
            trip_id VARCHAR NOT NULL REFERENCES trips(trip_id) ON DELETE CASCADE,
            traveller_id VARCHAR REFERENCES travellers(traveller_id) ON DELETE CASCADE,
            payment_type VARCHAR NOT NULL,
            amount FLOAT NOT NULL,
            payment_date DATE,
            notes VARCHAR,
            proof_path VARCHAR,
            status VARCHAR NOT NULL DEFAULT 'APPROVED',
            rejected_reason VARCHAR,
            sponsor_name VARCHAR,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS trip_payment_config (
            trip_id VARCHAR PRIMARY KEY REFERENCES trips(trip_id) ON DELETE CASCADE,
            expected_amount_per_traveller FLOAT DEFAULT 0,
            registration_fee_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            registration_fee_amount FLOAT DEFAULT 0,
            sponsor_name VARCHAR,
            sponsor_commitment FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )""",
    ]
    with engine.begin() as conn:
        for stmt in table_migrations + column_migrations:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                logger.warning(f"Migration skipped: {e}")
    logger.info("PostgreSQL schema check complete")


def _masked_url() -> str:
    """Return the DATABASE_URL with password masked."""
    url = DATABASE_URL
    if "@" in url:
        # mask password between : and @
        before_at = url.split("@")[0]
        after_at = url.split("@", 1)[1]
        if ":" in before_at:
            scheme_user = before_at.rsplit(":", 1)[0]
            return f"{scheme_user}:****@{after_at}"
    return url


def _run_sqlite_migrations():
    """Add columns that may be missing from older SQLite schemas."""
    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Get existing columns for trips table
    cur.execute("PRAGMA table_info(trips)")
    columns = {row[1] for row in cur.fetchall()}
    if "status" not in columns:
        cur.execute("ALTER TABLE trips ADD COLUMN status TEXT NOT NULL DEFAULT 'DRAFT'")
    if "origin_city" not in columns:
        cur.execute("ALTER TABLE trips ADD COLUMN origin_city TEXT")
    if "origin_state" not in columns:
        cur.execute("ALTER TABLE trips ADD COLUMN origin_state TEXT")
    if "financial_model" not in columns:
        cur.execute("ALTER TABLE trips ADD COLUMN financial_model TEXT NOT NULL DEFAULT 'SPONSORED'")
    conn.commit()

    # Get existing columns for expenses table
    cur.execute("PRAGMA table_info(expenses)")
    exp_columns = {row[1] for row in cur.fetchall()}
    if "receipt_path" not in exp_columns:
        cur.execute("ALTER TABLE expenses ADD COLUMN receipt_path TEXT")
    conn.commit()

    # Migrate document statuses: PENDING and VERIFIED → UPLOADED
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traveller_documents'")
    if cur.fetchone():
        cur.execute("UPDATE traveller_documents SET verification_status = 'UPLOADED' WHERE verification_status IN ('PENDING', 'VERIFIED')")
        conn.commit()

    conn.close()
