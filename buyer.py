from typing import Dict, List, Type

from base import BasePlayer
from neighborhood import Neighborhood
from util import tokens_for_type
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

def buyer_from_string(h_string: str, neighborhoods: Dict[str, Neighborhood]) -> object:
    tokens = tokens_for_type(h_string, 'H')

    name_token = None
    goal_tokens = []
    preference_string = None

    for token in tokens:
        # tokens with a ':' represent goal ratings:
        if ':' in token:
            goal_tokens.append(token)
        # and there should be one and only one string with '>' indicating neighborhood prefs
        elif '>' in token:
            preference_string = token
        # and any other string must be the name
        else:
            name_token = token

    goal_vector = PearlVector.from_tokens(goal_tokens)
    preference_keys = preference_string.split('>')
    preference_list = [neighborhoods[key] for key in preference_keys if key in neighborhoods.keys()]
    return Homebuyer(name=name_token, goals=goal_vector, preferences=preference_list)
