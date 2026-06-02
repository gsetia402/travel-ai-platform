from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./travel_memory.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations():
    """Add columns that may be missing from older schemas."""
    import sqlite3
    conn = sqlite3.connect(DATABASE_URL.replace("sqlite:///", ""))
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
    conn.commit()

    # Migrate document statuses: PENDING and VERIFIED → UPLOADED
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traveller_documents'")
    if cur.fetchone():
        cur.execute("UPDATE traveller_documents SET verification_status = 'UPLOADED' WHERE verification_status IN ('PENDING', 'VERIFIED')")
        conn.commit()

    conn.close()
