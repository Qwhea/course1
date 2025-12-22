import json
import logging
import os
import random
import sys
import time
import requests


group = 'PD142'
json_file = 'info.json'

help_text = '''
Ввести API_KEY: key
Сгенерировать котика: gen
Сгенерировать много котиков: autogen
Выйти: exit 
'''

class ApiKey:
    def __init__(self):
        self.__api_key = ''

    @property
    def key(self):
        return self.__api_key

    @key.setter
    def key(self, value):
        self.__api_key = value
        if self.is_valid():
            self.__api_key = value.strip()
            print(f'API_KEY "{self.__api_key}" установлен')
        else:
            self.__api_key = ''
            logging.error('Неверный API ключ')

    def is_valid(self):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {
            'path': '/'
        }
        headers = {
            'Authorization': self.__api_key
        }
        try:
            if requests.get(url, params=params, headers=headers).status_code == 200:
                return True
            else:
                return False
        except requests.RequestException as e:
            logging.error(f'Ошибка запроса: {e}')
            return False

def write_info(api_key, word):
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    params = {
        'path': f'{group}/{word}.jpg',
        'fields': 'path,size'
    }
    headers = {
        'Authorization': api_key
    }
    try:
        request = requests.get(url, params=params, headers=headers)
        request.raise_for_status()
    except requests.RequestException as e:
        logging.error(f'Ошибка запроса: {e}')
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                data_list = json.load(f)
            except json.JSONDecodeError:
                data_list = []
    else:
        data_list = []

    new_data = {
        'path': request.json()['path'],
        'size': request.json()['size']
    }
    data_list.append(new_data)

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def gen_cat(api_key, word):
    url =  'https://cataas.com/cat/cute/says/'
    url_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {
        'path': f'{group}/{word}.jpg',
        'overwrite': 'true',
        'url' : f'{url}{word}'
    }
    headers = {
        'Authorization': api_key
    }
    try:
        response = requests.post(url_upload, params=params, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        sys.exit(f'Ошибка загрузки изображения: {e}')
    answer = response.json()['href']

    while True:
        response = requests.get(answer, headers=headers)
        status = response.json()['status']

        if status == 'success':
            print(f'Котик "{word}" успешно загружен')
            write_info(api_key, word)
            break
        elif status == 'in-progress':
            print('Загрузка...')
            time.sleep(1)
            continue
        else:
            error = response.json()['message']
            print(f'Ошибка загрузки: {error}')
            break


def autogen_cat(api_key, language, count_cats):
    if language.lower() not in ['ru', 'en']:
        logging.error('Неверный язык')
    elif not count_cats.isdigit():
        logging.error('Количество должно быть числом')
    else:
        dict_dir = 'dict'
        dict_path = os.path.join(dict_dir, f'{language.lower()}.txt')
        for i in range(int(count_cats)):
            if language.lower() == 'ru':
                with open(dict_path) as f:
                    word = random.choice(f.read().splitlines())
            elif language.lower() == 'en':
                with open(dict_path) as f:
                    word = random.choice(f.read().splitlines())
            gen_cat(api_key, word)

if __name__ == '__main__':
    api_key = ApiKey()
    while True:
        print(help_text)
        choice_command = input('Введите команду: ')
        if choice_command == 'key':
            api_key.key = input('Введите API_KEY: ')

        elif choice_command == 'gen':
            if api_key.is_valid():
                gen_cat(
                    api_key.key,
                    input('Введите слово: '))
            else:
                print('API_KEY не установлен/неправильный')

        elif choice_command == 'autogen':
            if api_key.is_valid():
                autogen_cat(api_key.key,input('Выберите язык (RU/EN): '), input('Введите количество случайных котиков: '))
            else:
                print('API_KEY не установлен/неправильный')

        if choice_command == 'exit':
            print('Выход')
            break