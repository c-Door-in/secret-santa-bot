#!/usr/bin/env python
# pylint: disable=C0116,W0613
import logging
from datetime import datetime
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from pytz import timezone
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    message
)
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from santabot.models import Event, Participant, User, Pairs
from .bot_utils import datetime_from_str, choose_random_pairs

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

(
    MAIN_MENU,
    JOIN_GAME,
    MY_GAMES,
    CREATED_GAMES,
    JOINED_GAMES,
) = range(5)
(
    ENTER_GAME_NAME,
    COST_LIMITS,
    CHOOSE_COST,
    ENTER_COSTS,
    DATE_REG_ENDS,
    DATE_SEND,
    CONFIRM_DATA,
    SAVE_DATA,
) = range(5, 13)
(
    USERNAME,
    PHONE_NUMBER,
    INTERESTS,
    SANTA_LETTER,
    BYE
) = range(13, 18)

GAME_DETAILS, DRAW = range(18, 20)


def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""

    # context.user_data.clear() #!!!
    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    user_data['user_profile'], _ = User.objects.get_or_create(
        external_id=update.message.from_user.id,
        defaults={
            'name': update.message.from_user.name,
        },
    )

    update.message.reply_text(
        'Организуй тайный обмен подарками, запусти праздничное настроение!',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Создать игру', 'Вступить в игру', 'Мои игры'],
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    # на случай ошибок ввода
    context.user_data['error_message'] = 'Я вас не понимаю, выберите один из вариантов.'
    context.user_data['next_state'] = MAIN_MENU

    return MAIN_MENU


def foo(update: Update, context: CallbackContext) -> int:
    """Dumb foo func."""
    # TODO: временная заглушка
    update.message.reply_text(
        'Временно недоступно',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Создать игру', 'Вступить в игру', 'Мои игры'],
                ['Выход']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return MAIN_MENU


def my_games(update: Update, context: CallbackContext) -> int:
    """List menu of my games categories."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    update.message.reply_text(
        'Выберите пункт.',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Игры, которые я создал', 'Игры, где я участник'],
                ['Меню']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return MY_GAMES


def list_games(update: Update, context: CallbackContext) -> int:
    """List my games created or joined."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    tg_id = user_data['user_profile'].external_id
    keyboard = [[]]
    if update.message.text == 'Игры, которые я создал':
        msg = 'Здесь список созданных игр.\n\n'
        events = Event.objects.filter(creator__external_id=tg_id)
    if update.message.text == 'Игры, где я участник':
        msg = 'Здесь список игр в которых участвую(-ал).\n\n'
        events = Event.objects.filter(participant__user__external_id=tg_id)
    for event in events:
        keyboard.append(
            [InlineKeyboardButton(event.name, callback_data=event.name)],
        )
    update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return MY_GAMES


def game_details(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    event = Event.objects.get(name=query.data)
    query.answer()
    keyboard = [[]]
    participants = Participant.objects.filter(event=event)
    if not participants:
        query.edit_message_text('Нет игроков.')
        # keyboard = [[InlineKeyboardButton('Меню', callback_data='start')]]
        return GAME_DETAILS
    elif not Pairs.objects.all():
        participant_list = '\n'.join([f'{user}' for user in participants])
        keyboard = [
            [InlineKeyboardButton('Провести жеребьевку вручную', callback_data=event.name)],
            # [InlineKeyboardButton('Меню', callback_data='start')],
        ]
        text = (
            f'Игра {event.name}\n'
            f'Список участников:\n'
            f'{participant_list}\n'
            f'Жеребьевка будет проведена {event.last_register_date}\n'
            f'Дата отправки подарка - {event.sending_date}\n'
        )
    else:
        participant_list = '\n'.join([f'{user}' for user in participants])
        keyboard = [
            [InlineKeyboardButton('Показать пары', callback_data=event.name)],
            # [InlineKeyboardButton('Меню', callback_data='start')],
        ]
        text = (
            f'Игра {event.name}\n'
            f'Список участников:\n'
            f'{participant_list}\n'
            f'Жеребьевка была проведена\n'
            f'Дата отправки подарка - {event.sending_date}\n'
        )
    query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return GAME_DETAILS
    

def draw(event):
    participants = list(Participant.objects.filter(event=event).values_list('user__name', flat=True))
    pairs = choose_random_pairs(participants)
    for pair in pairs:
        for donor, receiver in pair.items():
            Pairs.objects.create(
                event=event,
                donor=Participant.objects.get(user__name=donor, event=event),
                receiver=Participant.objects.get(user__name=receiver, event=event),
            )
    return

def draw_result(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    event = Event.objects.get(name=query.data)
    query.answer()
    pairs_list = ''
    if not Pairs.objects.all():
        draw(event)
    pairs = Pairs.objects.filter(event=event)
    for pair in pairs:
        donor = pair.donor.name
        receiver = pair.receiver.name
        pairs_list += f'{donor} -> {receiver}\n'
    keyboard = [
        [InlineKeyboardButton('Назад', callback_data='back')],
        [InlineKeyboardButton('Меню', callback_data='start')],
    ]
    text = (
        f'Игра {event.name}\n'
        f'Результаты жеребьевки:\n'
        f'*Даритель* -> *Принимающий*'
        f'{pairs_list}'
    )
    query.edit_message_text(
        text=text,
        # reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return GAME_DETAILS



def enter_game_name(update: Update, context: CallbackContext) -> int:
    """Enter game name."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    if 'pass_cost_limits' in user_data:
        del user_data['pass_cost_limits']

    update.message.reply_text(
        'Название:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Меню']],
            one_time_keyboard=True,
            resize_keyboard=True,
        )
    )
    return COST_LIMITS


def cost_limits(update: Update, context: CallbackContext) -> int:
    """Save game name and ask costs limits."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    if 'cost_range' in user_data:
        del user_data['cost_range']

    if 'pass_cost_limits' not in user_data:
        text = update.message.text
        user_data['game_name'] = text

        if Event.objects.filter(name=text):
            update.message.reply_text('Такое имя уже используется.')
            return enter_game_name(update, context)

    update.message.reply_text(
        'Ограничение стоимости подарка: да/нет?',
        reply_markup= ReplyKeyboardMarkup(
            keyboard=[
                ['Да', 'Нет'],
                ['Назад', 'Меню']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        )
    )
    # искусственный флаг,
    # нужен чтобы понять были ли на этом этапе,
    # в случае возврата по кнопке "Назад"
    user_data['pass_cost_limits'] = True

    return CHOOSE_COST


def set_cost(update: Update, context: CallbackContext) -> int:
    """Set cost choosing flag and ask costs limits."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    if 'last_register_date' in user_data:
        del user_data['last_register_date']

    update.message.reply_text(
        'Выберите ценовой диапазон:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['до 500 рублей', '500-1000 рублей', '1000-2000 рублей'],
                ['Назад', 'Меню']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        )
    )

    context.user_data['error_message'] = 'Я вас не понимаю, выберите один из вариантов.'
    context.user_data['next_state'] = DATE_REG_ENDS

    return DATE_REG_ENDS


def choose_date_reg(update: Update, context: CallbackContext) -> int:
    """Choose end of registration."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    if 'sending_date' in user_data:
        del user_data['sending_date']

    # обновлять только если прилетело
    # с предыдущего а не с последующего
    if 'last_register_date' not in user_data:
        text = update.message.text
        user_data['cost_range'] = text

    update.message.reply_text(
        'Период регистрации участников:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Назад', 'Меню']],
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder='дд.мм.гггг',
        )
    )
    return DATE_SEND


def incorrect_input(update: Update, context: CallbackContext) -> int:
    """Send error message and go to next state."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', user_data['user_profile'], update.message.text
    )
    logger.info('user data: %s', user_data)

    message = user_data['error_message']
    next_state = user_data['next_state']

    update.message.reply_text(message)
    return next_state


def choose_date_send(update: Update, context: CallbackContext) -> int:
    """Choose send date."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    # если следующего нет, значит прилетели с данными правильными (дата)
    # от предыдущего,
    # если же он есть - то прилетели без данных, и вообще не за этим.
    # т.е. если прилетели назад менять дату отправки,
    # а дату окончания регистрации не нужно трогать.
    if 'sending_date' not in user_data:
        text = update.message.text

        res = re.search('^(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.20\d{2}$', text)
        if res is None:
            msg = (
                'Пожалуйста, введите дату в формате "дд.мм.гггг: 15.12.2021"'
            )
            user_data['error_message'] = msg
            user_data['next_state'] = DATE_SEND
            return incorrect_input(update, context)

        end_reg_date = datetime_from_str(date_str=text, time_str='12:00:00')
        # TODO: вынести?
        loctz = timezone('Europe/Moscow')
        if end_reg_date < loctz.localize(datetime.now()):
            user_data['error_message'] = 'Пожалуйста, введите еще не прошедшую дату.'
            user_data['next_state'] = DATE_SEND
            return incorrect_input(update, context)

        user_data['last_register_date'] = end_reg_date

    # если попали сюда по кнопке "Назад",
    # то не все данные собраны и флаг надо убать
    if 'is_all_collected' in user_data:
        del user_data['is_all_collected']

    update.message.reply_text(
        'Дата отправки подарка:',
        reply_markup= ReplyKeyboardMarkup(
            keyboard=[['Назад', 'Меню',]],
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder='дд.мм.гггг',
        )
    )
    return CONFIRM_DATA


def confirm_data(update: Update, context: CallbackContext) -> int:
    """Requesting confirmation entered data by user."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    # сначала обработка даты отправки подарков,
    # если еще не было наполнения,
    # т.е. если прилетели не по кнопке "Назад".
    if 'is_all_collected' not in user_data:
        text = update.message.text
        res = re.search('^(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.20\d{2}$', text)
        if res is None:
            msg = (
                'Пожалуйста, введите дату в формате "дд.мм.гггг: 15.12.2021"'
            )
            user_data['error_message'] = msg
            user_data['next_state'] = CONFIRM_DATA
            return incorrect_input(update, context)

        sending_date_time_obj = datetime_from_str(
            date_str=text, time_str='12:00:00'
        )
        if sending_date_time_obj < user_data['last_register_date']:
            msg = (
                'Пожалуйста, введите дату не ранее'
                f' {context.user_data["last_register_date"]}'
            )
            user_data['error_message'] = msg
            user_data['next_state'] = CONFIRM_DATA
            return incorrect_input(update, context)

        user_data['sending_date'] = sending_date_time_obj
        user_data['is_all_collected'] = True  # flag for already collected all data 

    # вывод всех данных для подтверждения
    message = ('Вы ввели:\n\n'

        f'Название игры: {user_data["game_name"]}\n'
        f'Ваш id и ник: {user_data["user_profile"]}\n'
        f'Ограничение цены подарка: {user_data["cost_range"]}\n'
        f'Дата окончания регистрации: {user_data["last_register_date"]}\n'
        f'Дата отправки подарка: {user_data["sending_date"]}\n\n'

        'Создать игру с этими данными?\n'
    )
    update.message.reply_text(
        message,
        reply_markup= ReplyKeyboardMarkup(
            keyboard=[
                ['Подтвердить'],
                ['Назад', 'Меню']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        )
    )

    context.user_data['error_message'] = 'Я вас не понимаю, выберите один из вариантов.'
    context.user_data['next_state'] = SAVE_DATA

    return SAVE_DATA


def save_data(update: Update, context: CallbackContext) -> int:
    """Save collected data in DB and send message."""

    user_data = context.user_data

    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    user_data['event'] = Event.objects.create(
        name=user_data['game_name'],
        creator=user_data['user_profile'],
        cost_range=user_data['cost_range'],
        last_register_date=user_data['last_register_date'],
        sending_date=user_data['sending_date'],
    )

    logger.info('Game created in DB, GAME_ID: %s', user_data['event'].pk)

    update.message.reply_text(
        'Отлично, Тайный Санта уже готовится к раздаче подарков!',
    )
    update.message.reply_text(
        'А здесь должна быть реферальная ссылка.',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Выход', 'Меню']],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    )

    user_data.clear()

    return MAIN_MENU


def done(update: Update, context: CallbackContext) -> int:
    """End conversation."""

    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    update.message.reply_text(
        'До свидания!',
        reply_markup=ReplyKeyboardRemove(),
    )
    user_data.clear()

    return ConversationHandler.END


def start_game(update: Update, context: CallbackContext):
    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)
    # event = Event.objects.get(pk=game_id) После того, как узнаем ID ключа.
    # Подставить в welcome_message значения: event.name, event.cost_range, event.last_register, event.sending_date

    welcome_message = 'Замечательно, ты собираешься участвовать в игре.\n'\
        'Имя игры: %ИМЯ_ИГРЫ%\n'\
        'Ограничение стоимости подарка: %СТОИМОСТЬ_ПОДАРКА%\n'\
        'Период регистрации: %ПЕРИОД_РЕГИСТРАЦИИ%\n'\
        'Дата отправки подарка: %ДАТА_ОТПРАВКИ_ПОДАРКА%\n'
    update.message.reply_text(welcome_message)
    update.message.reply_text('Введи своё имя:' ,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [f'{update._effective_chat.first_name}'],
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return PHONE_NUMBER


def get_phone_number(update: Update, context: CallbackContext):
    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)
    user_name = update.message.text
    context.user_data['user_name'] = user_name
    update.message.reply_text('Введите ваш номер телефона в формате (+79999999999):',
        reply_markup=ReplyKeyboardRemove(),
    )

    return INTERESTS


def get_interests(update: Update, context: CallbackContext):
    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)

    phone_number = update.message.text
    context.user_data['phone_number'] = phone_number
    update.message.reply_text('Интересы:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Спорт', 'Образование', 'Медицина', 'Путешествия', 'Книги', 'Подписки'],
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return SANTA_LETTER


def get_santa_letter(update: Update, context: CallbackContext):
    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)
    interests = update.message.text
    context.user_data['interests'] = interests
    update.message.reply_text('Напиши мини-письмо Санте:',
        reply_markup=ReplyKeyboardRemove(),
    )

    return BYE


def good_bye_message(update: Update, context: CallbackContext):
    user_data = context.user_data
    logger.info(
        'user %s: %s', update.message.from_user.name, update.message.text
    )
    logger.info('user data: %s', user_data)
    santa_letter = update.message.text
    context.user_data['santa_letter'] = santa_letter
    info_message = f'Имя пользователя: {user_data["user_name"]}\nВаш номер телефона: {user_data["phone_number"]}\n'\
        f'Ваши интересы: {user_data["interests"]}\n'
    update.message.reply_text(info_message)
    update.message.reply_text(f'Письмо Санте: {user_data["santa_letter"]}')
    bye_message = f'Превосходно, ты в игре!\n31.12.2021 мы проведем жеребьевку и ты узнаешь имя'\
        ' и контакты своего тайного друга. Ему и нужно будет подарить подарок!'
    update.message.reply_text(bye_message)
    user_data.clear()

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(settings.TELEGRAM_API_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('game', start_game)],
        states={
            MAIN_MENU: [
                MessageHandler(
                    Filters.regex('^Меню$'), start
                ),
                MessageHandler(
                    Filters.regex('^Создать игру$'), enter_game_name
                ),
                MessageHandler(
                    Filters.regex('^Вступить в игру$'), foo, # !
                ),
                MessageHandler(
                    Filters.regex('^Мои игры$'), my_games
                ),
                MessageHandler(
                    Filters.text & ~(Filters.regex('^Выход$') | Filters.command),
                    incorrect_input
                )
            ],
            # JOIN_GAME: [
            #     MessageHandler(
            #         Filters.regex('^Вступить в игру$'), start, # !
            #     )
            # ],
            MY_GAMES: [
                MessageHandler(
                    Filters.regex('^Игры, которые я создал$'), list_games,
                ),
                MessageHandler(
                    Filters.regex('^Игры, где я участник$'), list_games,
                ),
                MessageHandler(
                    Filters.regex('^Назад$'), my_games
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                ),
                CallbackQueryHandler(game_details),
                # MessageHandler(
                #     Filters.text & ~(Filters.regex('^Меню$') | Filters.command),
                #     incorrect_input
                # )
            ],
            GAME_DETAILS: [
                CommandHandler('start', start),
                CallbackQueryHandler(start, pattern='^start$'),
                CallbackQueryHandler(draw_result),
            ],
            COST_LIMITS: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    cost_limits
                ),
                MessageHandler(
                    Filters.regex('^Назад$'), start
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                )
            ],
            CHOOSE_COST: [
                MessageHandler(
                    Filters.regex('^Да$'), set_cost
                ),
                MessageHandler(
                    Filters.regex('^Нет$'), choose_date_reg
                ),
                MessageHandler(
                    Filters.regex('^Назад$'), enter_game_name
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                )
            ],
            DATE_REG_ENDS: [
                MessageHandler(
                    Filters.regex('^до 500 рублей|500-1000 рублей|1000-2000 рублей$') & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    choose_date_reg,
                ),
                MessageHandler(
                    Filters.regex('^Назад$'), cost_limits
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                ),
                MessageHandler(
                    Filters.text,
                    incorrect_input
                )
            ],
            DATE_SEND: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    choose_date_send
                ),
                MessageHandler(
                    Filters.regex('^Назад$'), cost_limits
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                ),
            ],
            CONFIRM_DATA: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    confirm_data
                ),
                MessageHandler(
                    Filters.regex('^Назад$'),
                    choose_date_reg
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                ),
            ],
            SAVE_DATA: [
                MessageHandler(
                    Filters.regex('^Подтвердить$') & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    save_data,
                ),
                MessageHandler(
                    Filters.regex('^Назад$'),
                    choose_date_send
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                ),
                MessageHandler(
                    Filters.text,
                    incorrect_input
                ),
            ],
            USERNAME: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    start_game,
                )
            ],
            PHONE_NUMBER: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_phone_number,
                )
            ],
            INTERESTS: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_interests,
                )
            ],
            SANTA_LETTER: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_santa_letter,
                )
            ],
            BYE: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    good_bye_message,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Выход$'), done)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        main()
