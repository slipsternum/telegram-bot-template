"""Async-friendly logging that can mirror to Telegram."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from telebot.async_telebot import AsyncTeleBot

from src.core import config


class Logger:
    LOG_LEVEL_ORDER = ["DEBUG", "INFO", "WARN", "ERROR"]
    LOG_LEVEL = config.LOG_LEVEL if config.LOG_LEVEL in LOG_LEVEL_ORDER else "INFO"
    ACCEPTED_LOG_LEVELS: list[str] = LOG_LEVEL_ORDER[
        LOG_LEVEL_ORDER.index(LOG_LEVEL) :
    ]

    BOT_USERNAME = "bot"
    _queue: asyncio.Queue[dict[str, Any] | object] | None = None
    _session: aiohttp.ClientSession | None = None
    _worker_task: asyncio.Task[None] | None = None
    _sentinel: object = object()

    @classmethod
    async def init(cls, bot: AsyncTeleBot | None = None) -> None:
        if cls._worker_task is not None:
            await cls.shutdown()

        cls._queue = asyncio.Queue(maxsize=500)
        cls._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        cls._worker_task = asyncio.create_task(cls._worker_loop(), name="logger-worker")

        if bot is not None:
            try:
                me = await bot.get_me()
                cls.BOT_USERNAME = getattr(me, "username", cls.BOT_USERNAME) or cls.BOT_USERNAME
            except Exception:
                pass

        cls.ACCEPTED_LOG_LEVELS = cls.LOG_LEVEL_ORDER[
            cls.LOG_LEVEL_ORDER.index(cls.LOG_LEVEL) :
        ]
        cls.info("Logger initialised.")

    @classmethod
    def _should_log(cls, level: str) -> bool:
        if not cls.ACCEPTED_LOG_LEVELS:
            cls.ACCEPTED_LOG_LEVELS = cls.LOG_LEVEL_ORDER[
                cls.LOG_LEVEL_ORDER.index(cls.LOG_LEVEL) :
            ]
        return level in cls.ACCEPTED_LOG_LEVELS

    @classmethod
    def log(
        cls,
        message: str,
        *,
        level: str = "INFO",
        to_channel: bool | None = None,
        to_console: bool = True,
    ) -> None:
        if not cls._should_log(level):
            return
        ts = datetime.now(timezone(timedelta(hours=config.TIMEZONE_OFFSET)))
        formatted = f"[{ts.isoformat()}] [{cls.BOT_USERNAME}] [{level}] {message}"

        if to_console:
            print(formatted)

        send_to_channel = to_channel
        if send_to_channel is None:
            send_to_channel = bool(config.LOGGING_BOT_TOKEN and config.LOGGER_CHAT_ID)
        if (
            send_to_channel
            and cls._queue is not None
            and config.LOGGING_BOT_TOKEN
            and config.LOGGER_CHAT_ID
        ):
            cls._enqueue(
                {
                    "chat_id": config.LOGGER_CHAT_ID,
                    "text": f"<pre>{formatted}</pre>",
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                }
            )

    @classmethod
    def debug(cls, message: str, *fmt_args, **kwargs) -> None:
        if cls._should_log("DEBUG"):
            cls.log(message % fmt_args if fmt_args else message, level="DEBUG", **kwargs)

    @classmethod
    def info(cls, message: str, *fmt_args, **kwargs) -> None:
        if cls._should_log("INFO"):
            cls.log(message % fmt_args if fmt_args else message, level="INFO", **kwargs)

    @classmethod
    def warn(cls, message: str, *fmt_args, **kwargs) -> None:
        if cls._should_log("WARN"):
            cls.log(message % fmt_args if fmt_args else message, level="WARN", **kwargs)

    @classmethod
    def error(cls, message: str, *fmt_args, **kwargs) -> None:
        if cls._should_log("ERROR"):
            cls.log(message % fmt_args if fmt_args else message, level="ERROR", **kwargs)

    @classmethod
    def _enqueue(cls, payload: dict[str, Any]) -> None:
        if cls._queue is None:
            return
        try:
            cls._queue.put_nowait(payload)
        except asyncio.QueueFull:
            print("[logger] Queue full; dropping log payload.")

    @classmethod
    async def _worker_loop(cls) -> None:
        assert cls._queue is not None
        try:
            while True:
                item = await cls._queue.get()
                if item is cls._sentinel:
                    cls._queue.task_done()
                    break
                try:
                    await cls._send_to_telegram(item)
                except Exception as exc:
                    print(f"[logger] Failed to deliver log: {exc}")
                finally:
                    cls._queue.task_done()
        except asyncio.CancelledError:
            raise

    @classmethod
    async def _send_to_telegram(cls, payload: dict[str, Any]) -> None:
        if cls._session is None:
            cls._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        url = f"https://api.telegram.org/bot{config.LOGGING_BOT_TOKEN}/sendMessage"
        async with cls._session.post(url, data=payload) as response:
            if response.status != 200:
                body = await response.text()
                print(f"[logger] Telegram logging failed: {response.status} {body}")

    @classmethod
    async def flush(cls) -> None:
        if cls._queue is None:
            return
        await cls._queue.join()

    @classmethod
    async def shutdown(cls) -> None:
        if cls._queue is None:
            return
        await cls._queue.put(cls._sentinel)
        if cls._worker_task is not None:
            await cls._worker_task
        if cls._session is not None:
            await cls._session.close()
        cls._queue = None
        cls._worker_task = None
        cls._session = None


logger = Logger

__all__ = ["Logger", "logger"]
