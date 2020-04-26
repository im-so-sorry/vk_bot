from random import random

import requests
from config import *
import vk_api
import psycopg2
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from psycopg2.extras import DictCursor
import inner_service_api
from inner_service_api import baraddur_service


def main():
    session = requests.Session()
    db = psycopg2.connect(
        database=database,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cursor = db.cursor(cursor_factory=DictCursor)

    vk_session = vk_api.VkApi(
        token=token)

    vk = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)
    message = ""
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            text = event.text.split(' ')
            if text[0] == "/start":
                cursor.execute("SELECT id from users where vk_id = {}".format(event.user_id))
                row = cursor.fetchall()
                if len(row) > 0:
                    message = "Мы с тобой уже знакомы, но еще раз здравствуй!"
                else:
                    cursor.execute("INSERT INTO users (vk_id) VALUES ({})".format(event.user_id))
                    db.commit()
                    # baraddur_service.BaraddurService.get_user()
                message = "Привет, я бот, и я помогу тебе собирать информацию из медиа потока вк и twitter. Для " \
                          "работы со мной тебе понадобятся следующие команды:\n/help чтобы получить справку\n/reg " \
                          "чтобы зарегистрировать серсис для отправки уведомлений\n/aad_rule чтобы добавить новое " \
                          "правило для выборки ваших уведомлений\n/remove_rule чтобы удалить правило\n/rule чтобы " \
                          "получить список правил "

                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
                continue

            if text[0] == "/help":
                message = "/reg <ник> - регистрация сервиса\n/add_rule <тэг> <значение> - добавление " \
                          "правила\n/remove_rule <тэг> - удаление правила\n/rules - получение списка правил"
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
                continue

            if text[0] == "/reg":
                if len(text) > 2:
                    message = "Одновременно можно активировать только один аккаунт."
                    vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
                    continue

                cursor.execute("SELECT * FROM users WHERE telegram_id = {}".format(text[1]))
                if len(cursor.fetchall()) > 0:
                    message = "Этот аккаунт уже зарегистрирован"
                else:
                    cursor.execute("SELECT id from registry where reg_id = {}".format(text[1]))
                    row = cursor.fetchall()
                    ran_gen = random.randint(1000, 9999)
                    if len(row) > 0:
                        cursor.execute(
                            "UPDATE registry SET access_code = {} WHERE reg_id = {}".format(ran_gen, text[1]))
                        db.commit()
                        message = "Ты уже регистрировался, но еще не активировал свой аккаунт. Перейди по ссылке t.me " \
                                  "и введи новый код /activate {}".format(ran_gen)
                    else:
                        cursor.execute(
                            "INSERT INTO registry (id, access_token, reg_id) VALUES ({}, {}, {}})".format(event.user_id,
                                                                                                          ran_gen,
                                                                                                          text[1]))
                        db.commit()
                        message = "Хорошо, теперь тебе надо активировать этот аккаунт перейди по сыылке и введи: " \
                                  "/activate {}".format(ran_gen)

                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
                continue

            if text[0] == "/add_rule":
                # text.remove("/add_rule")
                message = ""
                for i in range(1, len(text), 2):
                    try:
                        cursor.execute("SELECT id FROM  users WHERE vk_id = {}".format(event.user_id))
                        userID = cursor.fetchone()
                        cursor.execute(
                            "INSERT INTO tag (name, value, user_id) VALUES ('{}', {}, {})".format(text[i], text[i + 1],
                                                                                                  userID[0]))
                        db.commit()
                        message += "Тэг '{}' успешо добавлен".format(text[i])
                    except Exception:
                        message += "C n'ujv '{}' что-то случилось, поробуй позже".format(text[i])

                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
                continue

            if text[0] == "/remove_rule":
                text.remove("/remove_rule")
                message = ""
                for element in text:
                    cursor.execute("SELECT id FROM  users WHERE vk_id = {}".format(event.user_id))
                    userID = cursor.fetchone()
                    cursor.execute("SELECT * FROM tag WHERE user_id = {} and name = '{}'".format(userID[0], element))
                    if len(cursor.fetchone()) > 0:
                        cursor.execute("DELETE FROM tag WHERE name = '{}' and user_id = {}".format(element, userID[0]))
                        db.commit()
                        message += "\nТэг {} успешно удален".format(element)
                    else:
                        message += "\nТэга {} не существует".format(element)
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
                continue

            if text[0] == "/rule":
                if len(text) > 1:
                    message = "Слишком много параметров"
                else:
                    cursor.execute(
                        "SELECT name from tag WHERE user_id = (SELECT id FROM users WHERE vk_id = {})".format(
                            event.user_id))
                    row = cursor.fetchall()
                    # row = baraddur_service.BaraddurService.get_rules(username=event.user_id)
                    message = "Ваши теги:"
                    i = 1
                    for element in row:
                        message += "\n{}. {}".format(i, element[0])
                        i += 1
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
                continue

            if text[0] == "/activate":
                if len(text) > 2:
                    message = "Неверный код активации"
                else:
                    cursor.execute("SELECT * from registry where reg_id = {}".format(event.user_id))
                    row = cursor.fetchone()
                    if row['access_code'] == text[1]:
                        message = "Ваш аккаунт успешно зарегистрирован"
                        cursor.execute(
                            "UPDATE users SET vk_id = {} WHERE telegram_id = {}".format(event.user_id, row['user_id']))
                        db.commit()
                    else:
                        message = "Неверный код активации"
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)

            if text[0] == "./stop":
                if text[1] == stopCode:
                    cursor.close()
                    return

            message = "Хм что то странное, я тебя не понимаю, попробуй команду /help"
            vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)


if __name__ == '__main__':
    main()
