from __future__ import annotations

from telebot.async_telebot import AsyncTeleBot, types
from telebot.states.asyncio.context import StateContext as AsyncStateContext

from src.core.logging import logger
from src.core.states import UserStates
from src.services.notification_service import NotificationService
from src.utils.text import HelpText, WelcomeText


def register_general_handlers(
    bot: AsyncTeleBot,
    *,
    notifications: NotificationService,
) -> None:

    def _chat_id(message: types.Message) -> int:
        chat = getattr(message, "chat", None)
        return getattr(chat, "id", 0)

    def _user_id(message: types.Message) -> int | None:
        return getattr(getattr(message, "from_user", None), "id", None)

    @bot.message_handler(commands=["start"], isprivchat=True)
    async def handle_start(message: types.Message, state: AsyncStateContext):
        await notifications.send_message(
            _chat_id(message),
            WelcomeText.greeting(message.from_user),
        )

    @bot.message_handler(commands=["help"], isprivchat=True)
    async def handle_help(message: types.Message, state: AsyncStateContext):
        await notifications.send_message(
            _chat_id(message),
            HelpText.help_message(),
        )

    @bot.message_handler(commands=["ping"], isprivchat=True)
    async def handle_ping(message: types.Message, state: AsyncStateContext):
        await notifications.send_message(_chat_id(message), "pong")

    @bot.message_handler(commands=["cancel"], isprivchat=True)
    async def handle_cancel(message: types.Message, state: AsyncStateContext):
        await state.set(UserStates.idle)
        await notifications.send_message(_chat_id(message), WelcomeText.cancelled())

    # Add your custom handlers here


__all__ = ["register_general_handlers"]
