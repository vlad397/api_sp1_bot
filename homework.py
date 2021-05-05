import os
import time

import logging
import requests
import telegram
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def parse_homework_status(homework):
    homework_name = homework["homework_name"]
    if homework["status"] == "rejected":
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = '''Ревьюеру всё понравилось,
                     можно приступать к следующему уроку.'''
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    homework_statuses = requests.get(
        "https://praktikum.yandex.ru/api/user_api/homework_statuses/",
        params={"from_date": current_timestamp},
        headers={"Authorization": f"OAuth {PRAKTIKUM_TOKEN}"},
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Сообщение отправлено')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.debug('Момент запуска')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            logging.error('Бот не смог отправить сообщение')
            bot_client.send_message(
                chat_id=CHAT_ID,
                text='Бот не смог отправить сообщение'
            )
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        'my_logger.log',
        maxBytes=50000000,
        backupCount=5
    )
    logger.addHandler(handler)
    main()
