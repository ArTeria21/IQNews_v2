TRANSLATIONS = {
    "Hello, world!": "Привет, мир!",
    "Guten Tag!": "Добрый день!",
    "Здравствуйте!": "Здравствуйте!",
}


def translate_to_russian(text: str) -> str:
    """Simple dictionary-based translator used for tests."""
    return TRANSLATIONS.get(text, text)
