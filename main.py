import json
import logging
import os
import random
import sys
import time

import requests
from tqdm import tqdm


REQUEST_TIMEOUT = 10
GROUP = 'PD142'
JSON_FILE = 'info.json'

DICT_API_KEY = 'dict.1.1.20251222T085039Z.43ce529e7f6d1aa6.635db3c798ac69e440f24d47ea226115bc9e8cbc'

help_text_cat = """
Выбрана версия CAT
Ввести API_KEY: key
Сгенерировать котика: gen
Сгенерировать много котиков: autogen
Выйти: exit 
"""

help_text_dog = """
Выбрана версия DOG
Ввести API_KEY: key
Выбрать породу: select
Выйти: exit 
"""


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
            if requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT).status_code == 200:
                return True
            else:
                return False
        except requests.RequestException as e:
            logging.error(f'Ошибка запроса: {e}')
            return False

def create_dir(api_key, path):
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    params = {
        'path': path
    }
    headers = {
        'Authorization': api_key
    }
    request = requests.put(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    if request.status_code == 201:
        print(f'Папка "{path}" успешно создана')
    else:
        if request.status_code == 409:
            print(f'Папка "{path}" уже существует')
        else:
            print(f'Ошибка создания папки: {request.status_code}')

def dir_exist(api_key, path):
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    params = {
        'path': path
    }
    headers = {
        'Authorization': api_key
    }
    request = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    if request.status_code == 200:
        return True
    else:
        return False

def write_info(api_key, word = '', breed = '', subbreed = '', filename = ''):
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    if version == 'cat':
        params = {
            'path': f'{GROUP}/{word}.jpg',
            'fields': 'path,size'
        }
    else:
        if subbreed != '':
            params = {
                'path': f'{GROUP}/{breed}/{subbreed}-{filename}',
                'fields': 'path,size'
            }
        else:
            params = {
                'path': f'{GROUP}/{breed}/{filename}',
                'fields': 'path,size'
            }

    headers = {
        'Authorization': api_key
    }

    request = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    request.raise_for_status()

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                data_list = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                data_list = []
    else:
        data_list = []

    new_data = {
        'path': request.json()['path'],
        'size': request.json()['size']
    }
    data_list.append(new_data)

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def gen_cat(api_key, word):
    if(not dir_exist(api_key, GROUP)):
        create_dir(api_key, GROUP)
    url =  'https://cataas.com/cat/cute/says/'
    url_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {
        'path': f'{GROUP}/{word}.jpg',
        'overwrite': 'true',
        'url' : f'{url}{word}'
    }
    headers = {
        'Authorization': api_key
    }
    try:
        response = requests.post(url_upload, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f'Ошибка загрузки изображения: {e}')
    answer = response.json()['href']

    with tqdm(
            desc=f"Загрузка котика '{word}'",
            total=100,
            unit='% ',
            ncols=80,
            colour='green',
            leave=True
    ) as pbar:
        while True:
            try:
                response = requests.get(answer, headers=headers, timeout=REQUEST_TIMEOUT)
                status = response.json()['status']

                if status == 'success':
                    pbar.update(100 - pbar.n)
                    write_info(api_key, word)
                    pbar.close()
                    print(f'Котик "{word}" успешно загружен')
                    break
                elif status == 'in-progress':
                    if pbar.n < 95:
                        pbar.update(10 if pbar.n < 95 else 1)
                    time.sleep(1)
                    continue
                else:
                    error = response.json()['message']
                    print(f'Ошибка загрузки: {error}')
                    break
            except requests.RequestException as e:
                pbar.set_postfix_str("ошибка сети")
                print(f"\n Ошибка проверки статуса: {e}")
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
                with open(dict_path, encoding='utf-8') as f:
                    word = random.choice(f.read().splitlines())
            elif language.lower() == 'en':
                with open(dict_path, encoding='utf-8') as f:
                    word = random.choice(f.read().splitlines())
            gen_cat(api_key, word)

def contains_russian(text, alphabet=set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')):
    return not alphabet.isdisjoint(text.lower())

def translate(word):
    url = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
    params = {
        'key': DICT_API_KEY,
        'lang': 'ru-en',
        'text': word
    }
    tr = requests.get(url, params=params, timeout=REQUEST_TIMEOUT).json()['def'][0]['tr'][0]['text'].lower()
    return tr

def reserve_dog(api_key, dog, subbreed=''):
    if subbreed:
        url = f'https://dog.ceo/api/breed/{dog}/{subbreed}/images/random'
    else:
        url = f'https://dog.ceo/api/breed/{dog}/images/random'
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    get_dog = response.json()['message']
    filename = get_dog.split('/')[-1]
    if(not dir_exist(api_key, f'{GROUP}/{dog}')):
        create_dir(api_key, f'{GROUP}/{dog}')

    url_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    if subbreed != '':
        params = {
            'path': f'{GROUP}/{dog}/{subbreed}-{filename}',
            'overwrite': 'true',
            'url' : get_dog
        }
    else:
        params = {
            'path': f'{GROUP}/{dog}/{filename}',
            'overwrite': 'true',
            'url' : get_dog
        }
    headers = {
        'Authorization': api_key
    }
    try:
        response = requests.post(url_upload, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        sys.exit(f'Ошибка загрузки изображения: {e}')
    answer = response.json()['href']
    if subbreed != '':
        dog_load = f'{dog}-{subbreed}'
    else:
        dog_load = dog

    with tqdm(
            desc=f"Загрузка собаки '{dog_load}'",
            total=100,
            unit='% ',
            ncols=80,
            colour='green',
            leave=True
    ) as pbar:
        while True:
            try:
                response = requests.get(answer, headers=headers, timeout=REQUEST_TIMEOUT)
                status = response.json()['status']

                if status == 'success':
                    pbar.update(100 - pbar.n)
                    if subbreed != '':
                        write_info(api_key, breed = dog, subbreed = subbreed, filename = filename)
                    else:
                        write_info(api_key, breed = dog, filename = filename)
                    pbar.close()
                    print(f'Собака "{dog_load}" успешно загружена')
                    break
                elif status == 'in-progress':
                    if pbar.n < 95:
                        pbar.update(10 if pbar.n < 95 else 1)
                    time.sleep(1)
                    continue
                else:
                    error = response.json()['message']
                    print(f'Ошибка загрузки: {error}')
                    break
            except requests.RequestException as e:
                pbar.set_postfix_str("ошибка сети")
                print(f"\n Ошибка проверки статуса: {e}")
                break



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    api_key = ApiKey()
    version = ''
    while True:
        if version == '':
            version = input("Введите версию cat/dog: ")
            if version == 'cat' or version == 'dog':
                continue
            else:
                version = ''
                continue
        if version == 'cat':
            print(help_text_cat)
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
                version = ''
                continue
        elif version == 'dog':
            print(help_text_dog)
            choice_command = input('Введите команду: ')

            if choice_command == 'key':
                api_key.key = input('Введите API_KEY: ')

            if choice_command == 'select':
                if api_key.is_valid():
                    save_dog = input('Введите название породы собаки: ')
                    url = 'https://dog.ceo/api/breeds/list/all'
                    all_breeds = requests.get(url, timeout=REQUEST_TIMEOUT).json()['message']
                    if(contains_russian(save_dog)):
                        dog = translate(save_dog)
                    else:
                        dog = save_dog.lower()

                    if dog in all_breeds:
                        if not all_breeds[dog]:
                            reserve_dog(api_key.key, dog = dog)
                        else:
                            for subbreed in all_breeds[dog]:
                                reserve_dog(api_key.key, dog, subbreed)
                    else:
                        logging.error('Порода собаки не найдена')
                else:
                    print('API_KEY не установлен/неправильный')

            if choice_command == 'exit':
                version = ''
                continue
