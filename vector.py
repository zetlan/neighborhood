from functools import reduce
import operator
from typing import List

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
            # using int here for conformity with the brief, but it could be float to accommodate finer-grained ratings
            values[key] = int(value)
        return PearlVector(energy=values['E'], water=values['W'], resilience=values['R'])