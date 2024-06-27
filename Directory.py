import telebot
import sqlite3
from telebot import types

TOKEN = 'TOKEN'

# Функция для создания соединения с базой данных и создания таблицы users
def create_db():
    conn = sqlite3.connect('user_data.db', check_same_thread=False)
    cursor = conn.cursor()

    # Создаем таблицу users, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone_number TEXT,
            entrance TEXT,
            apartment TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Функция для создания соединения с базой данных
def get_connection():
    conn = sqlite3.connect('user_data.db', check_same_thread=False)
    return conn

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

# Перед запуском бота создаем таблицу users
create_db()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Проверяем, является ли пользователь администратором
    admin_id = admin_id  # Замените на ID вашего администратора
    if message.from_user.id == admin_id:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        item = types.KeyboardButton('Выгрузить данные')
        markup.add(item)
        bot.send_message(message.chat.id, "Вы администратор. Используйте кнопку для выгрузки данных.", reply_markup=markup)
    else:
        # Проверяем, есть ли данные о пользователе в базе
        user_id = message.from_user.id
        if check_user_exists(user_id):
            bot.send_message(message.chat.id, "Вы уже зарегистрированы в системе.")
        else:
            bot.send_message(message.chat.id, "Добро пожаловать! Пожалуйста, укажите ваше ФИО:")
            bot.register_next_step_handler(message, process_full_name)

# Функция для проверки наличия данных о пользователе в базе
def check_user_exists(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Функция для обработки ФИО пользователя
def process_full_name(message):
    full_name = message.text
    bot.send_message(message.chat.id, "Теперь укажите ваш номер телефона:")
    bot.register_next_step_handler(message, process_phone_number, full_name)

# Функция для обработки номера телефона пользователя
def process_phone_number(message, full_name):
    phone_number = message.text
    bot.send_message(message.chat.id, "Укажите номер вашего подъезда:")
    bot.register_next_step_handler(message, process_entrance, full_name, phone_number)

# Функция для обработки номера подъезда пользователя
def process_entrance(message, full_name, phone_number):
    entrance = message.text
    bot.send_message(message.chat.id, "Укажите номер вашей квартиры:")
    bot.register_next_step_handler(message, save_user_data, full_name, phone_number, entrance)

# Функция для сохранения данных пользователя в базу данных
def save_user_data(message, full_name, phone_number, entrance):
    apartment = message.text
    user_id = message.from_user.id

    # Используем функцию для создания соединения с базой данных
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Сохраняем данные пользователя в базу данных
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, full_name, phone_number, entrance, apartment)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, full_name, phone_number, entrance, apartment))
        conn.commit()

        # Отправляем сообщение пользователю о завершении регистрации
        bot.send_message(message.chat.id, "Вы успешно зарегистрированы.")
    except Exception as e:
        print(f"Error saving user data: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении данных. Обратитесь к администратору.")
    finally:
        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

# Обработчик кнопки "Выгрузить данные" для администратора
@bot.message_handler(func=lambda message: message.text == 'Выгрузить данные')
def handle_export_data(message):
    admin_id = message.from_user.id
    if admin_id != admin_id:  # Замените на ID вашего администратора
        bot.send_message(message.chat.id, "Доступ запрещен.")
        return

    # Используем функцию для создания соединения с базой данных
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Запрос данных всех зарегистрированных пользователей
        cursor.execute('SELECT * FROM users')
        users_data = cursor.fetchall()

        if users_data:
            # Запись данных в файл
            with open('exported_data.txt', 'w', encoding='utf-8') as file:
                for user in users_data:
                    file.write(f"Пользователь ID: {user[0]}\n")
                    file.write(f"ФИО: {user[1]}\n")
                    file.write(f"Номер телефона: {user[2]}\n")
                    file.write(f"Подъезд: {user[3]}\n")
                    file.write(f"Квартира: {user[4]}\n\n")

            # Отправка файла администратору
            with open('exported_data.txt', 'rb') as file:
                bot.send_document(admin_id, file)
        else:
            bot.send_message(message.chat.id, "В базе данных нет зарегистрированных пользователей.")
    except Exception as e:
        print(f"Error exporting data: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при выгрузке данных. Обратитесь к администратору.")
    finally:
        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

# Запускаем бота
bot.polling()
