import json

import folium
import requests
from environs import Env
from geopy import distance
from flask import Flask


def fetch_coordinates(apikey, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    places_found = response.json()['response']['GeoObjectCollection']['featureMember']
    most_relevant = places_found[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def fetch_coffee_shop_data(coffee_shop, user_coordinates):
    title = coffee_shop['Name']
    coordinates = coffee_shop['geoData']['coordinates']
    latitude, longitude = coordinates
    coffee_shop_distance = distance.distance((longitude, latitude), user_coordinates).km
    return {
        'title': title,
        'latitude': latitude,
        'longitude': longitude,
        'distance': coffee_shop_distance
    }


def get_coffee_shop_distance(coffee_shop):
    return coffee_shop['distance']


def place_to_map(coffee_shops_map, coffee_shop):
    latitude = coffee_shop['latitude']
    longitude = coffee_shop['longitude']
    title = coffee_shop['title']
    folium.Marker(
        location=[longitude, latitude],
        popup=title
    ).add_to(coffee_shops_map)


def main():
    map_filename = "coffee_shops_map.html"

    def open_map():
        with open(map_filename, encoding='utf-8') as file:
            return file.read()

    env = Env()
    env.read_env()
    coffee_shops_file = 'coffee.json'
    coffee_shops_num = env.int('COFFEE_SHOPS_NUM')
    apikey = env('YANDEX_GEOCODER_API_KEY')

    place = input('Где вы находитесь? ')
    user_coordinates = fetch_coordinates(apikey, place)

    with open(coffee_shops_file, encoding='cp1251') as f:
        coffee_shops = [fetch_coffee_shop_data(coffee_shop, user_coordinates)
                        for coffee_shop in json.load(f)]
    closest_coffee_shops = sorted(coffee_shops, key=get_coffee_shop_distance)[:coffee_shops_num]
    coffee_shops_map = folium.Map(location=user_coordinates, zoom_start=15)

    for coffee_shop in closest_coffee_shops:
        place_to_map(coffee_shops_map, coffee_shop)
    coffee_shops_map.save(map_filename)

    app = Flask(__name__)
    app.add_url_rule('/', 'map', open_map)
    app.run('0.0.0.0')


if __name__ == '__main__':
    main()
