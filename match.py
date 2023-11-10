"""A game of matching home buyers to their neighborhoods.

Some portions of this have been modeled after, adapted from, or wholesale copied
from the `matching` module here: https://github.com/daffidwilde/matching. Out-of-the-box that 
module would solve a base Hospital-Resident matching game, but we need to sort potential homebuyers
by their "fit" to the neighborhoods, and while subclass-and-override might be a fine approach, it would
also require setting up `matching` and its dependency `NumPy`, and I'm trying to get this done without
falling into Dependency Hell.
"""
import argparse
import logging
import sys
from typing import Dict, List

from buyer import Homebuyer
import exceptions
from neighborhood import Neighborhood
from vector import PearlVector

logger = logging.getLogger(__name__)

def _match_pair(player, other):
    """Match the players given by `player` and `other`."""

    player._match(other)
    other._match(player)

def _unmatch_pair(buyer: Homebuyer, neighborhood: Neighborhood):
    """Unmatch a (buyer, neighborhood)-pair."""

    buyer._unmatch()
    neighborhood._unmatch(buyer)

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
    # TODO: avoid division by zero – but if there were no neighborhoods, we'd have bigger problems
    capacity = len(free_buyers) // len(neighborhoods)

    for n in neighborhoods:
        # initialize capacity and neighborhood fits for buyers
        n.capacity = capacity
        n.set_prefs(free_buyers)

    while free_buyers:
        buyer = free_buyers.pop(0)
        logger.debug("Starting with buyer " + buyer.name)
        while not buyer.matching:
            for neighborhood in buyer.prefs:
                logger.debug("\t checking neighborhood " + neighborhood.name)
                if buyer.matching:
                    logger.debug("\t buyer is matched, continuing")
                    continue
                if len(neighborhood.matching) < neighborhood.capacity:
                    logger.debug("\t it's a match!")
                    _match_pair(buyer, neighborhood)
                else:
                    worst_match = neighborhood.get_worst_match()
                    worst_fit = neighborhood.get_fitness(worst_match)
                    buyer_fit = neighborhood.get_fitness(buyer)
                    if buyer_fit > worst_fit:
                        logger.debug("\t buyer is a better fit than the worst match")
                        _unmatch_pair(worst_match, neighborhood)
                        free_buyers.append(worst_match)
                        _match_pair(buyer, neighborhood)
                    else:
                        logger.debug("\t buyer is not as good a fit, continuing to check")
    return {n: n.matching for n in neighborhoods}

def tokens_for_type(data_string: str, type_indicator: str) -> List[str]:
    # let's start by being case tolerant; we'll work in uppercase:
    tokens = data_string.upper().split(' ')
    first_token = tokens.pop(0)
    if first_token != type_indicator:
        raise exceptions.DataParsingError(data_string)
    return tokens

def read_input_file(file_name: str) -> dict:
    """Reads the file specified by file_name and returns a dictionary containing neighborhood and homebuyer dictionaries"""
    neighborhoods = {}
    homebuyers = {}
    homebuyer_lines = []
    with open(file_name) as input_file:
        for line in input_file:
            stripped = line.rstrip()
            if line[0] == 'H':
                # Homebuyer creation depends on having the neighborhoods, so save these lines and parse them last
                homebuyer_lines.append(stripped)
            elif line[0] == 'N':
                neighborhood = neighborhood_from_string(stripped)
                neighborhoods[neighborhood.name] = neighborhood
            else:
                # all other lines are ignored
                pass
    for line in homebuyer_lines:
        homebuyer = buyer_from_string(line, neighborhoods)
        homebuyers[homebuyer.name] = homebuyer
    return { 'neighborhoods': list(neighborhoods.values()), 'homebuyers': list(homebuyers.values()) }

def write_output_file(file_name: str, matches: Dict[str, List[Homebuyer]]) -> None:
    """Write the matches out to a file.
    
    Matches are presumed to be provided in a dictionary whose keys are the names of the neighborhoods
    and whose values are ordered lists of the homebuyers matched to those neighborhoods.
    """
    with open(file_name, "w") if file_name else sys.stdout as output_file:
        for key, buyers in matches.items():
            buyer_text = ' '.join([f"{buyer.name}({buyer.fits[key.name]})" for buyer in buyers])
            print(f"{key}: {buyer_text}", file=output_file)

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Match homebuyers to neighborhoods, in a buyer-optimal way')
    parser.add_argument('input_file', type=str, 
                        help='Input file with neighborhood and homebuyer defintions.')
    parser.add_argument('--output', type=str, required=False,  dest='output_file',
                        help='Name of file where output should be written (will use stdout if not specified).')
    parser.add_argument('--debug', dest='debug', action='store_const', const=True, default=False, 
                        help='If present, turns on debug logging')
    parsed_args = parser.parse_args(sys.argv[1:])

    input_file = parsed_args.input_file
    output_file = parsed_args.output_file
    if parsed_args.debug:
        logger.setLevel(logging.DEBUG)
    
    input_data = read_input_file(input_file)
    matches = buyer_optimal_match(input_data['homebuyers'], input_data['neighborhoods'])
    write_output_file(output_file, matches)