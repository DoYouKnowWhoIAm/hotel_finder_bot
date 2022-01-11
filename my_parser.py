import json
import requests


HEADERS = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': "48b6b0faa6msha1bf07be06709fap142167jsn75e3fc90a596"
    }

LOCATION_ID = ''
HOTELS_NUM = ''


def request_api(url, querystring):
    response = requests.get(url, headers=HEADERS, params=querystring)
    data = json.loads(response.text)

    return data


def get_city_id(location):
    """ находит id города по названию """
    url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
    querystring = {'query': location, 'locale': 'ru_RU', 'currency': 'RUB'}
    data = request_api(url, querystring)
    location_id = data['suggestions'][0]['entities'][0]['destinationId']

    return location_id


def get_hotels(city_id, hotel_num, check_in, check_out, price):
    """ ф-ия для команды /lowprice """
    hotels_list = []
    url = 'https://hotels4.p.rapidapi.com/properties/list'
    querystring = {'destinationId': city_id, 'pageNumber': '1', 'pageSize': hotel_num, 'checkIn': check_in,
                   'checkOut': check_out, 'adults1': '1', 'sortOrder': price, 'locale': 'ru_RU', 'currency': 'RUB'}
    data = request_api(url, querystring)

    for i_elem in data['data']['body']['searchResults']['results']:
        cur_hotel = dict()
        cur_hotel['название'] = i_elem['name']
        cur_hotel['адрес'] = i_elem['address']['streetAddress']
        cur_hotel['расстояние до центра'] = i_elem['landmarks'][0]['distance']
        cur_hotel['цена за сутки'] = i_elem['ratePlan']['price']['current']
        cur_hotel['ссылка на отель'] = 'https://ru.hotels.com/ho' + str(i_elem['id'])
        hotels_list.append(cur_hotel)

    return hotels_list

