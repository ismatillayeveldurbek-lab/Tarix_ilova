"""Lotin -> kirill. Test holatlari JSON faylda: Mini App (TypeScript) ham xuddi shu ro'yxat bilan tekshiriladi."""
import json
from pathlib import Path

import pytest

from app.services.translit import to_cyrillic

CASES = json.loads((Path(__file__).parent / "translit_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("latn,cyrl", CASES)
def test_translit(latn, cyrl):
    assert to_cyrillic(latn) == cyrl
