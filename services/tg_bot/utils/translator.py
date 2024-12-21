from translatepy.translators.yandex import YandexTranslate


def translate_to_russian(text: str) -> str:
    translator = YandexTranslate()
    return str(translator.translate(text, "ru"))