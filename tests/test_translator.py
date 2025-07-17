import pytest

from services.tg_bot.utils.translator import translate_to_russian


test_cases_translate_to_russian = [
    ("Hello, world!", "привет, мир!"),
    ("Guten Tag!", "добрый день!"),
    ("Здравствуйте!", "здравствуйте!"),
]


@pytest.mark.parametrize("text,expected_result", test_cases_translate_to_russian)
def test_translate_to_russian(text, expected_result):
    result = translate_to_russian(text)
    assert result.lower() == expected_result
