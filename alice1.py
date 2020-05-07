from flask import Flask, request
import logging
import pymorphy2

import json
import os


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}

animals = [
    'слон',
    'кролик'
]

morph = pymorphy2.MorphAnalyzer()


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:

        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ],
            'animal_index': 0
        }
        animal = animals[sessionStorage[user_id]['animal_index']]
        parse = morph.parse(animal)[0]
        word = parse.inflect({'sing', 'gent'}).word
        res['response']['text'] = f'Привет! Купи {word}!'
        res['response']['buttons'] = get_suggests(user_id)
        return

    if any(map(lambda w: w in req['request']['original_utterance'].lower(), ['ладно',
                                                                             'куплю',
                                                                             'покупаю',
                                                                             'хорошо'])):
        animal = animals[sessionStorage[user_id]['animal_index']]
        parse = morph.parse(animal)[0]
        word = parse.inflect({'sing', 'gent'}).word
        res['response']['text'] = f'{word} можно найти на Яндекс.Маркете!'.capitalize()
        sessionStorage[user_id]['animal_index'] += 1
        if sessionStorage[user_id]['animal_index'] >= len(animals):
            res['response']['end_session'] = True
            sessionStorage[user_id]['animal_index'] = 0
            return
        else:
            sessionStorage[user_id] = {
                'suggests': [
                    "Не хочу.",
                    "Не буду.",
                    "Отстань!",
                ],
                'animal_index': sessionStorage[user_id]['animal_index']
            }
            animal = animals[sessionStorage[user_id]['animal_index']]
            parse = morph.parse(animal)[0]
            word = parse.inflect({'sing', 'gent'}).word
            res['response']['text'] += f'\nА теперь купи {word}!'
            res['response']['buttons'] = get_suggests(user_id)
    else:
        animal = animals[sessionStorage[user_id]['animal_index']]
        parse = morph.parse(animal)[0]
        word = parse.inflect({'sing', 'gent'}).word
        res['response']['text'] = \
            f"Все говорят '{req['request']['original_utterance']}', а ты купи {word}!"
        res['response']['buttons'] = get_suggests(user_id)


def get_suggests(user_id):
    session = sessionStorage[user_id]

    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    if len(suggests) < 2:
        animal = animals[sessionStorage[user_id]['animal_index']]
        suggests.append({
            "title": "Ладно",
            "url": f"https://market.yandex.ru/search?text={animal}",
            "hide": True
        })

    return suggests


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
