import json
import logging
import os
import random
import sys

#import setting
import requests

group = 'PD142'
json_file = 'info.json'
work = True


help = '''
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
        'path': '/'}
        headers = {
            'Authorization': self.__api_key
        }
        try:
            if requests.get(url, params=params, headers=headers).status_code == 200:
                return True
            else:
                return False
        except:
            return False




def get_upload_link(API_KEY, word):
    url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {
        'path': f'{group}/{word}.jpg',
        'overwrite': 'true'
    }
    headers = {
        'Authorization': API_KEY
    }
    if api_key.is_valid():
        try:
            request = requests.get(url, params=params, headers=headers)
        except:
            logging.error(f'Ошибка запроса: {request.status_code}')

    return request.json()['href']

def write_info(API_KEY, word):

    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    params = {
        'path': f'{group}/{word}.jpg',
        'fields': 'path,size'
    }
    headers = {
        'Authorization': API_KEY
    }
    try:
        request = requests.get(url, params=params, headers=headers)
    except:
        logging.error(f'Ошибка запроса: {request.status_code}')
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                data_list = json.load(f)
            except json.JSONDecodeError:
                data_list = []
    else:
        data_list = []

    new_data = {'path': request.json()['path'], 'size': request.json()['size']}
    data_list.append(new_data)

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def gen_cat(API_KEY,word):
    url = f'https://cataas.com/cat/cute/says/{word}'
    try: request = requests.get(url)
    except: logging.error(f'Ошибка запроса: {request.status_code}')

    # with open(f'{word}.jpg', 'wb') as f:
    #     f.write(request.content)
    #with open(f'{word}.jpg', 'rb') as f:   #Это если нужно сохранить копию локально и потом загрузить на диск

    headers = {
        'Authorization': API_KEY
    }

    try: r_upload = requests.put(get_upload_link(API_KEY, word), headers=headers, data=request.content)
    except:
        if r_upload.status_code != 201:
            if r_upload.status_code == 401:
                sys.exit('Неверный API ключ')
            else:
                sys.exit(f'Ошибка запроса: {r_upload.status_code}')
    print(f'Котик {word} успешно загружен')
    write_info(API_KEY,word)

def autogen_cat(API_KEY,language,count_cats):
    if language.lower() not in ['ru','en']:
        logging.error('Неверный язык')
    elif not count_cats.isdigit():
        logging.error('Количество должно быть числом')
    else:
        for i in range(int(count_cats)):
            if language.lower() == 'ru':
                with open(f'{os.path.abspath(os.curdir)}/dict/RUS.txt') as f:
                    word = random.choice(f.read().splitlines())
            elif language.lower() == 'en':
                with open(f'{os.path.abspath(os.curdir)}/dict/ENG.txt') as f:
                    word = random.choice(f.read().splitlines())
            gen_cat(API_KEY,word)



if __name__ == '__main__':
    api_key = ApiKey()
    while work:

        print(help)
        choiceCommand = input('Введите команду: ')
        if choiceCommand == 'key':
            api_key.key = input('Введите API_KEY: ')

        elif choiceCommand == 'gen':
            if api_key.is_valid():
                gen_cat(api_key.key, input('Введите слово: '))
            else:
                print('API_KEY не установлен/неправильный')

        elif choiceCommand == 'autogen':
            if api_key.is_valid():
                autogen_cat(api_key.key,input('Выберите язык (RU/EN): '), input('Введите количество случайных котиков: '))
            else:
                print('API_KEY не установлен/неправильный')

        if choiceCommand == 'exit':
            print('Выход')
            work = False