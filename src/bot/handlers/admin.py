from __future__ import annotations

from telebot.async_telebot import AsyncTeleBot, types
from telebot.states.asyncio.context import StateContext as AsyncStateContext

from src.core.logging import logger
from src.services.notification_service import NotificationService
from src.utils.text import AdminText


def register_admin_handlers(
    bot: AsyncTeleBot,
    *,
    notifications: NotificationService,
) -> None:

    def _chat_id(message: types.Message) -> int:
        chat = getattr(message, "chat", None)
        return getattr(chat, "id", 0)

    def _user_id(message: types.Message) -> int | None:
        return getattr(getattr(message, "from_user", None), "id", None)

    @bot.message_handler(commands=["stats"], isadmin=True)
    async def handle_stats(message: types.Message, state: AsyncStateContext):
        response = AdminText.stats_message()
        await notifications.send_message(_chat_id(message), response)

    @bot.message_handler(commands=["loglevel"], isadmin=True)
    async def handle_loglevel(message: types.Message, state: AsyncStateContext):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await notifications.send_message(_chat_id(message), AdminText.log_level_usage())
            return
        level = parts[1].strip().upper()
        if level not in logger.LOG_LEVEL_ORDER:
            await notifications.send_message(_chat_id(message), AdminText.log_level_usage())
            return

        logger.LOG_LEVEL = level
        logger.ACCEPTED_LOG_LEVELS = logger.LOG_LEVEL_ORDER[
            logger.LOG_LEVEL_ORDER.index(level) :
        ]
        await notifications.send_message(_chat_id(message), AdminText.log_level_changed(level))
        logger.info("Log level changed by admin to %s", level)


__all__ = ["register_admin_handlers"]
