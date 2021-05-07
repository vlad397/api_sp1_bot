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
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    if homework["homework_name"] is None or homework["status"] is None:
        verdict = 'Работа не найдена.'
    homework_name = homework["homework_name"]
    if homework["status"] == "rejected":
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework["status"] == "reviewing":
        verdict = 'Работа отправлена на ревью.'
    elif homework["status"] == "approved":
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    else:
        verdict = 'Статус неизвестен.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    try:
        homework_statuses = requests.get(
            "https://praktikum.yandex.ru/api/user_api/homework_statuses/",
            params={"from_date": current_timestamp},
            headers={"Authorization": f"OAuth {PRAKTIKUM_TOKEN}"},
        )
        return homework_statuses.json()

    except requests.exceptions.RequestException as e:
        logging.error(e)
        send_message(f'Возникла ошибка - {e}', bot_client)


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.debug('Момент запуска')
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
                )
                logging.info('Сообщение отправлено')
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception:
            logging.error('Бот не смог отправить сообщение')
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
