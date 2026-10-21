import unittest
import numpy as np
try:
    import addressed_updates as au
except ImportError:
    au=None

class AddressTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(au,'addressed updates missing')

    def test_requests_cover_permutations_and_return_to_first_cell(self):
        old,addresses,values,expected=au.requests()
        self.assertEqual(len({tuple(v) for v in old}),6)
        np.testing.assert_array_equal(addresses[:,0],addresses[:,-1])
        for h in range(6):
            state=old[h].copy()
            for e in range(4):
                a=addresses[h,e]
                self.assertNotEqual(values[h,e],state[a])
                state[a]=values[h,e]
                np.testing.assert_array_equal(state,expected[h,e])

    def test_blank_delay_can_move_trace_but_not_snap_latch(self):
        state=np.zeros((1,3))
        cue=np.array([[[2.,0.,0.]]])
        delay=np.array([[[0.,0.,10.],[0.,0.,10.]]])
        after,trace,snap=au.select(state,cue,delay,.5)
        self.assertEqual(trace[0],2)
        self.assertEqual(snap[0],0)
        self.assertEqual(after.shape,(1,3))

    def test_gate_masks_and_broadcast_command(self):
        opened=au.gate_mask('trace',np.array([1,2]),np.array([0,0]),np.array([2,1]))
        np.testing.assert_array_equal(opened,[[False,True,False],[False,False,True]])
        np.testing.assert_array_equal(au.gate_mask('closed',np.array([1]),np.array([0]),np.array([2])),[[False]*3])

    def test_operational_gate_rejects_bystander_damage_and_wrong_routes(self):
        s=dict(routing=1.,writes=1.,bystander_survival=1.,whole_array=1.,voted_read=1.,read_survival=1.)
        self.assertTrue(au.operational(s,True)['pass'])
        for k in s:
            self.assertFalse(au.operational(dict(s,**{k:0.}),True)['pass'])
        self.assertFalse(au.operational(s,False)['pass'])

    def test_probe_repair_cannot_turn_failed_write_into_success(self):
        self.assertTrue(hasattr(au,'write_success'),'separate pre-read writer score missing')
        before_read=np.array([[0,-1,1]]);valid=np.ones((1,3),bool)
        self.assertFalse(au.write_success(before_read,valid,np.array([0]),np.array([1]))[0])

    def test_analog_advantage_rejects_more_read_damage(self):
        import json
        p=json.loads((au.ROOT/'protocols/addressed_updates.json').read_text())
        s={a:dict.fromkeys(au.METRICS,1.) for a in au.ARMS}
        s['snap']['whole_array']=.5;s['trace']['read_survival']=0.
        result=au.aggregate([dict(summaries=s)],{'pass':True},p)
        self.assertFalse(result['analog_benefit']['pass'])

    def test_auditor_and_backend_are_source_bound(self):
        self.assertIn('audit.py',au.SOURCE_FILES)
        self.assertIn('array_backend.py',au.SOURCE_FILES)

    def test_shared_auditor_tampering_is_rejected(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import addressed_audit
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in au.SOURCE_FILES:
                p=root/name;p.parent.mkdir(exist_ok=True);p.write_text('original')
            with patch.object(au,'ROOT',root):
                manifest={'hashes':au.hashes()}
                (root/'audit.py').write_text('tampered comparator')
                with self.assertRaisesRegex(ValueError,'implementation differs'):
                    addressed_audit.verify(manifest)

    def test_cumulative_errors_remain_in_later_whole_array_score(self):
        events=[]
        for success in [False,False,True,False]:
            row={k:[True,True] for k in au.METRICS};row['whole_array']=[success,False]
            events.append(row)
        self.assertEqual(au.summaries(events)['whole_array'],1/8)
