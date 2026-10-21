import unittest
import numpy as np
try:
    import ring
except ImportError:
    ring = None

class RingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ring, 'ring implementation is missing')

    def test_winding_and_alias_rejection(self):
        for n in (-2, -1, 0, 1, 2):
            z = ring.initial_state(np.array([n]), 64, .5)
            w, valid = ring.winding(z)
            self.assertEqual(w[0], n)
            self.assertTrue(valid[0])
        z[0, 5] = 0
        self.assertFalse(ring.winding(z)[1][0])
        z = np.exp(1j * np.pi * np.arange(64))[None, :]
        self.assertFalse(ring.winding(z)[1][0])

    def test_covariant_plane_wave(self):
        z = ring.initial_state(np.array([1]), 64, .5)
        a = 2*np.pi/64
        lap = ring.laplacian(z, a, .5)
        np.testing.assert_allclose(lap, 0, atol=1e-13)

    def test_energy_descends(self):
        rng = np.random.default_rng(9)
        z = ring.initial_state(np.array([-1, 0, 1]), 64, .5)
        z += .1*(rng.normal(size=z.shape)+1j*rng.normal(size=z.shape))
        e = ring.energy(z, np.ones(64), 0, .5)
        z2 = ring.evolve(z, np.ones(64), 0, 0, 2, .02, .5, rng)
        self.assertTrue(np.all(ring.energy(z2, np.ones(64), 0, .5) < e))

    def test_hold_preserves_integer_and_seed_reproduces(self):
        z = ring.initial_state(np.array([-1,0,1]), 64, .5)
        a = ring.evolve(z, np.ones(64), 0, .01, 10, .02, .5, np.random.default_rng(8))
        b = ring.evolve(z, np.ones(64), 0, .01, 10, .02, .5, np.random.default_rng(8))
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(ring.winding(a)[0], [-1,0,1])
        np.testing.assert_array_equal(z, ring.initial_state(np.array([-1,0,1]),64,.5))

    def test_reader_gauge_invariant_and_signed(self):
        z = ring.initial_state(np.array([-1,0,1]), 64, .5)
        current = ring.current(z, 32, .5)
        np.testing.assert_allclose(current, ring.current(z*np.exp(.73j),32,.5),atol=1e-14)
        self.assertTrue(current[0] < current[1] < current[2])

    def test_bad_steps_rejected(self):
        with self.assertRaises(ValueError):
            ring.evolve(np.ones((1,64),complex),np.ones(64),0,0,1,.5,.5,np.random.default_rng(1))

    def test_sensor_is_covariant_energy_current(self):
        z = ring.initial_state(np.array([1]), 64, .5)
        a=.1;eps=1e-6;bond=32
        link=np.zeros(64);link[bond]=a
        plus=link.copy();plus[bond]+=eps
        minus=link.copy();minus[bond]-=eps
        expected=-(ring.energy(z,np.ones(64),plus,.5)-ring.energy(z,np.ones(64),minus,.5))/(2*eps)
        np.testing.assert_allclose(ring.current(z,bond,.5,a),expected,atol=1e-8)
        phase=np.linspace(-.2,.2,64)
        transformed=z*np.exp(1j*phase)
        np.testing.assert_allclose(ring.current(transformed,bond,.5,a+phase[bond+1]-phase[bond]),expected,atol=1e-8)
