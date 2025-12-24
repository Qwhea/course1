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
Сгенерировать котика: gen
Сгенерировать много котиков: autogen
Выйти: exit 
"""

help_text_dog = """
Выбрана версия DOG
Выйти: exit 
"""

class YDApi:

    def __init__(self):
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.__key = ''

        while self.__key == '':
            key = input('Введите API_KEY Яндекс Диска: ')
            if self.is_valid(key):
                self.__key = key
            else:
                print('Неверный API_KEY')
                continue

        self.headers = {
            'Authorization': self.__key
        }

    def is_valid(self, key = ''):
        if key == '':
            key = self.__key
        params = {
            'path': '/'
        }
        headers = {
            'Authorization': key
        }
        try:
            if requests.get(self.url, params=params, headers=headers, timeout=REQUEST_TIMEOUT).status_code == 200:
                return True
            else:
                return False
        except requests.RequestException as e:
            logging.error(f'Ошибка запроса: {e}')
            return False

    def create_dir(self, path):
        params = {
            'path': path
        }
        request = requests.put(self.url, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT)
        if request.status_code == 201:
            print(f'Папка "{path}" успешно создана')
        else:
            if request.status_code == 409:
                print(f'Папка "{path}" уже существует')
            else:
                print(f'Ошибка создания папки: {request.status_code}')

    def dir_exist(self, path):

        params = {
            'path': path
        }

        request = requests.get(self.url, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT)
        if request.status_code == 200:
            return True
        else:
            return False

    def write_info(self, word = '', breed = '', subbreed = '', filename = ''):
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

        request = requests.get(self.url, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT)
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

    def gen_cat(self,word):
        if not api.dir_exist(GROUP):
            api.create_dir(GROUP)
        url =  'https://cataas.com/cat/cute/says/'
        url_upload = f'{self.url}/upload'
        params = {
            'path': f'{GROUP}/{word}.jpg',
            'overwrite': 'true',
            'url' : f'{url}{word}'
        }
        try:
            response = requests.post(url_upload, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
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
                        response = requests.get(answer, headers=self.headers, timeout=REQUEST_TIMEOUT)
                        status = response.json()['status']

                        if status == 'success':
                            pbar.update(100 - pbar.n)
                            self.write_info(word)
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
        except requests.RequestException as e:
            logging.error(f'Ошибка загрузки изображения: {e}')

    def autogen_cat(self, language, count_cats):
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
                self.gen_cat(word)

    def save_dog(self, dog, subbreed=''):
        if subbreed:
            url = f'https://dog.ceo/api/breed/{dog}/{subbreed}/images/random'
        else:
            url = f'https://dog.ceo/api/breed/{dog}/images/random'
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        get_dog = response.json()['message']
        filename = get_dog.split('/')[-1]
        if not api.dir_exist(f'{GROUP}/{dog}'):
            api.create_dir(f'{GROUP}/{dog}')

        url_upload = f'{self.url}/upload'

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
        try:
            response = requests.post(url_upload, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT)
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
                    response = requests.get(answer, headers=self.headers, timeout=REQUEST_TIMEOUT)
                    status = response.json()['status']

                    if status == 'success':
                        pbar.update(100 - pbar.n)
                        if subbreed != '':
                            api.write_info(breed = dog, subbreed = subbreed, filename = filename)
                        else:
                            api.write_info(breed = dog, filename = filename)
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

def translate(word):
    url = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
    params = {
        'key': DICT_API_KEY,
        'lang': 'ru-en',
        'text': word
    }
    tr = requests.get(url, params=params, timeout=REQUEST_TIMEOUT).json()['def'][0]['tr'][0]['text'].lower()
    return tr

def contains_russian(text):
    alphabet=set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    return not alphabet.isdisjoint(text.lower())

def get_all_breeds():
    url = 'https://dog.ceo/api/breeds/list/all'
    all_breeds = requests.get(url, timeout=REQUEST_TIMEOUT).json()['message']
    return all_breeds

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    api = YDApi()

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
            command = input('Введите команду: ')

            if command == 'gen':
                api.gen_cat(input('Введите слово: '))

            elif command == 'autogen':
                api.autogen_cat(input('Выберите язык (RU/EN): '), input('Введите количество случайных котиков: '))

            if command == 'exit':
                version = ''
                continue
        elif version == 'dog':
            all_breeds = get_all_breeds()
            print(help_text_dog)
            command = input('Введите породу/команду: ')

            if command != 'exit':
                if contains_russian(command):
                    dog = translate(command)
                else:
                    dog = command.lower()

                if dog in all_breeds:
                    if not all_breeds[dog]:
                            api.save_dog(dog = dog)
                    else:
                        for subbreed in all_breeds[dog]:
                            api.save_dog(dog, subbreed)
                else:
                    logging.error('Порода собаки не найдена')

            else:
                version = ''
                continue