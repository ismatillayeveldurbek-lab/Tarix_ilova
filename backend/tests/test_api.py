"""API testlari: Telegram initData imzosi, Mini App oqimi, imtihon, admin panel."""
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import httpx
import pytest

from app.api.app import create_app
from app.config import settings
from app.db import SessionLocal
from app.security import make_admin_token, validate_init_data
from tests.test_services import load_sample


def init_data(user_id: int, first_name: str = "Ali", auth_date: int | None = None) -> str:
    """Telegram qanday imzolasa, xuddi shunday imzolangan initData yasaydi."""
    fields = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "AAH",
        "user": json.dumps({"id": user_id, "first_name": first_name}),
    }
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def client(auth: str | None = None) -> httpx.AsyncClient:
    headers = {"Authorization": auth} if auth else {}
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()),
                             base_url="http://test", headers=headers)


@pytest.fixture
async def seeded():
    from app.models import ExamConfig
    from scripts.seed import DEFAULT_EXAM
    async with SessionLocal() as s:
        await load_sample(s)
        s.add(ExamConfig(**DEFAULT_EXAM))
        await s.commit()


def test_init_data_validation():
    good = init_data(1)
    assert validate_init_data(good)["id"] == 1
    assert validate_init_data(good.replace("Ali", "Vali")) is None  # o'zgartirilgan
    assert validate_init_data(init_data(1, auth_date=int(time.time()) - 3 * 86400)) is None  # eskirgan
    assert validate_init_data("garbage") is None


async def test_requires_auth():
    async with client() as c:
        assert (await c.get("/api/home")).status_code == 401
    async with client("tma bad=1&hash=x") as c:
        assert (await c.get("/api/home")).status_code == 401


async def test_lesson_flow(seeded):
    async with client("tma " + init_data(100)) as c:
        home = (await c.get("/api/home")).json()
        assert home["today"] == {"done": 0, "goal": 10}
        assert home["path"] and home["path"][0]["topics"]
        assert len(home["week"]["days"]) == 7

        await c.patch("/api/me", json={"alphabet": "cyrl", "reminder_time": "20:30"})
        lesson = (await c.post("/api/lessons", json={"mode": "daily"})).json()
        assert len(lesson["questions"]) == 10
        q = lesson["questions"][0]
        assert "correct_option" not in q  # javob oldindan yuborilmaydi
        assert any(ch in q["text"] for ch in "аоиуе")  # kirillda

        res = (await c.post("/api/answers", json={"question_id": q["id"], "option": "a", "source": "daily"})).json()
        assert res["today_done"] == 1 and res["streak"] == 1 and res["xp"] in (1, 10)

        assert (await c.post("/api/reports", json={"question_id": q["id"], "comment": "Xato"})).status_code == 200

        rating = (await c.get("/api/rating")).json()
        assert rating["rows"][0]["is_me"] and rating["me"]["rank"] == 1

        home = (await c.get("/api/home")).json()
        assert home["user"]["alphabet"] == "cyrl" and home["user"]["reminder_time"] == "20:30"
        assert home["week"]["days"][-1]["active"]


async def test_exam_flow(seeded):
    async with client("tma " + init_data(101)) as c:
        info = (await c.get("/api/exam")).json()
        assert info["config"]["minutes"] == 60 and info["open_exam_id"] is None

        exam = (await c.post("/api/exam/start")).json()
        assert 0 < len(exam["questions"]) <= 20
        # qayta boshlash — o'sha imtihon qaytadi (davom ettirish)
        assert (await c.post("/api/exam/start")).json()["id"] == exam["id"]

        first = exam["questions"][0]
        assert (await c.put(f"/api/exam/{exam['id']}/answer",
                            json={"question_id": first["id"], "option": "b"})).status_code == 200
        result = (await c.post(f"/api/exam/{exam['id']}/finish")).json()
        assert result["total"] == len(exam["questions"])
        assert result["grade"] and result["items"][0]["chosen"] == "b"
        assert 0 <= result["score"] <= result["max_score"]
        # yakunlangandan keyin javob qabul qilinmaydi
        assert (await c.put(f"/api/exam/{exam['id']}/answer",
                            json={"question_id": first["id"], "option": "a"})).status_code == 409

    # boshqa foydalanuvchi bu imtihonni ko'ra olmaydi
    async with client("tma " + init_data(102)) as c:
        assert (await c.post(f"/api/exam/{exam['id']}/finish")).status_code == 404


async def test_admin_permissions_and_crud(seeded):
    async with client("tma " + init_data(100)) as c:
        assert (await c.get("/api/admin/stats")).status_code == 403

    async with client("tma " + init_data(999)) as c:  # 999 — ADMIN_IDS da
        await c.get("/api/home")
    token = make_admin_token(999)
    async with client("Bearer " + token) as c:
        stats = (await c.get("/api/admin/stats")).json()
        assert stats["questions"] == 20

        periods = (await c.get("/api/admin/periods")).json()
        pid = periods[0]["id"]
        new = (await c.post("/api/admin/questions", json={
            "text": "Yangi savol?", "a": "1", "b": "2", "c": "3", "d": "4", "correct": "c",
            "explanation": "izoh", "difficulty": 2, "period_id": pid,
        })).json()
        assert new["period"] == periods[0]["name"]
        found = (await c.get("/api/admin/questions", params={"q": "Yangi savol"})).json()
        assert found["total"] == 1
        upd = (await c.put(f"/api/admin/questions/{new['id']}", json={**{
            "text": "Tahrirlangan?", "a": "1", "b": "2", "c": "3", "d": "4", "correct": "d"}})).json()
        assert upd["text"] == "Tahrirlangan?" and upd["correct"] == "d"
        assert (await c.delete(f"/api/admin/questions/{new['id']}")).json()["deleted"] is True

        # import
        csv_bytes = "savol,a,b,c,d,togri\nImport savol?,1,2,3,4,A\n".encode()
        rep = (await c.post("/api/admin/import/questions", files={"file": ("q.csv", csv_bytes)})).json()
        assert rep["added"] == 1
        bad = await c.post("/api/admin/import/questions", files={"file": ("q.txt", b"x")})
        assert bad.status_code == 400
        hist = "oy,kun,yil,sarlavha,matn\n1,1,2000,Test voqea,matn\n13,1,,Xato,\n".encode()
        rep = (await c.post("/api/admin/import/history", files={"file": ("h.csv", hist)})).json()
        assert rep["added"] == 1 and len(rep["errors"]) == 1

        xlsx = await c.get("/api/admin/template/questions.xlsx")
        assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"

        cfg = (await c.get("/api/admin/exam-config")).json()
        assert cfg["availability"] == [11, 9, 1]  # 10 namuna + 1 import qilingan oson savol
        saved = (await c.put("/api/admin/exam-config", json={
            "name": "Yangi format", "duration_minutes": 90, "max_score": 100,
            "rules": [{"count": 5, "points": 2}], "grades": [{"min_percent": 50, "grade": "B"}],
        })).json()
        assert saved["duration_minutes"] == 90 and saved["availability"] == [21]

        # davr: savoli bor davrni o'chirib bo'lmaydi
        assert (await c.delete(f"/api/admin/periods/{pid}")).status_code == 400

    async with client("Bearer 999.1.bad") as c:
        assert (await c.get("/api/admin/stats")).status_code == 401
