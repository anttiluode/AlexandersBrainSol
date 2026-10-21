import unittest
import numpy as np
import ring
import experiment as ex
try:
    import array_backend as fast
except ImportError:
    fast=None

class BackendTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(fast,'array backend missing')

    def test_same_rng_trajectory_and_monitored_outputs(self):
        for temperature in [.005,.4]:
            z=ring.initial_state(np.array([-1,0,1]),64,.5)
            mu=np.ones(z.shape);mu[0,:6]=-4
            a=np.array([-.1,.0,.1])[:,None]
            def monitor():return dict(reference=np.array([-1,0,1]),changed=np.zeros(3,bool),minimum_amplitude=np.ones(3))
            m=monitor();f=monitor()
            left=ring.evolve(z,mu,a,temperature,2.,.0025,.5,np.random.default_rng(87),m)
            right=fast.evolve(z,mu,a,temperature,2.,.0025,.5,np.random.default_rng(87),f)
            np.testing.assert_allclose(left,right,rtol=1e-10,atol=1e-11)
            np.testing.assert_array_equal(m['changed'],f['changed'])
            np.testing.assert_allclose(m['minimum_amplitude'],f['minimum_amplitude'],rtol=1e-10,atol=1e-11)

    def test_noise_supplied_and_large_phase_jumps_match_monitor(self):
        z=ring.initial_state(np.array([1]),64,.5)
        increments=np.zeros((2,1,64),complex)
        increments[0,0]=ring.initial_state(np.array([-1]),64,.5)[0]-z[0]
        def monitor():return dict(reference=np.array([1]),changed=np.array([False]),minimum_amplitude=np.array([1.]))
        a=monitor();b=monitor()
        x=ring.evolve(z,np.ones(64),0,0,.005,.0025,.5,np.random.default_rng(1),a,increments)
        y=fast.evolve(z,np.ones(64),0,0,.005,.0025,.5,np.random.default_rng(1),b,increments)
        np.testing.assert_allclose(x,y,atol=1e-12)
        np.testing.assert_array_equal(a['changed'],b['changed'])
        self.assertTrue(b['changed'][0])

    def test_local_read_matches_original_sensor_and_noise(self):
        import json
        p=json.loads((ex.ROOT/'protocols/switching.json').read_text())
        z=ring.initial_state(np.array([-1,0,1]),64,.5)
        args=(z,p,np.random.default_rng(7),np.random.default_rng(8),[-.2,0,.2])
        x=ex.read_ring(*args,count=1)
        args=(z,p,np.random.default_rng(7),np.random.default_rng(8),[-.2,0,.2])
        y=fast.read_ring(*args,count=1)
        np.testing.assert_allclose(x[0],y[0],rtol=1e-10,atol=1e-11)
        np.testing.assert_array_equal(x[1],y[1])
        np.testing.assert_allclose(x[2],y[2],rtol=1e-10,atol=1e-11)
        np.testing.assert_array_equal(x[3]['changed'],y[3]['changed'])

    def test_already_wrong_reference_is_detected_on_first_step(self):
        z=ring.initial_state(np.array([1]),64,.5)
        a=dict(reference=np.array([0]),changed=np.array([False]),minimum_amplitude=np.ones(1))
        fast.evolve(z,np.ones(64),0,0,.0025,.0025,.5,np.random.default_rng(3),a)
        self.assertTrue(a['changed'][0])

    def test_rotor_matches_reference_euler_and_seed(self):
        self.assertTrue(hasattr(fast,'rotor_evolve'),'compiled rotor missing')
        theta=np.array([[-2.,0.,2.]])
        barrier=np.array([[.02,1.,1.]])
        target=np.array([[1.]])
        x=theta.copy();rng=np.random.default_rng(11)
        for _ in range(400):
            drift=-3*barrier*np.sin(3*x)+np.sin(target-x)
            x+=.0025*drift+np.sqrt(2*.005*.0025)*rng.normal(size=x.shape)
        bad=np.zeros(theta.shape,bool)
        y=fast.rotor_evolve(theta,barrier,target,1.,.005,1.,.0025,np.random.default_rng(11),np.array([[-1,0,1]]),bad)
        np.testing.assert_allclose(x,y,rtol=1e-10,atol=1e-11)

    def test_transient_winding_change_remains_damage_after_return(self):
        start=ring.initial_state(np.array([1]),64,.5)
        alternate=ring.initial_state(np.array([-1]),64,.5)
        dt=.0025
        def drift(z):return ring.laplacian(z,0,.5)+(1-np.abs(z)**2)*z
        noise=np.stack([alternate-start-dt*drift(start),start-alternate-dt*drift(alternate)])
        m=dict(reference=np.array([1]),changed=np.array([False]),minimum_amplitude=np.ones(1))
        final=fast.evolve(start,np.ones(64),0,0,2*dt,dt,.5,np.random.default_rng(1),m,noise)
        np.testing.assert_allclose(final,start,atol=1e-12)
        self.assertTrue(m['changed'][0])
