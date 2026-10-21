import unittest
import numpy as np
try:
    import audit
except ImportError:
    audit=None

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(audit,'audit implementation missing')

    def test_recursive_numeric_tolerance_and_integer_exactness(self):
        original={'x':[1.0,2.0],'seed':901,'good':True}
        audit.compare(original,dict(original,x=[1.+1e-11,2.]),1e-8,1e-10)
        with self.assertRaises(AssertionError):
            audit.compare(original,dict(original,seed=902),1e-8,1e-10)
        with self.assertRaises(AssertionError):
            audit.compare(original,dict(original,x=[1.1,2.]),1e-8,1e-10)

    def test_missing_extra_and_nonfinite_values_rejected(self):
        for other in [{}, {'a':[1,2]}, {'a':[1],'b':2}, {'a':[float('nan')]}]:
            with self.subTest(other=other), self.assertRaises(AssertionError):
                audit.compare({'a':[1.]},other,1e-8,1e-10)
