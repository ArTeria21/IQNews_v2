import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def fetch_html_aiohttp(url: str, timeout: int = 10) -> str:
    """Загрузка HTML с помощью aiohttp."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as resp:
            resp.raise_for_status()
            html = await resp.text()
            return html

async def extract_main_text(html: str) -> str:
    """Извлекает текст основного контента со страницы."""
    soup = BeautifulSoup(html, 'html.parser')

    # Удаляем скрипты, стили и прочие неинформационные теги
    for tag in soup(["script", "style", "header", "footer", "nav", "form", "noscript"]):
        tag.extract()

    # Попытка найти основной блок контента. Здесь можно подстраивать логику.
    # Сейчас берём просто тексты из body. 
    # Можно попробовать что-то более специфичное, например по определенным классам или тегам.
    body = soup.find('body')
    if not body:
        return soup.get_text('\n', strip=True)
    
    text = body.get_text('\n', strip=True)
    return text

async def fetch_html_playwright(url: str, timeout: int = 15) -> str:
    """Загрузка HTML с помощью playwright для динамических сайтов."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=timeout * 1000)
        # Опционально: можно подождать определённый селектор, чтобы страница точно загрузилась
        # await page.wait_for_selector('article', timeout=5000)
        html = await page.content()
        await browser.close()
        return html

async def fetch_article_text(url: str) -> str:
    # Сначала пробуем загрузить и распарсить без браузера
    try:
        html = await fetch_html_aiohttp(url)
        text = await extract_main_text(html)
        if text and len(text.split()) > 50:  # Если текста достаточно много, считаем успехом
            return text
    except Exception as e:
        # Если что-то пошло не так, переходим к playwright
        pass

    # Если мало текста или ошибка — пробуем через playwright
    try:
        html = await fetch_html_playwright(url)
        text = await extract_main_text(html)
        return text
    except Exception as e:
        return None
