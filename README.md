# neighborhood
Solve a permutation of the stable matching problem for Homebuyers and Neighborhoods.

## Requirements

This was developed on macOS 13.6 using the system Python: v3.8.2. It makes use of the following modules:
* abc
* argparse
* functools
* logging
* operator
* sys
* typing
* unittest

all of which should be part of the core Python library.

No claims are made about backwards/forwards compatibility.

I've made no effort to profile the code in terms of memory or CPU requirements. The matching algorithm was based on Gale-Shapley, which is itself O(n<sup>2</sup>), and it would be reasonable to expect similar if slightly worse performance here.

## Execution

```shell
# get some helpful instructions:
python3 match.py -h

# read parameters from test_input.txt and execute a match, 
# writing results to test_output.txt
python3 match.py test_input.txt --output=test_output.txt

# Run the unit tests:
python3 test.py
```


## Assumptions
I made a few assumptions in writing this code
1. it would be fine to borrow code for the matching algorithm; if everyone had to write everything from scratch nothing would ever get done
1. No homeowner will leave any neighborhood unranked in their preferences
1. We're only concerned with "fit" values as integers (we could be more fine-grained using floats)
1. We're always going to get valid data (this is, in practice, a hugely optimistic assumption)
1. No homeowner will specify a neighborhood that doesn't exist
