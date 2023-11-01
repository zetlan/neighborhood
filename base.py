import warnings
import abc

class BasePlayer:
    """An abstract base class to represent a player within a matching game.

    Parameters
    ----------
    name : object
        An identifier. This should be unique and descriptive.

    Attributes
    ----------
    prefs : List[BasePlayer]
        The player's preferences. Defaults to ``None`` and is updated using the
        ``set_prefs`` method.
    matching : Optional[BasePlayer]
        The current match of the player. ``None`` if not currently matched.
    _pref_names : Optional[List]
        A list of the names in ``prefs``. Updates with ``prefs`` via
        ``set_prefs`` method.
    _original_prefs : Optional[List[BasePlayer]]
        The original set of player preferences. Defaults to ``None`` and does
        not update after the first ``set_prefs`` method call.
    """

    def __init__(self, name):
        self.name = name
        self.prefs = []
        self.matching = None

        self._pref_names = []
        self._original_prefs = None

    def __repr__(self):
        return str(self.name)

    def _forget(self, other):
        """Forget another player by removing them from the player's preference
        list."""

        self.prefs = [p for p in self.prefs if p != other]

    def unmatched_message(self):
        """Message to say the player is not matched."""

        return f"{self} is unmatched."

    def not_in_preferences_message(self, other):
        """Message to say another player is an unacceptable match."""

        return (
            f"{self} is matched to {other} but they do not appear in their "
            f"preference list: {self.prefs}."
        )

    def set_prefs(self, players):
        """Set the player's preferences to be a list of players."""

        self.prefs = players
        self._pref_names = [player.name for player in players]

        if self._original_prefs is None:
            self._original_prefs = players[:]

    def prefers(self, player, other):
        """Determines whether the player prefers a player over some other
        player."""

        prefs = self._original_prefs
        return prefs.index(player) < prefs.index(other)

    @abc.abstractmethod
    def _match(self, other):
        """Placeholder for matching the player to another."""

    @abc.abstractmethod
    def _unmatch(self, other):
        """Placeholder for unmatching the player from another."""

    @abc.abstractmethod
    def get_favourite(self):
        """Placeholder for getting the player's favourite player."""

    @abc.abstractmethod
    def get_successors(self):
        """Placeholder for getting the successors of a match."""

    @abc.abstractmethod
    def check_if_match_is_unacceptable(self):
        """Placeholder for checking player's match is acceptable."""
