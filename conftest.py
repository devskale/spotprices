"""Root conftest.

Puts the project root on sys.path so test modules can import top-level
packages (config, db, api, ...) without per-file sys.path hacks, and
provides shared fixtures.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest


@pytest.fixture
def db_session():
    """In-memory SQLite session with the spot-price schema created.

    Yields a SQLAlchemy Session; schema is dropped afterwards. Use this
    for any DB-backed unit test instead of creating your own engine.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from db.models.spot_prices import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
