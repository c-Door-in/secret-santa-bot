#!/usr/bin/env python
# pylint: disable=C0116,W0613
import logging
from typing import Dict

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from django.conf import settings
from django.core.management.base import BaseCommand
from santabot.models import User
from santabot.models import Event

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

(
    ENTER_GAME_NAME,
    COST_LIMITS,
    CHOOSE_COST,
    ENTER_COSTS,
    DATE_REG_ENDS,
    DATE_SEND,
    BYE_MESSAGE,
) = range(7)

reply_keyboard = [
    ['Создать игру'],
    ['Выход']
]

reply_yes_no = [
    ['Да', 'Нет'],
    ['Выход']
]

reply_costs = [
    ['до 500 рублей', '500-1000 рублей'],
    ['1000-2000 рублей', 'Выход']
]

reply_date_end = [
    ['до 25.12.2021', 'до 31.12.2021'],
    ['Выход']
]

markup = ReplyKeyboardMarkup(
    reply_keyboard,
    one_time_keyboard=True
)

def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    context.user_data['user_profile'], _ = User.objects.get_or_create(
        external_id=update.message.from_user.id,
        defaults={
            'name': update.message.from_user.name,
        },
    )

    update.message.reply_text(
        "Организуй тайный обмен подарками, запусти праздничное настроение!",
        reply_markup=markup,
    )
    return ENTER_GAME_NAME


def enter_game_name(update: Update, context: CallbackContext) -> int:
    """Enter game name."""
    update.message.reply_text(
        "Название:",
    )
    return COST_LIMITS


def cost_limits(update: Update, context: CallbackContext) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data['game_name'] = text

    if Event.objects.filter(name=text):
        update.message.reply_text('Такое имя уже используется.')
        update.message.reply_text('Название:')
        return COST_LIMITS

    update.message.reply_text(
        f'Ограничение стоимости подарка: да/нет?',
        reply_markup= ReplyKeyboardMarkup(
            reply_yes_no,
            one_time_keyboard=True
        )
    )
    return CHOOSE_COST


def set_cost(update: Update, context: CallbackContext) -> int:
    """Set cost."""

    update.message.reply_text(
        f'Выберите ценовой диапазон:',
        reply_markup= ReplyKeyboardMarkup(
            reply_costs,
            one_time_keyboard=True
        )
    )

    return DATE_REG_ENDS


def choose_date_reg(update: Update, context: CallbackContext) -> int:
    """Choose reg date ends."""
    text = update.message.text
    context.user_data['cost_range'] = text

    update.message.reply_text(
        f'Период регистрации участников:',
        reply_markup= ReplyKeyboardMarkup(
            reply_date_end,
            one_time_keyboard=True
        )
    )
    return DATE_SEND


def choose_date_send(update: Update, context: CallbackContext) -> int:
    """Choose send date."""
    text = update.message.text
    context.user_data['last_register_date'] = text

    update.message.reply_text(
        f'Дата отправки подарка:',
        reply_markup= ReplyKeyboardMarkup(
            reply_date_end,
            one_time_keyboard=True
        )
    )
    return BYE_MESSAGE


def bye_message(update: Update, context: CallbackContext) -> int:
    """Send bye message."""
    text = update.message.text
    context.user_data['sending_date'] = text
    
    context.user_data['event'] = Event.objects.create(
        name=context.user_data['game_name'],
        creator=context.user_data['user_profile'],
        cost_range=context.user_data['cost_range'],
        last_register_date=context.user_data['last_register_date'],
        sending_date=context.user_data['sending_date'],
    )
    print(context.user_data)
    update.message.reply_text('Отлично, Тайный Санта уже готовится к раздаче подарков!')
    update.message.reply_text('А здесь должна быть реферальная ссылка.')

    return ConversationHandler.END


def done(update: Update, context: CallbackContext) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"Вы отменили ввод данных",
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

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ENTER_GAME_NAME: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Выход$')),
                    enter_game_name
                )
            ],
            COST_LIMITS: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Выход$')),
                    cost_limits
                )
            ],
            CHOOSE_COST: [
                MessageHandler(
                    Filters.regex('^Да$'), set_cost
                ),
                MessageHandler(
                    Filters.regex('^Нет$'), choose_date_reg
                ),
            ],
            DATE_REG_ENDS: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Выход$')),
                    choose_date_reg,
                )
            ],
            DATE_SEND: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Выход$')),
                    choose_date_send,
                )
            ],
            BYE_MESSAGE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Выход$')),
                    bye_message,
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
