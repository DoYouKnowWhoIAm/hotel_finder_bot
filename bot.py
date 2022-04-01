import telebot
from loguru import logger
import api_requests
from datetime import datetime, date, time, timedelta
from decouple import config
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar
import users

TOKEN = config('TOKEN')
bot = telebot.TeleBot(TOKEN)
logger.add('logs.log', format='{time} {level} {message}')


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user = users.User(chat_id)
    users.user_data[chat_id] = user
    logger.info(f'{chat_id} написал {message.text}')

    bot.send_message(chat_id, 'Привет! Чтобы посмотреть список доступных команд набери /help')


@bot.message_handler(commands=['help'])
def get_help(message):
    chat_id = message.chat.id
    user = users.User(chat_id)
    users.user_data[chat_id] = user
    logger.info(f'{chat_id} написал {message.text}')

    bot.send_message(
        chat_id,
        'выбери одну из команд:\n/help — помощь по командам бота,\n'
        '/lowprice — вывод самых дешёвых отелей в городе,\n'
        '/highprice — вывод самых дорогих отелей в городе,\n'
        '/bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра,\n'
        '/history — вывод истории поиска отелей\n'
    )


@bot.message_handler(commands=['lowprice'])
def low_price(message):
    chat_id = message.chat.id
    user = users.User(chat_id)
    users.user_data[chat_id] = user
    user.current_command = '/lowprice'
    logger.info(f'{chat_id} написал {message.text}')

    msg = bot.send_message(chat_id, 'В каком городе ищем (кроме городов РФ)?')
    bot.register_next_step_handler(msg, set_city_step)


@bot.message_handler(commands=['highprice'])
def get_command(message):
    chat_id = message.chat.id
    user = users.User(chat_id)
    users.user_data[chat_id] = user
    user.sort = 'PRICE_HIGHEST_FIRST'
    user.current_command = '/highprice'
    logger.info(f'{chat_id} написал {message.text}')

    msg = bot.send_message(chat_id, 'В каком городе ищем (кроме городов РФ)?')
    bot.register_next_step_handler(msg, set_city_step)


@bot.message_handler(commands='bestdeal')
def get_command(message):
    chat_id = message.chat.id
    user = users.User(chat_id)
    users.user_data[chat_id] = user
    user.sort = 'PRICE'
    user.current_command = '/bestdeal'
    logger.info(f'{chat_id} написал {message.text}')

    msg = bot.send_message(chat_id, 'В каком городе ищем (кроме городов РФ)?')
    bot.register_next_step_handler(msg, set_city_step)


@bot.message_handler(commands='history')
def get_history(message):
    chat_id = message.chat.id
    user = users.User(chat_id)
    users.user_data[chat_id] = user
    logger.info(f'{chat_id} написал {message.text}')

    try:
        with open(f'{chat_id}.txt', 'r', encoding='utf-8') as file:
            msg = ''
            for elem in file:
                if '***' in elem:
                    bot.send_message(chat_id, msg)
                    msg = ''
                else:
                    msg += elem
    except FileNotFoundError:
        bot.send_message(chat_id, 'История пуста')


