# TODO consider pytest; using unittest because it's built into Python: one less dependency needed.
from typing import cast
import unittest

from buyer import Homebuyer
from match import _match_pair, _unmatch_pair, buyer_optimal_match, buyer_from_string, neighborhood_from_string, tokens_for_type
from neighborhood import Neighborhood
from vector import PearlVector
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

        fit = vector @ other_vector
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
    def setUp(self) -> None:
        self.neighborhood = cast(Neighborhood, neighborhood_from_string('N N0 E:7 W:7 R:10'))
        self.homebuyers = [cast(Homebuyer, buyer_from_string(h_string, {'N0': self.neighborhood})) for h_string in [
            'H H0 E:3 W:9 R:2 N2>N0>N1',
            'H H1 E:4 W:3 R:7 N0>N2>N1'
        ]]
        self.homebuyers.sort(key=lambda b: b.name)
    
    def test_build_neighborhood_from_string(self):
        n = self.neighborhood
        c = n.characteristics
        self.assertTrue(c.energy == 7)
        self.assertTrue(c.water == 7)
        self.assertTrue(c.resilience == 10)
        self.assertTrue(n.name == 'N0')
    
    def test_build_homebuyer_from_string(self):
        neighborhoods = [neighborhood_from_string(n_string) for n_string in [
            'N N0 E:7 W:7 R:10',
            'N N1 E:2 W:1 R:1',
            'N N2 E:7 W:6 R:4',]]
        neighborhood_dict = {n.name: n for n in neighborhoods}
        buyer = cast(Homebuyer, buyer_from_string('H H0 E:3 W:9 R:2 N2>N0>N1', neighborhood_dict))
        self.assertListEqual(buyer.prefs, [neighborhood_dict['N2'], neighborhood_dict['N0'], neighborhood_dict['N1']])
    
    def test_prefers(self):
        neighborhood = self.neighborhood
        n_dict = {'N0': neighborhood}
        # buyer 1 should have fitness 104
        buyer1 = self.homebuyers[0]
        # buyer 2 should have fitness 119
        buyer2 = self.homebuyers[1]
        self.assertTrue(neighborhood.prefers(buyer2, buyer1))
    
    def test_get_successors(self):
        neighborhood = self.neighborhood
        neighborhood.set_prefs(self.homebuyers)
        buyers = self.homebuyers[:]
        # ensure buyers come back as H0, H1; the order matters to this test
        buyers.sort(key=lambda b: b.name)
        # buyer 1 should have fitness 104
        buyer1 = buyers[0]
        # buyer 2 should have fitness 119
        buyer2 = buyers[1]
        _match_pair(buyer2, neighborhood)
        self.assertListEqual(neighborhood.matching, [buyer2])
        successors = neighborhood.get_successors()
        self.assertListEqual(successors, [buyer1])

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
        self.homebuyers.sort(key=lambda b: b.name)

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
    
    def test_buyer_optimal_matching_simple(self):
        buyer_dict = {b.name: b for b in self.homebuyers}
        buyers = [buyer_dict['H0'], buyer_dict['H1'], buyer_dict['H2']]
        b0, b1, b2 = buyers

        n0 = self.neighborhood_dict['N0']
        n1 = self.neighborhood_dict['N1']
        n2 = self.neighborhood_dict['N2']

        match_dict = buyer_optimal_match(buyers, list(self.neighborhood_dict.values()))
        self.assertListEqual(n0.matching, [b2])
        self.assertListEqual(n1.matching, [b1])
        self.assertListEqual(n2.matching, [b0])
    
    def test_buyer_optimal_matching_full(self):
        buyers = self.homebuyers[:]
        match_dict = buyer_optimal_match(buyers, list(self.neighborhood_dict.values()))
        n0_match_names = [b.name for b in match_dict[self.neighborhood_dict['N0']]]
        n1_match_names = [b.name for b in match_dict[self.neighborhood_dict['N1']]]
        n2_match_names = [b.name for b in match_dict[self.neighborhood_dict['N2']]]
        self.assertListEqual(n0_match_names, ['H5', 'H11', 'H2', 'H4'])
        self.assertListEqual(n1_match_names, ['H9', 'H8', 'H7', 'H1'])
        self.assertListEqual(n2_match_names, ['H6', 'H3', 'H10', 'H0'])


if __name__ == '__main__':
    unittest.main()
