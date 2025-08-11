from telebot_import import bot
from split_lines import split_lines
from DATABASE_TG import Database
from telebot import types
from logg import logger

db = Database()

# консольный ввод
@bot.message_handler(commands=["console_input"])
def console_input(message):
    c_text = bot.send_message(
        message.chat.id,
        """
Введите задачи через _ЗАПЯТУЮ_
иначе будет : _задача1задача2_""",
        parse_mode="MarkdownV2",
    )
    bot.register_next_step_handler(c_text, process_tasks)


def process_tasks(message):
    tasks = split_lines(message.text)
    if not tasks:
        bot.send_message(message.chat.id, "Вы не ввели ни одной задачи!")
        return
    ask_for_name(message, tasks)


# работа с файлом
@bot.message_handler(commands=["get_file"])
def handle_get_file(message):
    bot.send_message(
        message.chat.id,
        """
Отправьте txt\-файл с задачами
Если после задачи нет запятой, то : _задача1задача2_""",
        parse_mode="MarkdownV2",
    )

    @bot.message_handler(content_types=["document"])
    def handle_document(message):
        try:
            if not message.document.file_name.lower().endswith(".txt"):
                bot.reply_to(
                    message,
                    "Поддерживаются только файлы *.txt*",
                    parse_mode="MarkdownV2",
                )
                return
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_content = downloaded_file.decode("utf-8")
            tasks = split_lines(file_content)
            if not tasks:
                bot.reply_to(message, "Файл не содержит задач!")
                return
            ask_for_name(message, tasks)
        except Exception as e:
            print(e)


# получение имени и сохранение данных в бд
def ask_for_name(message, tasks):
    name_mes = bot.send_message(
        message.chat.id, "Введите *имя* для сохранения задач:", parse_mode="MarkdownV2"
    )
    bot.register_next_step_handler(name_mes, lambda msg: save_to_db(msg, tasks))


def save_to_db(message, tasks):
    try:
        username = message.text.strip().lower().title()
        if not username:
            bot.send_message(
                message.chat.id,
                "Имя *не* может быть *пустым*!",
                parse_mode="MarkdownV2",
            )
            return
        db.save_tasks(username, tasks, message.chat.id)
        db.get_all_info(message.chat.id)
        bot.send_message(message.chat.id, "Данные успешно сохранены в БД!")
        

    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при сохранении")
        logger.info(e)


#удалить все с кнопкой
@bot.message_handler(commands=["delete_all"])
def delete_all(message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    button_yes = types.InlineKeyboardButton("Да", callback_data="yes")
    button_no = types.InlineKeyboardButton("Нет", callback_data="no")
    markup.add(button_yes, button_no)

    bot.send_message(
        message.chat.id,
        f"{message.from_user.first_name}, вы точно хотите удалить все данные?",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data in ["yes", "no"])
def handle_delete_choice(call):
    if call.data == "yes":
        try:
            db.delete_all(call.message.chat.id)
            bot.edit_message_text(
                "Все ваши данные были успешно удалены",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка: {str(e)}")
    else:
        bot.edit_message_text(
            "Удаление данных отменено",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )

#удалить по id 
@bot.message_handler(commands=["delete_by_id"])
def take_id_for_delete(message):
    ID = bot.send_message(
        message.chat.id,
        """
Вы выбрали удалить задачи по ID
напишите номера ID через *запятую*
            *_Например: 1,2,3_*""",
        parse_mode="MarkdownV2",
    )

    bot.register_next_step_handler(ID, process_ID_delete)


def process_ID_delete(message):
    ID_to_delete = split_lines(message.text)
    if not ID_to_delete:
        bot.send_message(message.chat.id, "_Вы не ввели ID_", parse_mode="MarkdownV2")
        return
    db.delete_only_id_tasks(ID_to_delete, message.chat.id)

#удалить по имени
@bot.message_handler(commands=["delete_by_username"])
def take_name_for_delete(message):
    name_mes = bot.send_message(
        message.chat.id, "Введите *имя* для удаления задач:", parse_mode="MarkdownV2"
    )
    bot.register_next_step_handler(name_mes, process_name_delete)

def process_name_delete(message):
    username = message.text
    db.delete_user_tasks(username.strip().lower().title(),message.chat.id)


# получить всю информацию из БД
@bot.message_handler(commands=["get_all_info"])
def info_from_bd(message):
    bot.send_message(message.chat.id, "Ваша информация из БД:")
    db.get_all_info(message.chat.id)


# start
@bot.message_handler(commands=["start"])
def start(message):
    global chat_id
    chat_id = message.chat.id
    bot.send_message(
        message.chat.id,
        """
Добрый день\\!
Я первый бот Тани\\!

||Напиши /help, чтобы посмотреть список команд||""",
        parse_mode="MarkdownV2",
    )


# help
@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(
        message.chat.id,
        """
Наши доступные команды:
/start - команда начала работы
/console_input - ввод задач для БД
/get_file - получить файл с данными для БД
/delete_all - удалить из БД все
/delete_by_id - удалить из БД задачи по id
/delete_by_username - удалить из БД задачи по имени
/get_all_info - получить всю информацию из БД""",
    )

bot.polling()

