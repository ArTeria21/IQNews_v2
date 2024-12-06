from dotenv import load_dotenv
import os

import pika

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER')
if not RABBITMQ_USER:
    raise ValueError("RABBITMQ_DEFAULT_USER not found in environment variables")

RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS') 
if not RABBITMQ_PASS:
    raise ValueError("RABBITMQ_DEFAULT_PASS not found in environment variables")

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
if not RABBITMQ_HOST:
    raise ValueError("RABBITMQ_HOST not found in environment variables")

RABBITMQ_PORT = os.getenv('RABBITMQ_PORT')
if not RABBITMQ_PORT:
    raise ValueError("RABBITMQ_PORT not found in environment variables")

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
CONNECTION = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT,
                                                            credentials=credentials))