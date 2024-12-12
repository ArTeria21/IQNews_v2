START_TEXT = 'Добро пожаловать в IQNews!\n\nМеня зовут XY, я менеджер новостей. Буду рада помочь!'

DONT_UNDERSTAND_TEXT = 'Прошу прощения, я не понимаю команду "{command}". Используйте команду /help для получения списка команд.'

HELP_TEXT = 'Список команд:\n\n/start - Начать диалог\n/help - Получить справку по командам\n/profile - Получить профиль\n/edit_profile - Изменить профиль\n/subscribe_feed - Подписаться на RSS-поток'

PROFILE_TEXT = 'Ваш профиль №{user_id}\n\nUsername: {username}\n{pro_status}\n\n\
Интересы: {preferences}\n\nКлючевые слова: {keywords}\n\n\
Вы можете изменить свои интересы и ключевые слова используя кнопки ниже или команду /profile_edit'

PROFILE_NOT_FOUND_TEXT = 'Профиль не найден'

PROFILE_LOADING_ERROR_TEXT = 'Ошибка при загрузке профиля'

EDIT_PROFILE_TEXT = 'Выберите, что вы хотите изменить:'

EDIT_PREFERENCES_TEXT = 'Пожалуйста, отправьте ответным сообщением текстсовое описание своих интересов, хобби и тем, на которые сделает акцент \
искусственный интеллект. Например: "Я люблю читать книги, изучать языки и путешествовать. Интересуюсь историей Китая и Японии."'

EDIT_KEYWORDS_TEXT = 'Пожалуйста, отправьте ответным сообщением текст с ключевыми словами, которые вы хотите видеть в новостях. Например: "Китай, Япония, история, языки, путешествия, книги"'

PREFERENCES_SAVED_TEXT = 'Ваши интересы успешно обновлены!'

KEYWORDS_SAVED_TEXT = 'Ваши ключевые слова успешно обновлены!'

SUBSCRIBE_FEED_TEXT = 'Пожалуйста, отправьте ответным сообщением URL RSS-потока, который вы хотите подписаться на. Например: "https://nplus1.ru/rss"'

INVALID_FEED_URL_TEXT = 'Некорректный URL RSS-потока'

INACTIVE_FEED_TEXT = 'RSS-поток не активен. Более 6 месяцев не выходили новые посты'

FEED_SUBSCRIBED_TEXT = 'Вы успешно подписались на RSS-поток'

def GET_SUBSCRIPTIONS_TEXT(urls: list[str]) -> str:
    numbered_urls = [f"{i+1}. {url}" for i, url in enumerate(urls)]
    return f"Вы подписаны на следующие RSS-потоки:\n{'\n'.join(numbered_urls)}"

NO_SUBSCRIPTIONS_TEXT = 'Вы ещё не подписаны на RSS-потоки'

UNSUBSCRIBE_FEED_TEXT = 'Пожалуйста, отправьте ответным сообщением URL RSS-потока, который вы хотите отписаться от. Например: "https://nplus1.ru/rss"'

UNSUBSCRIBE_FEED_SUCCESS_TEXT = 'Вы успешно отписались от RSS-потока'

UNSUBSCRIBE_FEED_ERROR_TEXT = 'Ошибка при отписке от RSS-потока. Возможно, вы не подписаны на него.'