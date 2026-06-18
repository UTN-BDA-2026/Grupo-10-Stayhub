"""Create database schema from SQLAlchemy ORM models.

This script is intentionally simple: it loads all model mappings and then
creates missing tables using SQLAlchemy metadata.

Usage:
    uv run python scripts/migrate_orm.py
"""

from app.database import Base, engine
import app.models  # noqa: F401  Ensures model classes are registered


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("ORM schema migration finished.")


if __name__ == "__main__":
    main()
