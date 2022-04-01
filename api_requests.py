from datetime import datetime
import json
import requests
from decouple import config
from loguru import logger

HEADERS = {
    'x-rapidapi-host': "hotels4.p.rapdapi.com",
    'x-rapidapi-key': config('KEY')
}


@logger.catch
def request_api(url, querystring):
    response = requests.request('GET', url, headers=HEADERS, params=querystring, timeout=10)
    if response.status_code == 200:
        data = json.loads(response.text)
        logger.info(response.status_code)

        return data

    else:
        return None


@logger.catch
def get_city_id(location):
    """ Находит id города по названию """

    url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
    querystring = {'query': location, 'locale': 'ru_RU', 'currency': 'RUB'}
    try:
        data = request_api(url, querystring)
        location_id = data['suggestions'][0]['entities'][0]['destinationId']

        return location_id
    except IndexError:
        return None


@logger.catch()
def get_hotels(city_id, page_size, check_in, check_out, sort, price_min=None, price_max=None):
    hotels_dict = dict()
    url = 'https://hotels4.p.rapidapi.com/properties/list'
    querystring = {'destinationId': city_id,
                   'pageNumber': '1',
                   'pageSize': page_size,
                   'checkIn': check_in,
                   'checkOut': check_out,
                   'adults1': '1',
                   "priceMin": price_min,
                   "priceMax": price_max,
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
def get_photos(hotel_id, page_size):
    url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
    querystring = {'id': hotel_id}
    data = request_api(url, querystring)
    photos_list = []
    count = 0
    for i_key in data['hotelImages']:
        if count == int(page_size):
            break
        count += 1
        photos_list.append(i_key['baseUrl'])

    return photos_list


@logger.catch()
def history(user, command, result):
    with open(f'{user}.txt', 'a', encoding='utf-8') as file:
        data = f'{command}\n{datetime.today()}\n\n{result}***\n'
        file.write(data)
