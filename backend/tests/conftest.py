import os
import tempfile

# Testlar haqiqiy bazaga tegmasin: vaqtinchalik SQLite fayl
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp.name}"
os.environ["ADMIN_IDS"] = "999"
os.environ["BOT_TOKEN"] = "42:TEST"

import pytest  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402,F401  (jadvallar ro'yxatga olinsin)


@pytest.fixture(autouse=True)
async def fresh_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def session():
    async with SessionLocal() as s:
        yield s


@pytest.fixture
async def seeded():
    from app.models import ExamConfig
    from scripts.seed import DEFAULT_EXAM
    from tests.test_services import load_sample
    async with SessionLocal() as s:
        await load_sample(s)
        s.add(ExamConfig(**DEFAULT_EXAM))
        await s.commit()
