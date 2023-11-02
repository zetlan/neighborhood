from typing import Dict, List
import sys

import exceptions
from buyer import Homebuyer, buyer_from_string
from neighborhood import neighborhood_from_string

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
