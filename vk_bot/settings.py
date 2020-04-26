from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

env = Env()
env.read_env()

VK_TOKEN = env("VK_TOKEN")

VK_START_KEYBOARD_BUTTONS = [
    [{"label": "Начать", "color": "primary", "payload": {"command": "start"}}],
    [{"label": "Правила выборки", "color": "primary", "payload": {"command": "rules"}}],
    [{"label": "Добавить правило", "color": "positive", "payload": {"command": "add_rule"}}],
    [{"label": "Удалить правило", "color": "negative", "payload": {"command": "remove_rule"}}],
    [{"label": "Статистика", "color": "primary", "payload": {"command": "stats"}}],
    [{"label": "Поток", "color": "primary", "payload": {"command": "stream"}}],
]

START_KEYBOARD = VkKeyboard()

# START_KEYBOARD.lines = VK_START_KEYBOARD_BUTTONS

for line in VK_START_KEYBOARD_BUTTONS:
    for btn in line:
        START_KEYBOARD.add_button(
            label=btn.get("label"), color=btn.get("color") or VkKeyboardColor.DEFAULT, payload=btn.get("payload")
        )
    START_KEYBOARD.add_line()

START_KEYBOARD.lines.pop(-1)

CORE_BASE_URL = env("CORE_BASE_URL", "https://localhost:8000")
INTERNAL_TOKEN = env("INTERNAL_TOKEN", "1")
SERVICE_TAG = env("SERVICE_TAG", "vk")
