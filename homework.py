import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
import telegram
from dotenv import load_dotenv
from telegram.error import TelegramError

from exceptions import ResponseError


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    filename='bot_logs.log',
    filemode='w',
    encoding='utf-8',
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
SEND_ERROR = False
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def init_logger() -> logging.Logger:
    """Инициализирует и настраивает логгер.

    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    )
    logger.addHandler(handler)
    return logger


logger = init_logger()


def check_tokens() -> None:
    """Проверяет доступность переменных окружения необходимых для работы.

    Если хотя бы одна из переменных окружения отсутствует - завершает работу
    программы.
    """
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logger.critical('Ошибка при проверке переменных окружения.')
        sys.exit()
    logger.debug('Переменные окружения проверенны успешно.')


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.

    Чат определяется с помощью переменной окружения TELEGRAM_CHAT_ID.

    Args:
        bot (telegram.Bot): экземпляр телеграм бота
        message (str): текст сообщения
    """
    logger.debug('Начата отправка сообщения в чат Telegram')
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except TelegramError:
        logger.error("Ошибка при отправке сообщения в Telegram чат.")
    logger.debug('Сообщение успешно отправлено в Telegram чат.')


def get_api_answer(timestamp: int) -> dict:
    """Отправляет запрос к единственному эндпоинту API-сервиса.

    Args:
        timestamp (int): временная метка в Unix time формате.

    Returns:
        dict: ответ от API-сервиса.
    """
    try:
        playoad = {'from_date': timestamp}
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=playoad)
        if response.status_code != HTTPStatus.OK:
            raise Exception('Получен некорректный ответ от сервера')
        logger.debug('Ответ от API получен')
        return response.json()
    except Exception as error:
        raise ResponseError(
            f'Произошла ошибка при обращении к API Практикума: {error}'
        )


def check_response(response: dict) -> dict:
    """проверяет ответ API на соответствие документации.

    Args:
        response (_type_): ответ от API-сервиса.

    Returns:
        dict: информация о домашней работе
    """
    if not isinstance(response, dict):
        raise TypeError('Переменная response не соответсует типу dict')
    if 'homeworks' not in response:
        raise KeyError('В response отсутствует ключ homeworks')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Переменная homeworks не соответствует типу list')
    if len(homeworks) == 0:
        raise ValueError('Список с домашками пуст')

    logger.debug('Ответ от API Практикума корректен.')
    return homeworks[0]


def parse_status(homework: dict) -> str:
    """Извлекает информацию о конкретной домашней работе.

    Args:
        homework (dict): информация о конкретной домашней работе.

    Returns:
        str: строка, содержащая один из вердиктов из словаря HOMEWORK_VERDICTS.
    """
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    homework_name = homework.get('homework_name')
    if homework_name and verdict:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    raise TypeError('Ошибка при извлечении информации о домашке')


def main() -> None:
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    last_message = ''

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            homeworks = check_response(api_answer)
            timestamp = api_answer.get('current_date')
            message = parse_status(homeworks)
            last_message = message
            send_message(bot, message)
        except Exception as error:
            message = f'Внимание! {error}'
            if last_message != message:
                last_message = message
                send_message(bot, message)
            logger.error(message)
        finally:
            logger.debug('Ожидание таймаута')
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
