# -*- coding: utf-8 -*-
import json
from enum import Enum


class VkKeyboardColor(Enum):
    """
    Класс-перечисление возможных цветов кнопок клавиатуры vk
    """

    PRIMARY = "primary"
    DEFAULT = "default"
    NEGATIVE = "negative"
    POSITIVE = "positive"


class VkKeyboard:
    """
    Класс конструктор для формирования клавиатуры vk
    :param one_time: bool - Если параметр False, то при нажатии на кнопку клавиатуры она скроется автоматически
    """

    def __init__(self, one_time=False):
        self.one_time = one_time

    """
    Формирует объект кнопки

        :param label: str - Текст, отображаемый на кнопке

        :param color: KBColor - цвет кнопки

        :param payload: dict - словарь используемы для последующей обработки нажатий кнопки,
            объект payload возвращается при нажатии кнопки в event.attachments,
            рекомендуется использовать словарь типа {"command": "key"}

        :param type: str - параметр для кнопки, в данный момент доступен только тип text

        :return dictionary - объект типа кнопка, в формате
            {
            "action":
                {
                    "type": str,
                    "payload": srt(dict),
                    "label": str
                },
                "color": KBColor
            }

    """

    @staticmethod
    def get_button(
        label: str,
        color: VkKeyboardColor = VkKeyboardColor.DEFAULT,
        command: str = None,
        payload: dict = None,
        type: str = "text",
    ):
        if command is not None:
            payload = {"command": command}
        elif payload is None:
            payload = {"command": label}
        button = {
            "action": {"type": type, "payload": json.dumps(payload, ensure_ascii=False), "label": label},
            "color": color.value,
        }

        return button

    """
    Формирует строку с клавиатурой

        :param buttons: list - список списков объектов типа button(возвращается методом get_button), двумерный массив,
            где каждый вложенный список представляет собой одну строку с кнопками, в одной строке не более 4-х кнопок,
            и не более 10-ти строк с кнопками, подробнее на (https://vk.com/dev/bots_docs_3)

        :param one_time: bool - параметр автоскрытия клавиатуры, если параметр False, то при нажатии кнопки клавиатура
            скроется, иначе нет

        :return raw str (dict) - сырая строка из dictionary с двумя параметрами buttons и one_time, для передачи в
            параметр keyboard метода messages.send
    """

    @staticmethod
    def get_keyboard(buttons=None, one_time: bool = False):
        if buttons is None:
            buttons = [[]]
        keyboard = {"one_time": one_time, "buttons": buttons}
        return json.dumps(keyboard, ensure_ascii=False)
