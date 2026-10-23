import unittest
import numpy as np
from maze_evolution.information_flow_m30 import make_sources,make_panel,recurrence,geometry,EQUATIONS
from maze_evolution.foundation_study import read_compressed as readz
from maze_evolution.foundation_calibration import ROOT
from maze_evolution.deep_campaign_data import cases_from_manifest
from maze_evolution.connected_trace import respond
from maze_evolution.connected_evaluation import organism
from maze_evolution.state_isolation_runtime import writer
from maze_evolution.exposure_selection import record
from maze_evolution.evaluator import Oracle

class InformationFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=make_sources();old=readz(ROOT/'results/state_interference_m29/cases.json.gz')
        cls.o=next(iter(cases_from_manifest(old['mazes']).values()));cls.m=cls.o.maze

    def test_recurrence_against_all_writers_on_arbitrary_states(self):
        rng=np.random.default_rng(3030)
        for role,i in self.sources['focal'].items():
            model=self.sources['models'][i]
            for k in range(4):
                state=np.zeros((10,len(self.m.cells)),np.uint16) if k==0 else np.full((10,len(self.m.cells)),65535,np.uint16) if k==1 else rng.integers(0,65536,size=(10,len(self.m.cells)),dtype=np.uint16)
                state[:,np.frombuffer(self.m.cells,np.uint8)==0]=0
                formula=recurrence(role,self.m,state)
                for ch in range(10):
                    value,_,_=writer(model,self.m,state,ch)
                    self.assertTrue(np.array_equal(value,formula[ch]),(role,k,ch))

    def test_all_native_completed_ticks_and_fields(self):
        for role,i in self.sources['focal'].items():
            model=self.sources['models'][i];r,h,_=respond(model,self.m)
            org=organism(model);native=org.react(self.m.cells,self.m.w,self.m.h,self.m.start,self.m.goal)
            self.assertEqual(record(r,self.o),record(native,self.o))
            for t in range(len(h)-1):self.assertTrue(np.array_equal(recurrence(role,self.m,h[t]),h[t+1]))

    def test_gate_swap_reverses_correct_arm(self):
        for n in (13,17,21):
            for gy in (5,n-6):
                a,info=geometry(n,gy,'A');b,_=geometry(n,gy,'B');oa,ob=Oracle.build(a),Oracle.build(b);j=info['junction']
                self.assertIn(j-1,oa.path);self.assertNotIn(j+1,oa.path)
                self.assertIn(j+1,ob.path);self.assertNotIn(j-1,ob.path)
                self.assertEqual(len(oa.path),len(ob.path));self.assertEqual(sum(a.cells),sum(b.cells))
                self.assertFalse(Oracle.build(geometry(n,gy,'neither')[0]).path)

    def test_full_corpus_is_fixed_and_locally_indistinguishable(self):
        d=make_panel();self.assertEqual(len(d['queries']['new']),288);self.assertEqual(len(d['contrasts']),144)
        self.assertEqual(len(d['queries']['all']),len(set(d['queries']['all'])))
        cases=cases_from_manifest(d['mazes'])
        for c in d['contrasts']:
            self.assertGreaterEqual(c['minimum_manhattan_to_observers'],3)
            a,b=[cases[c[k]].maze for k in ('a','b')]
            for p in c['observers']:
                self.assertEqual(a.cells[p],b.cells[p])
                for q in (p-1,p+1,p-a.w,p+a.w):self.assertEqual(a.cells[q],b.cells[q])
        self.assertEqual(d,make_panel())

    def test_nonvacuous_C6_to_C2_intervention(self):
        state=np.zeros((10,len(self.m.cells)),np.uint16);p=self.m.goal
        # Goal is not source. Force a positive C1/C4 context, C0=0.
        state[1,p]=state[4,p]=1
        for role,i in self.sources['focal'].items():
            before=recurrence(role,self.m,state);changed=state.copy();changed[6,p]=1;after=recurrence(role,self.m,changed)
            self.assertEqual(int(before[2,p]),0);self.assertEqual(int(after[2,p]),1)
            v,_,_=writer(self.sources['models'][i],self.m,changed,2);self.assertTrue(np.array_equal(v,after[2]))

    def test_directional_C6_and_saturation(self):
        n=5;from maze_evolution.evaluator import Maze
        m=Maze(bytes([1]*25),5,5,0,24);x=np.zeros((10,25),np.uint16);x[3]=np.arange(25,dtype=np.uint16)
        self.assertEqual(int(recurrence('donor',m,x)[6,12]),11)
        self.assertEqual(int(recurrence('recipient',m,x)[6,12]),7)
        x[0]=x[1]=1
        self.assertEqual(int(recurrence('recipient',m,x)[6,12]),13)
        x[7]=65535;x[0]=65535;x[5]=65535
        y=recurrence('recipient',m,x);self.assertEqual(int(y[0,12]),65535);self.assertEqual(int(y[7,12]),65535)

    def test_contrast_intervention_branch_is_nonvacuous(self):
        from unittest.mock import patch
        from maze_evolution import information_flow_m30 as study
        role='recipient';identity=self.sources['focal'][role];p=self.m.goal
        state=np.zeros((10,len(self.m.cells)),np.uint16);state[1,p]=state[4,p]=1
        other=state.copy();other[6,p]=1
        a=np.stack((state,recurrence(role,self.m,state)));b=np.stack((other,recurrence(role,self.m,other)))
        obs=[p]+[int(q) for q in np.flatnonzero(np.frombuffer(self.m.cells,np.uint8)) if q!=p][:3]
        row=dict(status='quiescent',steps=1,optimal=False,no_path=False)
        c=dict(id='fixture',kind='route_swap',a='a',b='b',observers=obs,minimum_manhattan_to_observers=3)
        context=dict(sources=self.sources,data=dict(contrasts=[c],metadata={k:dict(junction=obs[0]) for k in ('a','b')}),cases={'a':self.o,'b':self.o})
        def ref(i,cid):return dict(row=row),(a if cid=='a' else b)
        with patch.object(study,'_worker',context),patch.object(study,'reference',ref):
            result,_=study.evaluate(dict(id='fixture',phase='contrast',model=identity,role=role,contrast='fixture',case='a'))
        self.assertEqual(result['executions'],11)
        self.assertIn(6,result['intervention'][0]['single_channel_exact_partner_restorations'])
        self.assertTrue(result['intervention'][0]['full_common_state_restores'])

if __name__=='__main__':unittest.main()
