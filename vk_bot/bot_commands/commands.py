# -*- coding: utf-8 -*-
import json
from collections import defaultdict

import inner_service_api
import vk_api
from inner_service_api.baraddur_service import BaraddurService
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import Event

from vk_bot import settings
from vk_bot.messge_parser.parser import CommandDescription

POSITIVE_ANSWER = ["yes", "y", "да", "д", "1"]
NEGATIVE_ANSWER = ["no", "n", "нет", "н", "0"]


class BotCommands:
    """
    Клас для хранения команд бота

    Каждая команда первым параметром принимает event типа vk_api.longpoll.Event
    Последним должен быть *args

    Каждая команда-функция возвращает dictionary с необходимыми полями, обязателен возврат параметра message, остальные
    по необходимости

    Стандартные поля:
    - message: str
    - keyboard: str(dict)
    :param database_client: DbClient - клиент доступа к базе данных
    :param vk: vk_api.VkApi - объект доступа к Api
    :param vk_session: vk_api.VkApi - объект доступа к сессии
    """

    def __init__(self, vk, vk_session: vk_api.VkApi, params=None, process_list=None):
        if process_list is None:
            process_list = list()
        if params is None:
            params = {}
        self.vk = vk
        self.vk_session = vk_session
        self.params = params
        self.process_list = process_list
        self.commands = {
            "start": CommandDescription(
                command_name="start",
                action=self.payload_start,
                help_info="show start information",
                visibility=True,
            ),
            "rules": CommandDescription(
                command_name="rules", action=self.get_rules, help_info="return rules", visibility=True
            ),
            "stats": CommandDescription(
                command_name="stats", action=self.stats, help_info="return stats", visibility=True
            ),
            "add_rule": CommandDescription(
                command_name="add_rule",
                action=self.add_rule,
                help_info="add new rule",
                args_info="tag: str, value: str",
                visibility=True,
            ),
            "remove_rule": CommandDescription(
                command_name="remove_rule",
                action=self.remove_rule,
                help_info="remove rule",
                args_info="tag: str",
                visibility=True,
            ),
            "reg": CommandDescription(
                command_name="reg",
                action=self.registrate,
                help_info="registrate already exists user",
                args_info="token: str",
                visibility=True,
            ),
            "stream": CommandDescription(
                command_name="stream",
                action=self.stream,
                help_info="Change stream state",
                args_info="",
                visibility=False,
            ),
            "_state_dispatcher": CommandDescription(
                command_name="_state_dispatcher",
                action=self._state_dispatcher,
                help_info="Change state",
                args_info="",
                visibility=False,
            ),
        }

        self.core_service = BaraddurService(
            base_url=settings.CORE_BASE_URL,
            token=settings.INTERNAL_TOKEN,
            service=settings.SERVICE_TAG
        )

        self.user_states = {}

    def _invalid_response(self, message: str = None):
        return {
            "message": "Something went wrong: {}".format(message or "")
        }

    def get_rules(self, event: Event, *args, **kwargs):
        response = self.core_service.get_rules(str(event.peer_id))
        if response.status_code != 200:
            return self._invalid_response(response.text)

        rules = response.json().get("results", [])

        rules_message = "\n".join(
            "{}) {} - {}".format(i + 1, rule.get("key"), rule.get("value"))
            for i, rule in enumerate(rules)
        )

        return {"message": rules_message}

    def stats(self, event: Event, *args, **kwargs):
        response = self.core_service.get_stats(str(event.peer_id))

        if response.status_code != 200:
            return self._invalid_response(response.text)

        stats = response.json()

        message = """Статистика\n\nВсего событий: {total}\n""".format(total=stats.get('total', 0))

        for stat in stats.get("rules", []):
            message += """< {tag} >\nОбщее количество: {total}\n""".format(tag=stat.get("tag", ""),
                                                                           total=stat.get("total", 0))

            for event_type, count in stat.get("count", {}).items():
                message += "{event_type} : {count}\n".format(event_type=event_type, count=count)

        return {"message": message}

    def add_rule(self, event: Event, *args, **kwargs):
        try:
            payload = json.loads(event.payload)
        except Exception as e:
            payload = {}

        if len(args) > 0:
            if len(args) < 2:
                return {
                    "message": "Неверный формат аргументов, /add_rule <str> <str>"
                }

            response = self.core_service.add_rule(str(event.peer_id), args[0], args[1])

            if response.status_code not in (200, 201):
                return self._invalid_response(response.text[:512])

            return {
                "message": "Правило {} - {} создано".format(args[0], args[1])
            }

        state = self.user_states.pop(str(event.peer_id), None)

        if not state:
            self.user_states[str(event.peer_id)] = "add_rule"
            return {
                "message": "Введите правило в формате <key: str> <value: str>"
            }
        else:
            params = event.text.split()
            if len(params) < 2:
                return {
                    "message": "Неверный формат аргументов, /add_rule <str> <str>"
                }

            response = self.core_service.add_rule(str(event.peer_id), params[0], params[1])

            if response.status_code not in (200, 201):
                return self._invalid_response(response.text[:512])

            return {
                "message": "Правило {} - {} создано".format(params[0], params[1])
            }


    def _state_dispatcher(self, event: Event, *args, **kwargs):
        state = self.user_states.get(str(event.peer_id))

        if not state:
            return None

        handler = getattr(self, state, None)

        if not handler:
            return None

        return handler(event, *args, **kwargs)

    def remove_rule(self, event: Event, *args, **kwargs):
        try:
            payload = json.loads(event.payload)
        except Exception as e:
            payload = {}
        if not payload or not payload.get("state"):
            response = self.core_service.get_rules(str(event.peer_id))
            if response.status_code != 200:
                return self._invalid_response(response.text)

            rules = response.json().get("results", [])

            keyboard = VkKeyboard(inline=True)

            for i, rule in enumerate(rules):
                keyboard.add_button(
                    "{}) {} - {}".format(i + 1, rule.get("key"), rule.get("value")),
                    color=VkKeyboardColor.NEGATIVE,
                    payload={
                        "command": "remove_rule",
                        "state": "select",
                        "rule": rule,
                    })
                keyboard.add_line()

            keyboard.lines.pop(-1)

            return {
                "message": "Выберите правило для удаления",
                "keyboard": keyboard.get_keyboard()
            }
        elif payload.get("state") == "select":
            rule = payload.get("rule", {})

            keyboard = VkKeyboard(inline=True)
            keyboard.add_button(
                "Удалить",
                color=VkKeyboardColor.NEGATIVE,
                payload={
                    "command": "remove_rule",
                    "state": "confirm",
                    "rule": rule,
                })
            keyboard.add_button(
                "Отменить",
                color=VkKeyboardColor.POSITIVE,
                payload={
                    "command": "start",
                })
            message = "Удалить {} - {} ?".format(rule.get("key"), rule.get("value"))
            return {
                "message": message,
                "keyboard": keyboard.get_keyboard()
            }
        elif payload.get("state") == "confirm":
            rule = payload.get("rule", {})
            response = self.core_service.remove_rule(str(event.peer_id), rule.get("key"))

            return {
                "message": "Правило удалено",
            }

    def registrate(self, event: Event, *args, **kwargs):
        return {"message": "registrate"}

    def stream(self, event: Event, *args, **kwargs):
        try:
            payload = json.loads(event.payload)
        except Exception as e:
            payload = {}

        if not payload.get("state"):
            response = self.core_service.get_user(str(event.peer_id))
            if response.status_code >= 400:
                return self._invalid_response(response.text[:512])
            result = response.json()

            keyboard = VkKeyboard(inline=True)

            if not result.get("is_streaming", False):
                keyboard.add_button(
                    "Включить",
                    color=VkKeyboardColor.POSITIVE,
                    payload={
                        "command": "stream",
                        "state": "on",
                    })
            else:
                keyboard.add_button(
                    "Выключить",
                    color=VkKeyboardColor.NEGATIVE,
                    payload={
                        "command": "stream",
                        "state": "off",
                    })

            return {
                "message": "Статус потока: {}".format("Включен" if result.get("is_streaming") else "Выключен"),
                "keyboard": keyboard.get_keyboard()
            }
        else:
            state = payload.get("state")

            response = self.core_service.switch_streaming(str(event.peer_id), state == "on")
            if response.status_code >= 400:
                return self._invalid_response(response.text[:512])

            return {
                "message": "Статус потока: {}".format("Включен" if state == "on" else "Выключен"),
            }

    def payload_start(self, event: Event, *args, **kwargs):
        """ /start
        Возвращает стартовую клавиатуру с приветственным сообщением

            :param event: Event

            :return dict {"message": str, "keyboard": str(dict) } - результат выполнения
        """
        start_keyboard = settings.START_KEYBOARD.get_keyboard()
        return {
            "message": "Welcome to EOS chat bot",
            "keyboard": start_keyboard
        }

    def help(self, event: Event, *args, **kwargs):
        return {
            "message": "",
            "keyboard": settings.START_KEYBOARD.get_keyboard()
        }
