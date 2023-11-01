# TODO consider pytest; using unittest because it's built into Python: one less dependency needed.
import unittest

from match import Homebuyer, Neighborhood, PearlVector, vector_fit, tokens_for_type
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
        n = Neighborhood.from_string('N N1 E:10 W:1 R:5')
        c = n.characteristics
        self.assertTrue(c.energy == 10)
        self.assertTrue(c.water == 1)
        self.assertTrue(c.resilience == 5)
        self.assertTrue(n.name == 'N1')

class TestHomebuyers(unittest.TestCase):
    def setUp(self):
        neighborhoods = [Neighborhood.from_string(n_string) for n_string in [
            'N N0 E:7 W:7 R:10',
            'N N1 E:2 W:1 R:1',
            'N N2 E:7 W:6 R:4',]]
        self.neighborhood_dict = {n.name: n for n in neighborhoods}

    def test_build_from_string(self):
        n_dict = self.neighborhood_dict
        h = Homebuyer.from_string('H H0 E:3 W:9 R:2 N2>N0>N1', n_dict)
        self.assertTrue(h.name == 'H0')
        goals = h.goals
        self.assertTrue(goals.energy == 3)
        self.assertTrue(goals.water == 9)
        self.assertTrue(goals.resilience == 2)
        self.assertListEqual(h.preferences, [n_dict['N2'], n_dict['N0'], n_dict['N1'],])
        fits = h.fits
        self.assertDictEqual(fits, {'N0': 104, 'N1': 17, 'N2': 83 })

    
if __name__ == '__main__':
    unittest.main()
