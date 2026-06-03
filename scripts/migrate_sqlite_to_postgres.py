#!/usr/bin/env python3
"""
SQLite → PostgreSQL Migration Script for TripOps
=================================================

Reads all data from a local SQLite database and inserts it into a PostgreSQL
database specified by DATABASE_URL.

Usage:
    DATABASE_URL=postgresql://user:pass@host:5432/tripops \
    python scripts/migrate_sqlite_to_postgres.py [--sqlite-path ./travel_memory.db]

Requirements:
    pip install sqlalchemy psycopg2-binary python-dotenv
"""

import argparse
import os
import sys
import sqlite3
import logging
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("migrate")

# --------------- Ordered table list (respects FK dependencies) ---------------
MIGRATION_ORDER = [
    "organizations",
    "users",
    "user_preferences",
    "trips",
    "travellers",
    "rooms",
    "room_allocations",
    "consents",
    "traveller_documents",
    "trip_document_requirements",
    "expenses",
    "communications",
    "communication_recipients",
    "registration_links",
    "registration_form_configs",
    "invitations",
    "trip_itineraries",
]


def get_sqlite_tables(sqlite_path: str) -> list[str]:
    """Return list of tables present in the SQLite database."""
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables


def read_sqlite_table(sqlite_path: str, table_name: str) -> tuple[list[str], list[tuple]]:
    """Read all rows from a SQLite table. Returns (column_names, rows)."""
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM "{table_name}"')
    rows = cur.fetchall()
    columns = rows[0].keys() if rows else []
    data = [tuple(row) for row in rows]
    conn.close()
    return list(columns), data


def table_exists_pg(pg_engine, table_name: str) -> bool:
    """Check if a table exists in PostgreSQL."""
    inspector = inspect(pg_engine)
    return table_name in inspector.get_table_names()


def migrate_table(sqlite_path: str, pg_engine, table_name: str) -> int:
    """Migrate a single table from SQLite to PostgreSQL. Returns row count."""
    columns, rows = read_sqlite_table(sqlite_path, table_name)
    if not rows:
        logger.info(f"  {table_name}: 0 rows (empty)")
        return 0

    if not table_exists_pg(pg_engine, table_name):
        logger.warning(f"  {table_name}: table does not exist in PostgreSQL — skipping")
        return 0

    # Build INSERT statement with named params
    col_list = ", ".join(f'"{c}"' for c in columns)
    param_list = ", ".join(f":{c}" for c in columns)
    insert_sql = text(f'INSERT INTO "{table_name}" ({col_list}) VALUES ({param_list})')

    Session = sessionmaker(bind=pg_engine)
    session = Session()
    inserted = 0
    skipped = 0

    try:
        for row in rows:
            row_dict = dict(zip(columns, row))
            try:
                session.execute(insert_sql, row_dict)
                inserted += 1
            except Exception as e:
                session.rollback()
                skipped += 1
                if skipped <= 3:
                    logger.warning(f"  {table_name}: skipped row — {e}")
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"  {table_name}: migration failed — {e}")
        return 0
    finally:
        session.close()

    status = f"{inserted} rows migrated"
    if skipped:
        status += f", {skipped} skipped"
    logger.info(f"  {table_name}: {status}")
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Migrate TripOps data from SQLite to PostgreSQL")
    parser.add_argument("--sqlite-path", default="./travel_memory.db", help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be migrated")
    args = parser.parse_args()

    # Validate SQLite path
    if not os.path.exists(args.sqlite_path):
        logger.error(f"SQLite database not found: {args.sqlite_path}")
        sys.exit(1)

    # Validate DATABASE_URL
    pg_url = os.getenv("DATABASE_URL")
    if not pg_url:
        logger.error("DATABASE_URL environment variable is not set")
        logger.error("Example: DATABASE_URL=postgresql://user:pass@host:5432/tripops")
        sys.exit(1)

    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    if pg_url.startswith("sqlite"):
        logger.error("DATABASE_URL points to SQLite — set it to a PostgreSQL URL")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("TripOps — SQLite → PostgreSQL Migration")
    logger.info("=" * 60)
    logger.info(f"Source:  {args.sqlite_path}")
    logger.info(f"Target:  {pg_url.split('@')[-1] if '@' in pg_url else pg_url}")
    logger.info("")

    # Discover SQLite tables
    sqlite_tables = set(get_sqlite_tables(args.sqlite_path))
    logger.info(f"SQLite tables found: {len(sqlite_tables)}")
    for t in sorted(sqlite_tables):
        cols, rows = read_sqlite_table(args.sqlite_path, t)
        logger.info(f"  {t}: {len(rows)} rows")
    logger.info("")

    if args.dry_run:
        logger.info("DRY RUN — no data will be written")
        return

    # Connect to PostgreSQL
    pg_engine = create_engine(pg_url, pool_pre_ping=True)

    try:
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Cannot connect to PostgreSQL: {e}")
        sys.exit(1)

    # Create tables in PostgreSQL (import models to register metadata)
    from database import Base
    import models.auth  # noqa: F401
    import models.group_trip  # noqa: F401
    import models.document  # noqa: F401
    import models.room  # noqa: F401
    import models.consent  # noqa: F401
    import models.expense  # noqa: F401
    import models.communication  # noqa: F401
    import models.registration  # noqa: F401
    import models.trip_itinerary  # noqa: F401
    import models.user_preference  # noqa: F401

    logger.info("Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=pg_engine)
    logger.info("✅ Tables created")
    logger.info("")

    # Migrate tables in dependency order
    logger.info("Starting data migration...")
    logger.info("-" * 40)
    total_rows = 0
    total_tables = 0

    for table_name in MIGRATION_ORDER:
        if table_name in sqlite_tables:
            count = migrate_table(args.sqlite_path, pg_engine, table_name)
            total_rows += count
            total_tables += 1

    # Migrate any remaining tables not in the ordered list
    remaining = sqlite_tables - set(MIGRATION_ORDER)
    for table_name in sorted(remaining):
        if table_name == "alembic_version":
            continue
        count = migrate_table(args.sqlite_path, pg_engine, table_name)
        total_rows += count
        total_tables += 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info(f"Tables migrated:  {total_tables}")
    logger.info(f"Total rows:       {total_rows}")
    logger.info(f"Completed at:     {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Stamp Alembic version
    try:
        with pg_engine.connect() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"
            ))
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
                         {"v": "0001_create_all_tables"})
            conn.commit()
        logger.info("✅ Alembic version stamped: 0001_create_all_tables")
    except Exception as e:
        logger.warning(f"Could not stamp Alembic version: {e}")

    logger.info("")
    logger.info("🎉 Migration complete! Your PostgreSQL database is ready.")


if __name__ == "__main__":
    main()
