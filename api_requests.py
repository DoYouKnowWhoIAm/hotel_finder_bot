import time
from datetime import datetime
import json
import requests
from decouple import config
from telebot import types
from loguru import logger
import re
import os

HEADERS = {
    'x-rapidapi-host': "hotels4.p.rapdapi.com",
    'x-rapidapi-key': config('KEY')
}


@logger.catch
def request_api(url, querystring):
    """
    Отправляет запрос на rapidapi.com
    :param url:
    :param querystring: полученные параметры для запроса
    :return: результат запроса по переданным параметрам
    """
    response = requests.request('GET', url, headers=HEADERS, params=querystring, timeout=10)
    if response.status_code == 200:
        data = json.loads(response.text)
        logger.info(response.status_code)

        return data

    else:
        return None


@logger.catch
def get_city_id(location):
    """
    Находит id города по названию
    :param location: название города
    :return: id города
    """
    url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
    querystring = {'query': location, 'locale': 'ru_RU', 'currency': 'RUB'}
    try:
        data = request_api(url, querystring)
        location_id = data['suggestions'][0]['entities'][0]['destinationId']

        return location_id
    except IndexError:
        return None


@logger.catch()
def get_hotels(city_id, page_size, check_in, check_out, sort):
    """
    Возвращает словарь отелей по заданным параметрам для команд
    /lowprice и /highprice.
    :param city_id: id города.
    :param page_size: размер страницы (количество отелей, заданный пользователем).
    :param check_in: дата заезда, по умолчанию сегодняшняя дата.
    :param check_out: дата выезда, по умолчанию завтрашняя дата.
    :param sort: параметр сортировки найденных отелей (дешевые/дорогие).
    :return: словарь, содержащий информацию по найденным отелям.
    """
    hotels_dict = dict()
    url = 'https://hotels4.p.rapidapi.com/properties/list'
    querystring = {'destinationId': city_id,
                   'pageNumber': '1',
                   'pageSize': page_size,
                   'checkIn': check_in,
                   'checkOut': check_out,
                   'adults1': '1',
                   'sortOrder': sort,
                   'locale': 'ru_RU',
                   'currency': 'RUB'}
    data = request_api(url, querystring)

    for i_elem in data['data']['body']['searchResults']['results']:
        hotels_dict[i_elem['id']] = dict()
        hotels_dict[i_elem['id']]['Название'] = i_elem['name']
        if i_elem['address'].get('streetAddress') is None:
            hotels_dict[i_elem['id']]['Адрес'] = 'не указан'
        else:
            hotels_dict[i_elem['id']]['Адрес'] = i_elem['address']['streetAddress']
        hotels_dict[i_elem['id']]['Расстояние до центра'] = i_elem['landmarks'][0]['distance']
        hotels_dict[i_elem['id']]['Цена'] = i_elem['ratePlan']['price']['current']
        hotels_dict[i_elem['id']]['Ссылка на отель'] = 'https://hotels.com/ho' + str(i_elem['id'])

    return hotels_dict


@logger.catch()
def get_bestdeal_hotels(city_id, page_size, check_in, check_out, price_min, price_max, min_dist, max_dist):
    """
    Возвращает словарь отелей по заданным параметрам для команды /bestdeal.
    :param city_id:
    :param page_size: размер страницы (количество отелей, заданный пользователем).
    :param check_in: дата заезда, выбранная пользователем.
    :param check_out: дата выезда, выбранная пользователем.
    :param price_min: минимальная цена, выбранная пользователем.
    :param price_max: максимальная цена, выбранная пользователем.
    :param min_dist: минимальное расстояние до центра города.
    :param max_dist: максимальное расстояние до центра города.
    :return: словарь, содержащий информацию по найденным отелям.
    """
    hotels_dict = dict()
    url = 'https://hotels4.p.rapidapi.com/properties/list'
    querystring = {'destinationId': city_id,
                   'pageNumber': '1',
                   'pageSize': '25',
                   'checkIn': check_in,
                   'checkOut': check_out,
                   'adults1': '1',
                   "priceMin": price_min,
                   "priceMax": price_max,
                   'sortOrder': 'PRICE_HIGHEST_FIRST',
                   'locale': 'ru_RU',
                   'currency': 'RUB'}
    start = datetime.now()
    now = time.time()
    time_out = 15
    while True:
        if time_out < time.time() - now:
            return None
        data = request_api(url, querystring)

        for i_elem in data['data']['body']['searchResults']['results']:
            distance = re.findall(r'\d[,.]?\d', i_elem['landmarks'][0]['distance'])[0].replace(',', '.')
            if float(min_dist) <= float(distance) <= float(max_dist):
                hotels_dict[i_elem['id']] = dict()
                hotels_dict[i_elem['id']]['Название'] = i_elem['name']
                if i_elem['address'].get('streetAddress') is None:
                    hotels_dict[i_elem['id']]['Адрес'] = 'не указан'
                else:
                    hotels_dict[i_elem['id']]['Адрес'] = i_elem['address']['streetAddress']
                hotels_dict[i_elem['id']]['Расстояние до центра'] = i_elem['landmarks'][0]['distance']
                hotels_dict[i_elem['id']]['Цена'] = i_elem['ratePlan']['price']['current']
                hotels_dict[i_elem['id']]['Ссылка на отель'] = 'https://hotels.com/ho' + str(i_elem['id'])
            if len(hotels_dict) == int(page_size):
                return hotels_dict

        querystring['pageNumber'] = str(int(querystring.get('pageNumber')) + 1)


@logger.catch()
def get_photos(hotel_id, page_size):
    """
    Возвращает список url для фото к выбранным отелям.
    :param hotel_id: id отеля.
    :param page_size: количество фотографий, указанное пользователем.
    :return: список url-ссылок фотографий отеля.
    """
    url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
    querystring = {'id': hotel_id}
    data = request_api(url, querystring)
    photos_list = []
    count = 0
    for i_key in data['hotelImages']:
        if count == int(page_size):
            break
        count += 1
        photos_list.append(types.InputMediaPhoto(i_key['baseUrl'].format(size='y')))
    print(photos_list)
    return photos_list


@logger.catch()
def history(user, command, result):
    """
    Сохранение команды, текущего времени и полученного результата в файл.
    :param user: id пользователя, имя файла для истории пользователя.
    :param command: введенная пользователем команда.
    :param result: информация по найденным отелям.
    :return: None
    """
    if not os.path.exists('history'):
        os.mkdir('history')
    path = os.path.abspath(os.path.join('history', f'{user}.txt'))
    with open(path, 'a', encoding='utf-8') as file:
        data = f'{command}\n{datetime.today()}\n\n{result}***\n'
        file.write(data)
