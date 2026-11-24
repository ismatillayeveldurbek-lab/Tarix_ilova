import pytest

from app.services.translit import to_cyrillic


@pytest.mark.parametrize("latn,cyrl", [
    ("Amir Temur", "Амир Темур"),
    ("O'zbekiston", "Ўзбекистон"),
    ("G'alaba", "Ғалаба"),
    ("Shahrisabz", "Шаҳрисабз"),
    ("choy", "чой"),
    ("yo'l", "йўл"),
    ("Yangi davr", "Янги давр"),
    ("yulduz", "юлдуз"),
    ("ma'no", "маъно"),
    ("Ekin", "Экин"),
    ("poeziya", "поэзия"),
    ("Mirzo Ulug'bek", "Мирзо Улуғбек"),
    ("SHAHAR", "ШАҲАР"),
    ("Tong", "Тонг"),
])
def test_words(latn, cyrl):
    assert to_cyrillic(latn) == cyrl


def test_html_and_placeholders_untouched():
    assert to_cyrillic("<b>Savol {n}/{total}</b>") == "<b>Савол {n}/{total}</b>"
    assert to_cyrillic("a &amp; b") == "а &amp; б"


def test_numbers_and_punctuation():
    assert to_cyrillic("1336-yil, 9-aprel!") == "1336-йил, 9-апрел!"
