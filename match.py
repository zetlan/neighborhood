"""A game of matching home buyers to their neighborhoods.

Some portions of this have been modeled after, adapted from, or wholesale copied
from the `matching` module here: https://github.com/daffidwilde/matching. Out-of-the-box that 
module would solve a base Hospital-Resident matching game, but we need to sort potential homebuyers
by their "fit" to the neighborhoods, and while subclass-and-override would be a fine approach, it would
also require setting up `matching` and its dependency `NumPy`, and I'm trying to get this done without
falling into Dependency Hell.
"""

from functools import reduce
import operator
from typing import Type, List, Dict

from base import BasePlayer
import exceptions

class PearlVector:
    def __init__(self, energy, water, resilience) -> None:
        self.energy = energy
        self.water = water
        self.resilience = resilience
    
    def _to_list(self):
        return [self.energy, self.water, self.resilience]
    
    def __matmul__(self, other):
        self_list = self._to_list()
        other_list = other._to_list()
        return reduce(operator.add, [s * o for s, o in zip(self_list, other_list)], 0)

    @staticmethod
    def from_tokens(tokens: List[str]) -> object:
        values = {}
        for token in tokens:
            key, value = token.split(':')
            values[key] = float(value)
        return PearlVector(energy=values['E'], water=values['W'], resilience=values['R'])

class Neighborhood(BasePlayer):
    def __init__(self, name: str, characteristics: Type[PearlVector]) -> None:
        super().__init__(name=name)
        self.capacity = 0
        self.characteristics = characteristics
    
    def prefers(self, buyer, other):
        """Determines whether the Neighborhood is a better fit for one buyer or another"""
        buyer_fit = buyer.get_fitness(self)
        other_fit = other.get_fitness(self)
        return buyer_fit > other_fit
    
    def get_worst_match(self):
        return self.matching[-1]
    
    def get_successors(self):
        """Get the successors to the neighborhoods's worst current match."""

        idx = self.prefs.index(self.get_worst_match())
        return self.prefs[idx + 1 :]

    def _match(self, other: BasePlayer):
        """Make a match between this Neighborhood and some player.
        
        This needs to add a player to the current prefs list, but put that list in order by fitness."""
        if other in self.matching:
            return self.matching
        
        self.matching.append(other)
        self.matching.sort(key=lambda player: player.get_fitness(self), reverse=True)


class Homebuyer(BasePlayer):
    def __init__(self, name: str, goals: Type[PearlVector], preferences: List[Neighborhood]) -> None:
        super().__init__(name)
        self.goals = goals
        self.set_prefs(preferences)
        self.matching = {}
        self.fits = {n.name: self.goals @ n.characteristics for n in preferences}
    
    def get_fitness(self, neighborhood: Neighborhood):
        if neighborhood.name in self.fits.keys():
            return self.fits[neighborhood.name]
        else:
            fitness = self.goals @ neighborhood.characteristics
            self.fits[neighborhood.name] = fitness
            return fitness

    def get_favorite(self) -> Neighborhood:
        return self.prefs[0]

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


def tokens_for_type(data_string: str, type_indicator: str):
    # let's start by being case tolerant; we'll work in uppercase:
    tokens = data_string.upper().split(' ')
    first_token = tokens.pop(0)
    if first_token != type_indicator:
        raise exceptions.DataParsingError(data_string)
    return tokens
    
def vector_fit(vector: Type[PearlVector], other_vector: Type[PearlVector]):
    return vector @ other_vector

def _delete_pair(player, other):
    """Make a player forget another (and vice versa), deleting the pair from
    further consideration in the game."""

    player._forget(other)
    other._forget(player)


def _match_pair(player, other):
    """Match the players given by `player` and `other`."""

    player._match(other)
    other._match(player)


def buyer_optimal_match(buyers: List[Homebuyer], neighborhoods: List[Neighborhood]):
    """
    Solve a matching 'game' using an adapted Gale-Shapley algorithm in which residents rank their preferences
    for neighborhoods, and neighborhood preferences are based on 'fit' of residents who prefer them to that neighborhood.

    This was shamelessly sto-- uh, borrowed, from the `matching` package. Gale & Shapley proved that there are two solutions
    to the stable matching problem in which members of two separate populations rank their preferences for each other;
    the algorithm can produce a match that is optimal for one population or the other. Here we use a buyer-optimal match,
    which should produce an arrangement of homebuyers in neighborhoods such that no homebuyer would be a better fit for a 
    neighborhood they'd prefer more than the one they're in.

    https://github.com/daffidwilde/matching/blob/main/src/matching/algorithms/hospital_resident.py"""

    # operate on a copy of the residents list, not the original
    free_buyers = buyers[:]

    # we could assume that neighborhoods have varying capacities, but our prompt simplifies this to simply 
    # distributing residents equally among neighborhoods, and further lets us assume an even division of 
    # homebuyers (that is, we expect the number of homebuyers modulo the number of neighborhoods is zero).
    # 
    # TODO: check this assumption
    # TODO: avoid division by zero
    capacity = len(free_buyers) // len(neighborhoods)
    for n in neighborhoods:
        # yes, this is a side effect, but it's for a good cause
        n.capacity = capacity

    while free_buyers:
        buyer = free_buyers.pop()
        neighborhood = buyer.get_favorite()

        if len(neighborhood.matching) == neighborhood.capacity:
            worst = neighborhood.get_worst_match()
            _unmatch_pair(worst, neighborhood)
            free_buyers.append(worst)

        _match_pair(buyer, neighborhood)

        if len(neighborhood.matching) == neighborhood.capacity:
            successors = neighborhood.get_successors()
            for successor in successors:
                _delete_pair(neighborhood, successor)
                if not successor.prefs and successor in free_buyers:
                    free_buyers.remove(successor)

    return {n: n.matching for n in neighborhoods}

def read_input_file(file_name: str) -> dict:
    """Reads the file specified by file_name and returns a dictionary containing neighborhood and homebuyer dictionaries"""
    neighborhoods = {}
    homebuyers = {}
    homebuyer_lines = []
    with open(file_name) as input_file:
        for line in input_file:
            if line[0] == 'H':
                # Homebuyer creation depends on having the neighborhoods, so save these lines and parse them last
                homebuyer_lines.append(line)
            elif line[0] == 'N':
                neighborhood = neighborhood_from_string(line)
                neighborhoods[neighborhood.name] = neighborhood
            else:
                # all other lines are ignored
                pass
    for line in homebuyer_lines:
        homebuyer  = buyer_from_string(line, neighborhoods)
        homebuyers[homebuyer.name] = homebuyer
    return { 'neighborhoods': neighborhoods, 'homebuyers': homebuyers }

def write_output_file(file_name: str, matches: Dict[str, List[Homebuyer]]) -> None:
    """Write the matches out to a file.
    
    Matches are presumed to be provided in a dictionary whose keys are the names of the neighborhoods
    and whose values are ordered lists of the homebuyers matched to those neighborhoods.
    """
    with open(file_name, "w") as output_file:
        for key, buyers in matches.items():
            buyer_text = ' '.join([f"{buyer.name}({buyer.fits[key]})" for buyer in buyers])
            print(f"{key}: {buyer_text}", file=output_file)