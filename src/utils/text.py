from __future__ import annotations


class WelcomeText:
    @staticmethod
    def greeting(user: object | None) -> str:
        first_name = getattr(user, "first_name", None) or "there"
        return (
            f"Hey {first_name}! Welcome to your Telegram bot.\n\n"
            "Use /help to see available commands."
        )

    @staticmethod
    def cancelled() -> str:
        return "Cancelled."


class HelpText:
    @staticmethod
    def help_message() -> str:
        return (
            "Available commands:\n"
            "- /start: show the welcome message\n"
            "- /ping: check bot health\n"
            "- /help: show this help message\n"
            "- /cancel: cancel the current operation\n\n"
            "Admin commands:\n"
            "- /stats: show bot metrics\n"
            "- /loglevel: change log level (DEBUG|INFO|WARN|ERROR)"
        )


class AdminText:
    @staticmethod
    def stats_message() -> str:
        return "Bot stats:\n(Add your metrics here)"

    @staticmethod
    def log_level_usage() -> str:
        return "Usage: /loglevel DEBUG|INFO|WARN|ERROR"

    @staticmethod
    def log_level_changed(level: str) -> str:
        return f"Log level changed to {level}."
