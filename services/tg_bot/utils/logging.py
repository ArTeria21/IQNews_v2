import uuid

def generate_correlation_id():
    """Генерирует UUID для корреляции сообщений"""
    return str(uuid.uuid4())