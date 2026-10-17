"""Domain errors exposed by the JSON adapters and CLI."""


class ReembolsoError(Exception):
    """Base error with a message safe to display to the CLI user."""


class InputDataError(ReembolsoError):
    """The expense, policy, or exchange-rate input is invalid."""
