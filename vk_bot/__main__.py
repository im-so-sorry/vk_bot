import argparse
import json
import threading

import vk_api

from vk_api.longpoll import Event, VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from vk_bot import settings
from vk_bot.messge_parser.parser import MessageParser
from vk_bot.bot_commands.commands import BotCommands

msg_parser = MessageParser()

running = False


class MessageHandler(threading.Thread):
    """
    Класс обертка для обработки входящих сообщений в раздельных потоках для каждого пользователя
    принимает единственный параметр event: Event со входящим событием
    при старте обработки события от пользователя в dictionary process_list помечается
    """

    def __init__(self, event: Event):
        super().__init__()
        self.event = event

    def run(self):
        answer = None

        if self.event.attachments:
            try:
                payload_data = json.loads(self.event.attachments["payload"])
                payload_command = payload_data["command"]
                payload_args = ""
                if "args" in payload_data:
                    payload_args = " " + str(payload_data["args"])
                p_answer = {}
                try:
                    p_res = msg_parser.parse(msg_parser.command_symbol + payload_command + payload_args)
                    if p_res is not None:
                        action, args = p_res
                        p_answer = action(self.event, *args)
                except ValueError as e:
                    p_answer = {"message": "Error at parsing: {0}".format(e)}
                except Exception as e:
                    p_answer = {"message": str(e)}

                if "keyboard" in p_answer:
                    vk.messages.send(
                        peer_id=self.event.peer_id,
                        message=p_answer.get("message"),
                        keyboard=p_answer.get("keyboard"),
                        random_id=get_random_id(),
                    )
                else:
                    vk.messages.send(
                        peer_id=self.event.peer_id, message=p_answer.get("message"), random_id=get_random_id()
                    )

                vk.messages.markAsRead(peer_id=self.event.peer_id, start_message_id=self.event.message_id)
                print(payload_data)
                return
            except Exception as e:
                answer = {"message": str(e)}

        try:
            res = msg_parser.parse(self.event)
            if res is not None:
                action, args = res
                answer = action(self.event, *args)
            else:
                command = msg_parser.commands.get("_state_dispatcher")
                answer = command.action(self.event)
        except ValueError as e:
            answer = {"message": "Error at parsing: {0}".format(e)}
        except Exception as e:
            answer = {"message": str(e)}

        if answer is None:
            return

        if "keyboard" in answer:
            vk.messages.send(
                peer_id=self.event.peer_id,
                message=answer["message"],
                keyboard=answer["keyboard"],
                random_id=get_random_id(),
            )
        else:
            vk.messages.send(
                peer_id=self.event.peer_id,
                message=answer["message"],
                ensure_ascii=False,
                random_id=get_random_id(),
            )
        vk.messages.markAsRead(peer_id=self.event.peer_id)


def main():
    longpoll = VkLongPoll(vk_session)

    global running
    try:
        running = True

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                t = MessageHandler(event)
                t.start()

    except InterruptedError:
        running = False


if __name__ == "__main__":
    vk_session = vk_api.VkApi(token=settings.VK_TOKEN)

    vk = vk_session.get_api()

    args_parser = argparse.ArgumentParser(description="")
    args_parser.add_argument("--wait", "-w", type=float, dest="wait", help="Timeout", default=5)
    parsed_args = args_parser.parse_args()

    commands = BotCommands(vk, vk_session)

    msg_parser.add_module_commands(commands.commands)

    main()