def set_city_step(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    logger.info(f'{chat_id} написал {message.text}')

    if not message.text.isalpha():
        msg = bot.send_message(chat_id, 'Название  должно содержать только буквы')
        bot.register_next_step_handler(msg, set_city_step)
    else:
        user.city = message.text
        user.city_id = api_requests.get_city_id(user.city)
        if user.city_id is None:
            msg = bot.send_message(chat_id, 'Город не найден. Проверьте правильность ввода')
            bot.register_next_step_handler(msg, set_city_step)

        else:
            if user.current_command == '/bestdeal':
                set_check_in(message)
            else:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add('1', '3', '5')
                msg = bot.send_message(chat_id, 'Сколько отелей показать?', reply_markup=markup)
                bot.register_next_step_handler(msg, set_number_hotels_step)


def set_check_in(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today(), locale='ru').build()
    bot.send_message(chat_id, 'выберите дату заезда', reply_markup=calendar)


def set_check_out(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    calendar, step = DetailedTelegramCalendar(calendar_id=2,
                                              min_date=user.check_in + timedelta(days=1), locale='ru').build()
    bot.send_message(chat_id, 'выберите дату выезда', reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def call_back1(call):
    chat_id = call.message.chat.id
    user = users.user_data[chat_id]

    result, key, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today(), locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text('далее...', call.message.chat.id, call.message.message_id, reply_markup=key)
    elif result:
        user.check_in = result
        logger.info(f'{chat_id} написал {result}')

        bot.delete_message(call.message.chat.id, call.message.message_id)
        set_check_out(call.message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def call_back2(call):
    chat_id = call.message.chat.id
    user = users.user_data[chat_id]
    result, key, step = DetailedTelegramCalendar(calendar_id=2,
                                                 min_date=user.check_in + timedelta(days=1),
                                                 locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text('далее...', call.message.chat.id, call.message.message_id, reply_markup=key)
    elif result:
        user.check_out = result
        logger.info(f'{chat_id} написал {result}')

        bot.delete_message(call.message.chat.id, call.message.message_id)

        msg = bot.send_message(chat_id, 'Введите желаемую минимальную стоимость за сутки')
        bot.register_next_step_handler(msg, set_price_min_step)


def set_price_min_step(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    logger.info(f'{chat_id} написал {message.text}')

    if not message.text.isdigit():
        msg = bot.send_message(chat_id, 'Введите стоимость цифрами')
        bot.register_next_step_handler(msg, set_price_min_step)
    else:
        user.price_min = message.text

        msg = bot.send_message(chat_id, 'Введите желаемую максимальную стоимость')
        bot.register_next_step_handler(msg, set_price_max_step)


def set_price_max_step(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    logger.info(f'{chat_id} написал {message.text}')

    if not message.text.isdigit() or int(user.price_min) > int(message.text):
        msg = bot.send_message(chat_id, 'Введите стоимость больше указанной минимальной')
        bot.register_next_step_handler(msg, set_price_max_step)
    else:
        user.price_max = message.text
        msg = bot.send_message(chat_id, 'Введите желаемое минимальное расстояние до центра (в километрах)')
        bot.register_next_step_handler(msg, set_distance_step)


def set_distance_step(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    logger.info(f'{chat_id} написал {message.text}')

    if not message.text.isdigit():
        msg = bot.send_message(chat_id, 'Введите расстояние цифрами')
        bot.register_next_step_handler(msg, set_distance_step)
    else:
        user.distance_from_center = message.text

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('1', '3', '5')
        msg = bot.send_message(chat_id, 'Сколько отелей показать?', reply_markup=markup)
        bot.register_next_step_handler(msg, set_number_hotels_step)


def set_number_hotels_step(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    logger.info(f'{chat_id} написал {message.text}')

    if not message.text.isdigit():
        msg = bot.send_message(chat_id, 'Введите количество цифрами или выберите ответ из предложенных')
        bot.register_next_step_handler(msg, set_number_hotels_step)
    else:
        user.hotels_num = message.text

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        msg = bot.send_message(chat_id, 'Показать фотографии?', reply_markup=markup)
        bot.register_next_step_handler(msg, show_photo)


def show_photo(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    logger.info(f'{chat_id} написал {message.text}')

    if message.text.lower() == 'нет':
        user.photos_num = 0
        bot.send_message(chat_id, 'Уже ищу!')
        send_results(message)

    elif message.text.lower() == 'да':
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('1', '3', '5')
        msg = bot.send_message(chat_id, 'Сколько фото показать?', reply_markup=markup)
        bot.register_next_step_handler(msg, set_photo_num)

    else:
        msg = bot.send_message(chat_id, 'Введите Да/Нет или выберите ответ из предложенных')
        bot.register_next_step_handler(msg, show_photo)


def set_photo_num(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]
    logger.info(f'{chat_id} написал {message.text}')

    if not message.text.isdigit():
        msg = bot.send_message(chat_id, 'Введите количество цифрами или выберите ответ из предложенных')
        bot.register_next_step_handler(msg, set_photo_num)
    else:
        user.photos_num = message.text

        msg = bot.send_message(chat_id, 'Уже ищу!')
        send_results(msg)


@logger.catch
def send_results(message):
    chat_id = message.chat.id
    user = users.user_data[chat_id]

    if user.check_in is None:
        user.check_in = date.today()
        user.check_out = date.today() + timedelta(days=1)

    if user.current_command == '/lowprice' or '/highprice':
        user.hotels = api_requests.get_hotels(city_id=user.city_id, page_size=user.hotels_num, check_in=user.check_in,
                                              check_out=user.check_out, sort=user.sort)
    elif user.current_command == '/bestdeal':
        user.hotels = api_requests.get_hotels(city_id=user.city_id, page_size=user.hotels_num, check_in=user.check_in,
                                              check_out=user.check_out, sort=user.sort, price_min=user.price_min,
                                              price_max=user.price_max)
    if user.hotels:
        for i_key, i_value in user.hotels.items():
            if user.photos_num != 0:
                user.photos = api_requests.get_photos(i_key, user.photos_num)

            hotel_info = ''
            for j_key, j_value in i_value.items():
                hotel_info += f'{j_key}: {j_value}\n'
            bot.send_message(chat_id, hotel_info)
            user.results += f'{hotel_info}\n'

            if user.photos_num != 0:
                for i_photo in user.photos:
                    bot.send_photo(chat_id, i_photo.format(size='y'))

        api_requests.history(user=chat_id, command=user.current_command, result=user.results)
        user.results = ''


def run_bot():
    bot.infinity_polling()
