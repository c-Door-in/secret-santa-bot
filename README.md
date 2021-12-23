# secret-santa
 Бот для игры "Тайный Санта"

## Настройки

### Подключите зависимости
```
pip install -r requirements.txt
```
### Подключите переменные окружения
Создайте файл .env в директории `/tgadmin/tgadmin` рядом с `settings.py` и введите
```
TELEGRAM_API_TOKEN=<token>
```
где token - токен телеграм-бота.

### Подключите базу данных
Пейдите в директорию `/tgadmin` с `manage.py` и запустите команду
```
python manage.py migrate
```

## Запуск бота
Для запуска бота введите
```
python manage.py bot
```
## Запуск админки
Для запуска админки введите
```
python manage.py runserver
```
Перейдите по адресу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
Имя: `admin`
Пароль: `admin`

## Редактирование бота
Код бота располагается в `/tgadmin/santabot/management/commands/bot.py`
Модели базы данных располагаются в `/tgadmin/santabot/models.py`
