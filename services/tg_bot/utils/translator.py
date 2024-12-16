from translatepy.translators.yandex import YandexTranslate

def translate_to_russian(text: str) -> str:
    translator = YandexTranslate()
    return translator.translate(text, 'ru')