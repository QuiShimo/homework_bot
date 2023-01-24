# Бот для уведомлений от Практикума
Высылает уведомления об изменении статуса домашнего задания
## Как запустить
1. Клонируем репозиторий
```
git clone https://github.com/QuiShimo/homework_bot.git
```
2. Устанавливаем необходимые зависимости из requirements.txt
```
pip install -r requirements.txt
```
3. Создаем в корне файл .env и создаем в нем переменные окружения. Пример содержимого файла:
```
PRACTICUM_TOKEN=ASDFGVXFDSFerwwerQEWQe5342DWe
TELEGRAM_TOKEN=123412312:AAAAAAAADSADweqwRQW$535DFF
TELEGRAM_CHAT_ID=1234567
```
5. Запускаем homeworks.py