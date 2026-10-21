import unittest
import numpy as np
import report

class ReadControlTests(unittest.TestCase):
    def test_quantized_vote_uses_only_symbols_and_abstains_without_majority(self):
        self.assertTrue(hasattr(report,'vote_five'),'quantized control missing')
        labels=np.array([[-1,-1,0,-1,1],[-1,-1,0,0,1],[1,1,0,1,0]])
        np.testing.assert_array_equal(report.vote_five(labels),[[-1],[2],[1]])
