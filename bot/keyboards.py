from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_task_keyboard(task_id: str, task_url: str) -> InlineKeyboardMarkup:
    """Generates an inline keyboard for a task."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Переглянути задачу", url=task_url)
    builder.button(text="Відмітити виконаною", callback_data=f"done:{task_id}")
    builder.adjust(1)
    return builder.as_markup()
