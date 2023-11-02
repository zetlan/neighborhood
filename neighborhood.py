from typing import List

from base import BasePlayer
from util import tokens_for_type
from vector import PearlVector

class Neighborhood(BasePlayer):
    def __init__(self, name: str, characteristics: PearlVector) -> None:
        super().__init__(name=name, vector=characteristics)
        self.capacity = 0
        self.characteristics = characteristics
    
    def _unmatch(self, other):
        self.matching = [b for b in self.matching if b != other]
    
    def prefers(self, buyer: BasePlayer, other: BasePlayer):
        """Determines whether the Neighborhood is a better fit for one buyer or another"""
        buyer_fit = buyer.get_fitness(self)
        other_fit = other.get_fitness(self)
        return buyer_fit > other_fit

    def get_favorite(self):
        """Get the neighborhood's favourite buyer outside their matching.

        If no such buyer exists, return ``None``.
        """

        for player in self.prefs:
            if player not in self.matching:
                return player

        return None

    def get_worst_match(self):
        return self.matching[-1]
    
    def get_successors(self):
        """Get the successors to the neighborhoods's worst current match."""

        worst_match = self.get_worst_match()
        if worst_match in self.prefs:
            idx = self.prefs.index(self.get_worst_match())
            return self.prefs[idx + 1 :]
        else:
            return self.prefs

    def _match(self, other: BasePlayer):
        """Make a match between this Neighborhood and some player.
        
        This needs to add a player to the current prefs list, but put that list in order by fitness."""
        if other in self.matching:
            return self.matching
        
        self.matching.append(other)
        self.matching.sort(key=lambda player: player.get_fitness(self), reverse=True)
    
    def set_prefs(self, buyers: List[BasePlayer]):
        """Set the neighborhood's preferences to be a list of buyers."""

        self.prefs = buyers
        self.prefs.sort(key=lambda buyer: self.get_fitness(buyer), reverse=True)
        self._pref_names = [player.name for player in self.prefs]

        if self._original_prefs is None:
            self._original_prefs = self.prefs[:]

def neighborhood_from_string(n_string: str) -> Neighborhood:
    tokens = tokens_for_type(n_string, 'N')

    name_token = None
    score_tokens = []

    for token in tokens:
        # tokens with a ':' represent goal ratings:
        if ':' in token:
            score_tokens.append(token)
        # any other string must be the name
        else:
            name_token = token

    characteristic_vector = PearlVector.from_tokens(score_tokens)
    return Neighborhood(name=name_token, characteristics=characteristic_vector)
