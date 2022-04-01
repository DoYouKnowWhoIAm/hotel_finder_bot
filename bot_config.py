import telebot
from decouple import config

TOKEN = config('TOKEN')
bot = telebot.TeleBot(TOKEN)

HEADERS = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': config('KEY')
    }