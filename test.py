# TODO consider pytest; using unittest because it's built into Python: one less dependency needed.
from typing import cast
import unittest

from match import Homebuyer, Neighborhood, PearlVector, vector_fit, tokens_for_type, neighborhood_from_string, buyer_from_string, _match_pair, _unmatch_pair
import exceptions

class TestVectors(unittest.TestCase):
    
    def test_instantiation(self):
        vector = PearlVector(1, 2, 3)
        self.assertEqual(vector.energy, 1)
        self.assertEqual(vector.water, 2)
        self.assertEqual(vector.resilience, 3)

    def test_to_tuple(self):
        vector = PearlVector(1, 2, 3)
        vector_list = vector._to_list()
        self.assertListEqual(vector_list, [1, 2, 3])

    def test_vector_fit(self):
        vector = PearlVector(1, 2, 3)
        other_vector = PearlVector(4, 5, 6)

        fit = vector_fit(vector, other_vector)
        self.assertEqual(fit, 32)
    
class TestUtils(unittest.TestCase):
    def test_parse_error(self):
        try:
            tokens = tokens_for_type('N any other stuff here', 'H')
        except exceptions.DataParsingError as error:
            thrown = True
        self.assertTrue(thrown)
    
    def test_parse_tokens(self):
        tokens = tokens_for_type('X a>b>C>d W:10 some_name_here R:7 e:2', 'X')
        self.assertTrue(tokens != None)
        self.assertTrue('A>B>C>D' in tokens)
        self.assertTrue('SOME_NAME_HERE' in tokens)
        self.assertTrue('W:10' in tokens)
        self.assertTrue('R:7' in tokens)
        self.assertTrue('E:2' in tokens)

class TestNeighborhoods(unittest.TestCase):
    def test_build_from_string(self):
        n = neighborhood_from_string('N N1 E:10 W:1 R:5')
        c = n.characteristics
        self.assertTrue(c.energy == 10)
        self.assertTrue(c.water == 1)
        self.assertTrue(c.resilience == 5)
        self.assertTrue(n.name == 'N1')
    
    def test_prefers(self):
        neighborhood = cast(Neighborhood, neighborhood_from_string('N N0 E:7 W:7 R:10'))
        n_dict = {'N0': neighborhood}
        # buyer 1 should have fitness 104
        buyer1 = buyer_from_string('H H0 E:3 W:9 R:2 N2>N0>N1', n_dict)
        # buyer 2 should have fitness 119
        buyer2 = buyer_from_string('H H1 E:4 W:3 R:7 N0>N2>N1', n_dict)
        self.assertTrue(neighborhood.prefers(buyer2, buyer1))

class TestHomebuyers(unittest.TestCase):
    def setUp(self):
        neighborhoods = [neighborhood_from_string(n_string) for n_string in [
            'N N0 E:7 W:7 R:10',
            'N N1 E:2 W:1 R:1',
            'N N2 E:7 W:6 R:4',]]
        self.neighborhood_dict = {n.name: n for n in neighborhoods}

    def test_build_from_string(self):
        n_dict = self.neighborhood_dict
        h = cast(Homebuyer, buyer_from_string('H H0 E:3 W:9 R:2 N2>N0>N1', n_dict))
        self.assertTrue(h.name == 'H0')
        goals = h.goals
        self.assertTrue(goals.energy == 3)
        self.assertTrue(goals.water == 9)
        self.assertTrue(goals.resilience == 2)
        self.assertListEqual(h.prefs, [n_dict['N2'], n_dict['N0'], n_dict['N1'],])
        self.assertListEqual(h._original_prefs, [n_dict['N2'], n_dict['N0'], n_dict['N1'],])
        fits = h.fits
        self.assertDictEqual(fits, {'N0': 104, 'N1': 17, 'N2': 83 })

class TestMatching(unittest.TestCase):
    def setUp(self):
        neighborhoods = [cast(Neighborhood, neighborhood_from_string(n_string)) for n_string in [
            'N N0 E:7 W:7 R:10',
            'N N1 E:2 W:1 R:1',
            'N N2 E:7 W:6 R:4',]]
        self.neighborhood_dict = {n.name: n for n in neighborhoods}
        self.homebuyers = [cast(Homebuyer, buyer_from_string(h_string, self.neighborhood_dict)) for h_string in [
            'H H0 E:3 W:9 R:2 N2>N0>N1',
            'H H1 E:4 W:3 R:7 N0>N2>N1',
            'H H2 E:4 W:0 R:10 N0>N2>N1',
            'H H3 E:10 W:3 R:8 N2>N0>N1',
            'H H4 E:6 W:10 R:1 N0>N2>N1',
            'H H5 E:6 W:7 R:7 N0>N2>N1',
            'H H6 E:8 W:6 R:9 N2>N1>N0',
            'H H7 E:7 W:1 R:5 N2>N1>N0',
            'H H8 E:8 W:2 R:3 N1>N0>N2',
            'H H9 E:10 W:2 R:1 N1>N2>N0',
            'H H10 E:6 W:4 R:5 N0>N2>N1',
            'H H11 E:8 W:4 R:7 N0>N1>N2'
        ]]

    def test_add_match(self):
        neighborhood = self.neighborhood_dict['N0']
        buyer1 = self.homebuyers[0] # fitness: 104
        buyer2 = self.homebuyers[1] # fitness: 119
        buyer3 = self.homebuyers[2] # fitness: 128
        neighborhood._match(buyer1)
        neighborhood._match(buyer2)
        neighborhood._match(buyer3)
        matching = neighborhood.matching
        self.assertListEqual(matching, [buyer3, buyer2, buyer1])

    def test_match_is_unique(self):
        neighborhood = self.neighborhood_dict['N0']
        buyer1 = self.homebuyers[0] # fitness: 104
        neighborhood._match(buyer1)
        neighborhood._match(buyer1)
        self.assertListEqual(neighborhood.matching, [buyer1])
    
    def test_match_via_util(self):
        neighborhood = self.neighborhood_dict['N0']
        buyer1 = self.homebuyers[0] # fitness: 104
        _match_pair(buyer1, neighborhood)
        self.assertEqual(buyer1.matching, neighborhood)
        self.assertListEqual(neighborhood.matching, [buyer1])
    
    def test_unmatch_via_util(self):
        neighborhood = self.neighborhood_dict['N0']
        buyer1 = self.homebuyers[0] # fitness: 104
        buyer2 = self.homebuyers[1] # fitness: 119
        buyer3 = self.homebuyers[2] # fitness: 128
        _match_pair(buyer1, neighborhood)
        _match_pair(buyer2, neighborhood)
        _match_pair(buyer3, neighborhood)
        _unmatch_pair(buyer1, neighborhood)
        self.assertIsNone(buyer1.matching)
        self.assertListEqual(neighborhood.matching, [buyer3, buyer2])


if __name__ == '__main__':
    unittest.main()
