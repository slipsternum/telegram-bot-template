from telebot.states import State, StatesGroup


class UserStates(StatesGroup):
    """Conversation states for your bot."""

    idle = State()
    # Add your custom states here


__all__ = ["UserStates"]
