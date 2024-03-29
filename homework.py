from http import HTTPStatus
import logging
import os
import time
import requests
import sys
from tokenize import TokenError
from dotenv import load_dotenv
from telegram import Bot


load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_YP')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def send_message(bot, message):
    """Отправка сообщения от бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info('Сообщение отправлено')
    except Exception:
        logging.error('Сбой при отправке сообщения')


def get_api_answer(current_timestamp):
    """Запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise requests.HTTPError(response)
        return response.json()
    except requests.exceptions.RequestException as error:
        logging.error(f'Ошибка в работе программы: {error}')
        raise Exception(f'Ошибка в работе программы: {error}')


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        logging.error(
            'Тип данных API не является словарем'
        )
        raise TypeError(
            'Тип данных API не является словарем'
        )
    elif 'homeworks' not in response:
        logging.error(
            'Ответ API не содержит ключ homeworks'
        )
        raise KeyError(
            'Ответ API не содержит ключ homeworks'
        )
    homeworks = response.get('homeworks')
    if isinstance(homeworks, list):
        homeworks == []
        logging.debug('Новых статусов нет')
    else:
        logging.error(
            'Ответ отличается от ожидаемого'
        )
        raise TypeError(
            'Ответ отличается от ожидаемого'
        )
    return homeworks


def parse_status(homework):
    """Запрос статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES.keys():
        logging.error(
            'Такого статуса не существует'
        )
        raise KeyError(
            'Такого статуса не существует'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия Токенов."""
    if all([TELEGRAM_TOKEN,
           TELEGRAM_CHAT_ID,
           PRACTICUM_TOKEN]):
        return True
    else:
        logging.critical(
            'Одна или более переменных отсутствует'
        )
        return False


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        raise TokenError(
            'Одна или более переменных отсутствует'
        )
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework_statuses = check_response(response)
            if homework_statuses:
                send_message(bot, parse_status(homework_statuses[0]))
            else:
                logging.debug('Статус не изменился')
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
        else:
            logging.critical('Сбой в работе бота')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
