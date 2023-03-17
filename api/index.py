import logging
from telegram import Update, Poll, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, PollHandler, PollAnswerHandler, Dispatcher
from deta import Deta
from api.helper import get_quiz, get_motivational, TelegramWebhook
import random
from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI()
deta = Deta("d011wxuu1l1_ZDghSFpyhLyrzvzE6AArrRSnnjNwHEeW")
quiz_user = deta.Base("quiz_user")

WELCOME_MESSAGE = '''Welcome <a href="tg://user?id={user_id}">{user_name}</a> to Quiz/Motivational Bot

To use this bot 
    - send /quiz to get a random quiz
    - send /motivation to get a random motivational quote

By default, the bot will send you a quiz and a motivational quote every day at 8:00 AM UTC.


For more info send /help
'''

QUIZ_URL = "https://opentdb.com/api.php?amount=1&category=9&difficulty=easy&type=multiple"


def waiter_wrapper(func):
    def wrapper(update: Update, context: CallbackContext):
        try:
            user = update.effective_user or update.message.from_user
            msg = context.bot.send_message(
                chat_id=user.id,
                text="Please wait...",
            )
            func(update, context)
            context.bot.delete_message(
                chat_id=user.id,
                message_id=msg.message_id
            )
        except Exception as e:
            logger.error('Error happened in a Wrapper %s', e)
    return wrapper


@waiter_wrapper
def start(update: Update, context: CallbackContext):
    update.message.reply_html(WELCOME_MESSAGE.format(
        user_id=update.message.from_user.id, user_name=update.message.from_user.first_name))
    user = update.message.from_user.to_dict()
    user['key'] = str(user.get('id') or user.get('user_id'))
    if not quiz_user.get(user['key']):
        quiz_user.put(user)


@waiter_wrapper
def start_quiz(update: Update, context: CallbackContext):
    print('Quiz started')
    quiz = get_quiz()
    options = []
    options.append(quiz[0]['correctAnswer'])
    for option in quiz[0]['incorrectAnswers']:
        options.append(option)

    random.shuffle(options)
    correct = options.index(quiz[0]['correctAnswer'])
    user = update.effective_user or update.message.from_user
    context.bot.send_poll(
        chat_id=user.id,
        question=quiz[0]['question'],
        type=Poll.QUIZ,
        allows_multiple_answers=False,
        options=options,
        correct_option_id=correct,
        protect_content=True,
        is_anonymous=False,
        # TODO: add timer
    )
    return 0


def register_dispatcher(dispatcher: Dispatcher):
    dispatcher.add_handler(PollAnswerHandler(start_quiz))
    dispatcher.add_handler(PollHandler(start_quiz))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("quiz", start_quiz))


def main():
    updater = Updater("1789117801:AAG4_R5rK1Zis8sIfZlS1cj_zx1_Wa1MmZg")
    dispatcher = updater.dispatcher

    # register dispatcher
    register_dispatcher(dispatcher)

    updater.start_polling()
    updater.idle()


@app.get("/")
def index():
    return {"message": "Hello World"}


@app.post("/webhook")
def webhook(our_update: TelegramWebhook):
    bot = Bot("1789117801:AAG4_R5rK1Zis8sIfZlS1cj_zx1_Wa1MmZg")
    update = Update.de_json(our_update.to_json(), bot)
    dispatcher = Dispatcher(bot, None)

    register_dispatcher(dispatcher)

    dispatcher.process_update(update)
    return {"message": "ok"}


# if __name__ == '__main__':
#     main()