import telebot
import sqlite3
from telebot import types
from KEY import token

bot = telebot.TeleBot(token, parse_mode=None)

conn = sqlite3.connect("users.db", check_same_thread=False)

cur = conn.cursor()

# Обработчик команд.
@bot.message_handler(commands=['start'])
def send_start_message(message):
    keyboard1 = telebot.types.InlineKeyboardMarkup()
    keyboard1.row(
        types.InlineKeyboardButton('Да', callback_data='start_asking'),
        types.InlineKeyboardButton('Нет', callback_data='stop')
    )

    keyboard2 = telebot.types.InlineKeyboardMarkup()
    keyboard2.row(
        types.InlineKeyboardButton('Посмотреть анкеты', callback_data='start_viewing'),
        types.InlineKeyboardButton('Заполнить анкету заново', callback_data='start_asking')
    )
    keyboard2.row(
        types.InlineKeyboardButton('Назад', callback_data='main_menu'),
    )

    # Проверяем, есть ли в базей анкета с таким айди.
    cur.execute(f"""SELECT EXISTS(SELECT ID FROM resumes
                    WHERE ID = {message.from_user.id})
    """)
    has_resume = cur.fetchone()
    if has_resume[0] == 0:
        bot.reply_to(message, "Привет, для добавления анкеты ты должен ответить на пару вопросов о себе,"
                              " анкету можно удалить и заполнить заново. Начать заполнение анкеты?",
                              reply_markup=keyboard1)
    else:
        bot.reply_to(message, "Привет, твоя анкета уже лежит в нашей базе, ты можешь посмотреть сожителей или заново заполнить анкету",
                              reply_markup=keyboard2)


# Обработчик коллбек кнопок.
@bot.callback_query_handler(func=lambda call: True)
def callback_first_question(call):

    if call.data == "start_asking":
        start_asking(call)

    elif call.data == "stop":
        # TODO: показать главное меню
        pass

    elif call.data in ["answer_moscow", "answer_saintp"]:

        cities = {"answer_moscow": "Москва", "answer_saintp": "СПБ"}
        cur.execute(f"""UPDATE resumes
                        SET City = '{cities[call.data]}'
                        WHERE ID = '{call.message.chat.id}'""")
        conn.commit()

        smoking_asking(call)

    elif call.data in ["answer_not_smoking", "answer_smoking"]:
        smoking = {"answer_not_smoking": 0, "answer_smoking": 1}
        cur.execute(f"""UPDATE resumes
                        SET Smoking = '{smoking[call.data]}'
                        WHERE ID = '{call.message.chat.id}'""")
        conn.commit()
        bot.edit_message_text('Анкета успешно оставлена!', call.message.chat.id, call.message.message_id)


# Выводим первый вопрос, создаем запись в бд.
def start_asking(call):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton('Москва', callback_data='answer_moscow'),
        types.InlineKeyboardButton('Питер', callback_data='answer_saintp')
    )

    # Удаляем запись, если уже есть резюме и заполняем заново.
    cur.execute(f"""DELETE FROM resumes
                    WHERE ID = '{call.message.chat.id}'
                    """)

    conn.commit()

    bot.edit_message_text('Ваш город:', call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    cur.execute(f"""INSERT OR IGNORE INTO resumes (ID)
                    VALUES('{call.message.chat.id}')""")
    conn.commit()


# 2 вопрос про курение, обновляем бд данными про город, данными из объекта call.
def smoking_asking(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton('Да', callback_data='answer_smoking'),
        types.InlineKeyboardButton('Нет', callback_data='answer_not_smoking')
    )

    bot.edit_message_text("Вы курите?", call.message.chat.id, call.message.message_id, reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def help_message(message):
    pass


bot.polling(none_stop=True, interval=0)
