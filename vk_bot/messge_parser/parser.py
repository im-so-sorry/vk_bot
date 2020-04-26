import json
from typing import List

from vk_api.longpoll import Event


class CommandDescription:
    """
    Класс описания команды
        :param command_name: str - наименование команды, которое будет парситься из сообщения,
                команда не должна иметь пробельных символов
        :param help_info: str - вспомогательная информация при выводе команды /help
        :param visibility: bool - видимость команды, если False,
                то команда будет выводиться только при вызове /help admin_pincode
        :param access_level: int - уровень доступа, от 1 до 10, 10 самый низший
        :param args_info: str - информация о аргументах команды
    """

    def __init__(
        self,
        command_name: str,
        action,
        help_info: str,
        visibility: bool = True,
        access_level: int = 10,
        args_info: str = None,
    ):
        if " " in command_name:
            raise ValueError("spaces in command name not allowed")
        self.name = command_name
        self.action = action
        self.access_level = access_level
        self.visibility = visibility
        self.help_info = help_info
        self.args_info = args_info


"""
    Пересечение словарей
"""


def dict_intersect(first_dict: dict, second_dict: dict):
    return dict(first_dict.items() & second_dict.items())


class MessageParser(object):
    """
    Класс обработки сообщений и парсинга команд
        :param command_symbol: str = '/' - командный символ, с которого должны начинаться передаваемые боту команды
        :param admin_pincode: int = 1 - код доступа администратора для выполнения привилеригированных команд
    """

    def __init__(self, command_symbol: str = "/", admin_pincode: int = 1):
        self.command_symbol = command_symbol
        self.commands = {}
        self.admin_pincode = admin_pincode
        self.add_command(
            "help", action=self.list_commands, help_info="Lists all commands", args_info="admin pin code"
        )

    """
        Получение списка команд бота
        :param event: Event
        :param pin: int = 0 - код доступа администратора
            если переданый pin совпадает с admin_pincode, то в результат выдачи добавятся привилеригированные команды
        :return { "message": str }
    """

    def list_commands(self, event: Event, pin: int = 0, *args):
        infos = []
        try:
            pin = int(pin)
        except Exception as e:
            pin = 0

        for command in self.commands.values():
            if command.visibility or (pin == self.admin_pincode):
                info = "{0}{1} - {2}".format(self.command_symbol, command.name, command.help_info)
                if command.args_info is not None and len(command.args_info) > 0:
                    info += "\n  Args: " + command.args_info

                infos.append(info)

        return {"message": "\n\n".join(infos)}

    """
        Добавление модуля с командами
        :param {"commad": CommandDescription}
    """

    def add_module_commands(self, commands: dict):
        intersection = dict_intersect(self.commands, commands)
        if len(intersection) > 0:
            raise ValueError("duplicate commands {0}".format(str(intersection)))
        for command in commands:
            if type(commands[command]) is not CommandDescription:
                raise ValueError("command must be CommandDescription class")
        self.commands.update(commands)

    """
        Добавить одну команду
        :param command_name: str - наименование команды, используется для вызова через бота
        :param action: function(event: Event, some_arguments, *args) - исполняемая функция, первый аргумент должен быть
            event: vk_api.longpoll.Event последним должен приниматься список пргументов переменной длинны 
        :param visibility - видимость команды при вызове help, если false, то будет выдаваться только при запросе с 
            кодом администратора
        :param help_info - вспомогательная информация по команде
        :param args_info - информация по аргументам команды
    """

    def add_command(
        self, command_name: str, action, visibility: bool = True, help_info: str = "", args_info: str = None
    ):
        if command_name in self.commands:
            raise ValueError("duplicate command {0}".format(command_name))
        elif " " in command_name:
            raise ValueError("spaces in command name not allowed")

        self.commands[command_name] = CommandDescription(
            command_name, action, help_info, visibility, args_info
        )

    """
        Парсинг сообщения и проверка на соответствии команде бота
        :param message: str - разбираемое сообщение
        :return (function(), arguments) or None - tuple из вызываемой функции и аргументов для этой функции, если 
            удалось разобрать сообщение и найти совпадение в списке команд бота, иначе None
    """

    def parse_command(self, event: Event):
        try:
            payload = event.payload
            payload = json.loads(payload)
        except Exception as e:
            return None, None
        return payload.get("command"), payload.get("args", [])

    def parse(self, event: Event):
        message = event.text.strip(" ").lower()

        command, args = self.parse_command(event)

        if command:
            command_description = self.commands[command]
            command_args: List[str] = args
            return command_description.action, command_args

        if not message.startswith(self.command_symbol):
            return None

        try:
            command_name = message[len(self.command_symbol) :].split(" ")[0]
        except IndexError:
            raise ValueError("Can't parse command name")

        if command_name not in self.commands:
            raise ValueError("No such command: {0}".format(command_name))

        command_description = self.commands[command_name]
        command_args = message.split(" ")[1:]

        return command_description.action, command_args
