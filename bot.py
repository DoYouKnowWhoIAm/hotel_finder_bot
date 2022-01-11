import telebot
import my_parser
from datetime import date, timedelta

# имя бота @AFKtestBot
TOKEN = '5052517322:AAGXCjHaK_TUpWGrvFdmwuWdXgwgK8fkOw4'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_message(
        message.from_user.id,
        'выбери одну из команд:\n/help — помощь по командам бота,\n'
        '/lowprice — вывод самых дешёвых отелей в городе,\n'
        '/highprice — вывод самых дорогих отелей в городе,\n'
        '/bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра,\n'
        '/history — вывод истории поиска отелей\n'
    )


@bot.message_handler(content_types=['text'])
def get_command(message):
    if message.text == '/lowprice':
        msg = bot.send_message(message.from_user.id, 'в каком городе ищем?')
        bot.register_next_step_handler(msg, set_city_step)
    else:
        bot.send_message(message.chat.id, 'пока я знаю только команду /lowprice')


def set_city_step(message):
    my_parser.LOCATION_ID = my_parser.get_city_id(message.text)
    msg = bot.send_message(message.from_user.id, 'сколько отелей показать?')
    bot.register_next_step_handler(msg, set_number_hotels_step)


def set_number_hotels_step(message):
    my_parser.HOTELS_NUM = message.text
    msg = bot.send_message(message.from_user.id, 'показать фотографии?')
    bot.register_next_step_handler(msg, set_photo)


def set_photo(message):
    current_date = date.today()
    tomorrow_date = date.today() + timedelta(days=1)
    print(current_date, tomorrow_date)
    result = my_parser.get_hotels(city_id=my_parser.LOCATION_ID, hotel_num=my_parser.HOTELS_NUM, check_in=current_date,
                                  check_out=tomorrow_date, price='PRICE')

    for i in result:
        hotel = ''
        for j, k in i.items():
            hotel += f'{j}: {k}\n'
        bot.send_message(message.from_user.id, hotel)


bot.infinity_polling()
