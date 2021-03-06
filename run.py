#!/usr/bin/python3
# -*- coding: utf-8 -*

import json
import uuid
import logging

import apiai
from telegram.ext import Updater, CommandHandler, Filters, \
    MessageHandler, InlineQueryHandler
import telegram
from telegram import InlineQueryResultArticle, InputTextMessageContent

from config import TELEGRAM_TOKEN, ADMIN_CHAT_ID, DIALOGFLOW_TOKEN


def start(bot, update):
    chat_id = update.message.chat_id
    bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
    reply = dialogflow_event_request('TELEGRAM_WELCOME', chat_id)
    bot.send_message(chat_id=chat_id, text=reply)


def text(bot, update):
    chat_id = update.message.chat_id
    bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
    reply = dialogflow_text_request(update.message.text, chat_id)
    bot.send_message(chat_id=chat_id, text=reply)


def inline(bot, update):
    query = update.inline_query.query
    if not query:
        return
    session_id = update.inline_query.from_user.id
    dialogflow_reply = dialogflow_text_request(query, session_id)
    reply = list()
    reply.append(
        InlineQueryResultArticle(
            id=uuid.uuid4(),
            title=query.capitalize(),
            input_message_content=InputTextMessageContent(dialogflow_reply),
            description=dialogflow_reply
        )
    )
    bot.answer_inline_query(update.inline_query.id, reply)


def dialogflow_request(request, session_id):
    request.session_id = session_id
    response = request.getresponse().read().decode()
    response_json = json.loads(response, strict=False)
    return response_json['result']['fulfillment']['messages'][0]['speech']


def dialogflow_event_request(event, session_id):
    request = DIALOGFLOW.event_request(apiai.events.Event(event))
    return dialogflow_request(request, session_id)


def dialogflow_text_request(query, session_id):
    request = DIALOGFLOW.text_request()
    request.query = query
    return dialogflow_request(request, session_id)


logging.info('Program started')

# Init dialogflow
DIALOGFLOW = apiai.ApiAI(DIALOGFLOW_TOKEN)

# Init telegram
BOT = telegram.Bot(TELEGRAM_TOKEN)
UPDATER = Updater(token=TELEGRAM_TOKEN)
DISPATCHER = UPDATER.dispatcher
logging.info('Bot started')
if ADMIN_CHAT_ID:
    BOT.sendMessage(ADMIN_CHAT_ID, text='Bot started.')

# Add telegram handlers
START_HANDLER = CommandHandler('start', start)
DISPATCHER.add_handler(START_HANDLER)
TEXT_HANDLER = MessageHandler(Filters.text, text)
DISPATCHER.add_handler(TEXT_HANDLER)
INLINE_HANDLER = InlineQueryHandler(inline)
DISPATCHER.add_handler(INLINE_HANDLER)

# Start polling and wait on idle state
UPDATER.start_polling()
UPDATER.idle()
if ADMIN_CHAT_ID:
    BOT.sendMessage(ADMIN_CHAT_ID, text='Program aborted.')
logging.info('Program aborted')
