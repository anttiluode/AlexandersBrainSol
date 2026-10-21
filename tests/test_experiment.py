import unittest
import numpy as np
try:
    import experiment as ex
except ImportError:
    ex = None

class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ex, 'experiment implementation is missing')

    def test_gate_conjunction_rejects_failed_writes_and_damage(self):
        row = dict(write_accuracy=1., closed_replacement=0., closed_retention=1., idle_retention=1., read_accuracy=1.,
                   probe_damage=0., idle_damage=0., refinement_ok=True)
        self.assertTrue(ex.verdict(row)['pass'])
        for name, value in [('write_accuracy',.9), ('closed_replacement',.1),
                            ('read_accuracy',.9), ('probe_damage',.02),
                            ('idle_damage',.02), ('refinement_ok',False)]:
            with self.subTest(name=name):
                self.assertFalse(ex.verdict(dict(row, **{name:value}))['pass'])

    def test_decoder_accepts_only_sensor_scalar_and_orders_codes(self):
        means=np.array([-.2,0,.2])
        np.testing.assert_array_equal(ex.decode(np.array([-.3,-.11,0,.11,.3]),means),[-1,-1,0,1,1])
        self.assertEqual(ex.decode(np.array([.01]),means).shape,(1,))
        with self.assertRaises(ValueError):
            ex.decode(np.array([np.nan]),means)

    def test_ordinary_memory_hold_and_gated_replacement(self):
        old=np.array([-1,-1,0,0,1,1]);new=np.array([0,1,-1,1,-1,0])
        theta=2*np.pi*old/3
        t=ex.rotor_evolve(theta,0,1.,None,0,10,.01,np.random.default_rng(1))
        np.testing.assert_array_equal(ex.rotor_label(t),old)
        t=ex.rotor_evolve(theta,.02,1.,2*np.pi*new/3,0,10,.01,np.random.default_rng(1))
        np.testing.assert_array_equal(ex.rotor_label(t),new)

    def test_summary_includes_failed_writes_and_invalid_reads(self):
        data={'gated':{'target':[1,1], 'final':[1,0], 'valid':[True,False],
                       'reads':[[1,1],[1,1]], 'probe_changed':[False,True],
                       'idle_changed':[False,False]},
              'closed':{'target':[1,1], 'final':[0,0], 'valid':[True,True], 'old':[0,0]},
              'idle':{'valid':[True,True], 'final':[0,0], 'old':[0,0]}}
        s=ex.summarize(data,True)
        self.assertEqual(s['write_accuracy'],.5)
        self.assertEqual(s['read_accuracy'],.5)
        self.assertEqual(s['probe_damage'],.5)

    def test_protocol_full_seed_requires_lock(self):
        with self.assertRaises(ValueError):
            ex.require_full_lock('development',None)

    def test_paired_brownian_refinement_sums(self):
        noise=np.arange(48.).reshape(4,2,6)
        np.testing.assert_array_equal(ex.coarsen_noise(noise),noise[::2]+noise[1::2])

    def test_closed_erasure_cannot_pass_resistance(self):
        s=dict(write_accuracy=1.,closed_replacement=0.,closed_retention=0.,
               idle_retention=1.,read_accuracy=1.,probe_damage=0.,idle_damage=0.,refinement_ok=True)
        self.assertFalse(ex.verdict(s)['pass'])

    def test_checkpoints_survive_interruption(self):
        import tempfile,json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)
            def runner(seed):
                if seed==2:raise RuntimeError('interruption')
                return dict(seed=seed,value=.3)
            with self.assertRaises(RuntimeError):
                ex.execute_seeds([1,2,3],runner,path)
            self.assertEqual(json.loads((path/'seed-1.json').read_text())['seed'],1)
            self.assertFalse((path/'seed-3.json').exists())
            self.assertTrue((path/'aborted.json').exists())

    def test_lock_rejects_untracked_source_and_stale_calibration(self):
        import tempfile,subprocess,json
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            def git(*args):
                return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL,text=True).strip()
            git('init');git('config','user.name','test');git('config','user.email','test@example.invalid')
            (root/'LICENSE').write_text('test')
            git('add','LICENSE');git('commit','-m','base')
            head=git('rev-parse','HEAD')
            for f in ex.SOURCE_FILES:
                p=root/f;p.parent.mkdir(exist_ok=True);p.write_text('{}')
            with patch.object(ex,'ROOT',root),self.assertRaises((ValueError,subprocess.CalledProcessError)):
                ex.require_full_lock('full',head)
            (root/'protocols/calibration.json').write_text(json.dumps({'source_hashes':{'ring.py':'stale'}}))
            git('add','.');git('commit','-m','source')
            head=git('rev-parse','HEAD')
            with patch.object(ex,'ROOT',root),self.assertRaisesRegex(ValueError,'stale calibration'):
                ex.require_full_lock('full',head)

    def test_parallel_checkpoints_match_serial_model_and_keep_seed_order(self):
        import tempfile,json
        from pathlib import Path
        from functools import partial
        p=json.loads((ex.ROOT/'protocols/switching.json').read_text())
        p.update(replicas=1,write_time=0,close_time=0,release_time=0,wait_time=0,
                 read_time=.05,read_count=2)
        runner=partial(ex.run_seed,p=p,means=[-.2,0,.2])
        with tempfile.TemporaryDirectory() as temp:
            rows=ex.execute_seeds([3,1],runner,Path(temp),workers=2)
            self.assertEqual(rows,[runner(3),runner(1)])
            self.assertTrue((Path(temp)/'seed-3.json').exists())
