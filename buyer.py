from typing import List, Type

from base import BasePlayer
from neighborhood import Neighborhood
from vector import PearlVector

class Homebuyer(BasePlayer):
    def __init__(self, name: str, goals: Type[PearlVector], preferences: List[Neighborhood]) -> None:
        super().__init__(name, vector=goals)
        self.goals = goals
        self.matching = None
        self.set_prefs(preferences)
        self.fits = {n.name: self.goals @ n.characteristics for n in preferences}
    
    def _match(self, other):
        self.matching = other

    def _unmatch(self):
        self.matching = None
    
    def get_favorite(self) -> Neighborhood:
        return self.prefs[0]

    def get_successors(self):
        """Get all the successors to the current match of the buyer."""

        idx = self.prefs.index(self.matching)
        return self.prefs[idx + 1 :]