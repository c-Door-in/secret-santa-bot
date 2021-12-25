#!/usr/bin/env python
# pylint: disable=C0116,W0613
import logging
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from pytz import timezone
from santabot.models import Event, User
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from .bot_utils import datetime_from_str

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

(
    MAIN_MENU,
    ENTER_GAME_NAME,
    COST_LIMITS,
    CHOOSE_COST,
    ENTER_COSTS,
    DATE_REG_ENDS,
    DATE_SEND,
    CONFIRM_DATA,
    BYE_MESSAGE,
) = range(9)


def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""

    context.user_data.clear()

    context.user_data['user_profile'], _ = User.objects.get_or_create(
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
                ['Выход']
            ],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return ENTER_GAME_NAME


def enter_game_name(update: Update, context: CallbackContext) -> int:
    """Enter game name."""

    if 'cost_limits' in context.user_data:
        del context.user_data['cost_limits']

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

    if 'cost_range' in context.user_data:
        del context.user_data['cost_range']

    if 'cost_limits' not in context.user_data:
        text = update.message.text
        context.user_data['game_name'] = text

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
    context.user_data['cost_limits'] = True

    return CHOOSE_COST


def set_cost(update: Update, context: CallbackContext) -> int:
    """Set cost choosing flag and ask costs limits."""

    if 'last_register_date' in context.user_data:
        del context.user_data['last_register_date']

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
    return DATE_REG_ENDS


def choose_date_reg(update: Update, context: CallbackContext) -> int:
    """Choose end of registration."""

    if 'sending_date' in context.user_data:
        del context.user_data['sending_date']

    # обновлять только если прилетело
    # с предыдущего а не с последующего
    if 'last_register_date' not in context.user_data:
        text = update.message.text
        context.user_data['cost_range'] = text

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


def incorrect_date(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Пожалуйста, введите дату в формате "дд.мм.гггг: 15.12.2021"'
    )
    return BYE_MESSAGE


def incorrect_date_send(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Пожалуйста, введите дату в формате "дд.мм.гггг: 15.12.2021"'
    )
    return DATE_SEND


def incorrect_confirm_date(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Пожалуйста, введите дату в формате "дд.мм.гггг: 15.12.2021"'
    )
    return CONFIRM_DATA


def incorrect_date_after(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Пожалуйста, введите еще не прошедшую дату.'
    )
    return DATE_SEND


def incorrect_date_before(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        (
            'Пожалуйста, введите дату не ранее'
            f' {context.user_data["last_register_date"]}'
        )
    )
    return CONFIRM_DATA


def incorrect_confirm(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Я вас не понял, введите "Создать игру" или "Меню".'
    )
    return BYE_MESSAGE


def choose_date_send(update: Update, context: CallbackContext) -> int:
    """Choose send date."""
    # если следующего нет, значит прилетели с данными правильными (дата)
    # от предыдущего,
    # если же он есть - то прилетели без данных, и вообще не за этим.
    # т.е. если прилетели назад менять дату отправки,
    # а дату окончания регистрации не нужно трогать.
    if 'sending_date' not in context.user_data:
        text = update.message.text
        end_reg_date = datetime_from_str(date_str=text, time_str='12:00:00')
        # TODO: вынести?
        loctz = timezone('Europe/Moscow')
        if end_reg_date < loctz.localize(datetime.now()):
            return incorrect_date_after(update, context)

        context.user_data['last_register_date'] = end_reg_date

    # если попали сюда по кнопке "Назад",
    # то не все данные собраны и флаг надо убать
    if 'is_all_collected' in context.user_data:
        del context.user_data['is_all_collected']

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
    # сначала обработка даты отправки подарков,
    # если еще не было наполнения,
    # т.е. если прилетели не по кнопке "Назад".
    if 'is_all_collected' not in context.user_data:
        text = update.message.text
        sending_date_time_obj = datetime_from_str(
            date_str=text, time_str='12:00:00'
        )
        if sending_date_time_obj < context.user_data['last_register_date']:
            return incorrect_date_before(update, context)

        context.user_data['sending_date'] = sending_date_time_obj
        context.user_data['is_all_collected'] = True  # already collected flag

    # вывод всех данных для подтверждения
    message = ('Вы ввели:\n\n'

        f'Название игры: {context.user_data["game_name"]}\n'
        f'Ваше имя: {context.user_data["user_profile"]}\n'
        f'Ограничение цены подарка: {context.user_data["cost_range"]}\n'
        f'Дата окончания регистрации: {context.user_data["last_register_date"]}\n'
        f'Дата отправки подарка: {context.user_data["sending_date"]}\n\n'

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

    return BYE_MESSAGE


def bye_message(update: Update, context: CallbackContext) -> int:
    """Save collected data in DB and send bye message."""

    context.user_data['event'] = Event.objects.create(
        name=context.user_data['game_name'],
        creator=context.user_data['user_profile'],
        cost_range=context.user_data['cost_range'],
        last_register_date=context.user_data['last_register_date'],
        sending_date=context.user_data['sending_date'],
    )
    print(f'{context.user_data=}')
    game_id = context.user_data['event'].pk
    print(f'GAME_ID - {game_id}')

    update.message.reply_text(
        'Отлично, Тайный Санта уже готовится к раздаче подарков!',
        # reply_markup=ReplyKeyboardRemove(),
    )
    update.message.reply_text(
        'А здесь должна быть реферальная ссылка.',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[['Выход', 'Меню']],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    )
    context.user_data.clear()

    return MAIN_MENU


def done(update: Update, context: CallbackContext) -> int:
    """End conversation."""
    user_data = context.user_data

    update.message.reply_text(
        'До свидания!',
        reply_markup=ReplyKeyboardRemove(),
    )
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
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(
                    Filters.regex('^Меню$'), start
                )
            ],
            ENTER_GAME_NAME: [
                MessageHandler(
                    Filters.regex('^Создать игру$'),
                    enter_game_name
                ),
                MessageHandler(
                    Filters.regex('^Вступить в игру$'), start
                ),
                MessageHandler(
                    Filters.regex('^Мои игры$'), start
                )
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
                    Filters.text & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    choose_date_reg,
                ),
                MessageHandler(
                    Filters.regex('^Назад$'), cost_limits
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                )
            ],
            DATE_SEND: [
                MessageHandler(
                    Filters.regex('^(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.20\d{2}$'),
                    choose_date_send,
                ),
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    incorrect_date_send
                ),
                MessageHandler(
                    Filters.regex('^Назад$'), cost_limits
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                )
            ],
            CONFIRM_DATA: [
                    MessageHandler(
                    Filters.regex('^(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.20\d{2}$'),
                    confirm_data,
                ),
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    incorrect_confirm_date
                ),
                MessageHandler(
                    Filters.regex('^Назад$'),
                    choose_date_reg
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
                )
            ],
            BYE_MESSAGE: [
                MessageHandler(
                    Filters.regex('^Подтвердить$') & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    bye_message,
                ),
                MessageHandler(
                    Filters.regex('^Назад$'),
                    choose_date_send
                ),
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Назад$') | Filters.regex('^Меню$')),
                    incorrect_confirm
                ),
                MessageHandler(
                    Filters.regex('^Меню$'), start
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
