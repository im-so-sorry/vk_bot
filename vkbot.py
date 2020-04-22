import requests
from config import token
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id


def main():
    session = requests.Session()

    vk_session = vk_api.VkApi(
        token=token)

    vk = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)
    message = ""
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:

            if event.text == "/start":
                message = "Hello I can help to search mem in vk"
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
            if event.text == "/help":
                message = "/reg - регистрация сервиса\n/add_rule <tag> <value> - добавление " \
                          "правила\n/remove_rule <tag> - удаление правила\n/rules - получение списка правил"
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
            if event.text == "/reg":
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
            if event.text == "/add_rule":
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
            if event.text == "/remove_rule":
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)
            if event.text == "/rule":
                vk.messages.send(user_id=event.user_id, random_id=get_random_id(), message=message)


if __name__ == '__main__':
    main()
