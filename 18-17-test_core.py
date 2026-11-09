import copy
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from halllab import analyze,verify
from halllab.core import cardinality
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/controls.json').read_text())
class HallTests(unittest.TestCase):
    def test_controls(self):
        for c in CONTROLS: self.assertTrue(verify(analyze(c['input'])))
        r=analyze(CONTROLS[0]['input']); self.assertEqual(r['filtered'],[[0,1],[0,1],[2]])
        self.assertEqual(r['pairwise_rounds'],[r['input']['domains']]*2)
        self.assertEqual(r['solution_count'],2)
        self.assertEqual(r['edges'][4]['obstruction'],dict(variables=[0,1],neighbors=[1],deficit=1))
    def test_all_three_value_domains_up_to_four_variables(self):
        domains=[[v for v in range(3) if mask>>v&1] for mask in range(8)]
        count=0
        for n in range(5):
            for ds in itertools.product(domains,repeat=n):
                r=analyze(dict(values=3,domains=list(ds))); self.assertTrue(verify(r)); count+=1
        self.assertEqual(count,4681)
    def test_all_four_value_domains_three_variables(self):
        domains=[[v for v in range(4) if mask>>v&1] for mask in range(16)]
        for ds in itertools.product(domains,repeat=3): self.assertTrue(verify(analyze(dict(values=4,domains=list(ds)))))
    def test_seeded_larger(self):
        rng=random.Random(1927)
        for _ in range(120):
            m=rng.randrange(9);n=rng.randrange(7)
            self.assertTrue(verify(analyze(dict(values=m,domains=[[v for v in range(m) if rng.random()<.5] for _ in range(n)]))))
    def test_maximum(self):
        r=analyze(CONTROLS[-1]['input']);self.assertEqual(r['solution_count'],20160);self.assertTrue(verify(r));self.assertEqual(len(r['edges']),48)
    def test_empty_and_unsat(self):
        self.assertEqual(analyze(dict(values=0,domains=[]))['solution_count'],1)
        r=analyze(dict(values=0,domains=[[]]));self.assertFalse(r['satisfiable']);self.assertEqual(r['matching'],[None]);self.assertTrue(verify(r))
        r=analyze(CONTROLS[1]['input']);self.assertFalse(r['satisfiable']);self.assertEqual(r['maximum_size'],2);self.assertEqual(r['filtered'],[[],[],[]]);self.assertEqual(r['pairwise_rounds'][-1],[[0,1]]*3)
    def test_matching_independent_checker(self):
        r=analyze(CONTROLS[0]['input'])
        with patch('halllab.core.cardinality',side_effect=AssertionError),patch('halllab.core.analyze',side_effect=AssertionError),patch('halllab.core.halls',side_effect=AssertionError),patch('halllab.core.pairwise',side_effect=AssertionError): self.assertTrue(verify(r))
    def test_invalid_input(self):
        bad=[None,[],{},dict(values=True,domains=[]),dict(values=9,domains=[]),dict(values=1,domains=[[True]]),dict(values=2,domains=[[1,0]]),dict(values=2,domains=[[0,0]]),dict(values=1,domains=[[1]]),dict(values=0,domains=[[]]*7),dict(values=0,domains=[],extra=1)]
        for data in bad:
            with self.assertRaises(ValueError):analyze(data)
    def test_forged_report(self):
        r=analyze(CONTROLS[0]['input'])
        cases=[]
        for k in r:
            t=copy.deepcopy(r);del t[k];cases.append(t)
        for k in ['solution_count','maximum_size']:
            t=copy.deepcopy(r);t[k]=True;cases.append(t)
        for path,val in [('schema','wrong'),('satisfiable',1),('filtered',[[0,1],[0,1],[0,1,2]]),('matching',[0,0,2]),('hall_sets',[]),('edges',r['edges'][::-1]),('pairwise_rounds',[r['input']['domains']])]:
            t=copy.deepcopy(r);t[path]=val;cases.append(t)
        for k,val in [('supported',False),('assignment',[0,0,2]),('obstruction',{}),('variable',False),('value',False)]:
            t=copy.deepcopy(r);t['edges'][0][k]=val;cases.append(t)
        t=copy.deepcopy(r);t['edges'][4]['obstruction']['neighbors']=[];cases.append(t)
        t=copy.deepcopy(r);t['extra']=1;cases.append(t)
        for t in cases:
            with self.assertRaises(ValueError):verify(t)
    def test_immutability_idempotent(self):
        for c in CONTROLS:
            d=copy.deepcopy(c['input']);r=analyze(d);saved=copy.deepcopy(r);verify(r);self.assertEqual(r,saved);self.assertEqual(d,c['input'])
            self.assertEqual(analyze(dict(values=d['values'],domains=r['filtered']))['filtered'],r['filtered'])
            self.assertTrue(all(set(g)<=set(p) for g,p in zip(r['filtered'],r['pairwise_rounds'][-1])))
    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'report.json'
            p=subprocess.run([sys.executable,'-m','halllab','-','--output',str(out)],input=json.dumps(CONTROLS[0]['input']),text=True,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(verify(json.loads(out.read_text())))
            for args in [[sys.executable,'-m','halllab',str(out),'--verify']]:
                q=subprocess.run(args,text=True,capture_output=True);self.assertEqual(q.returncode,0,q.stderr);self.assertEqual(json.loads(q.stdout),dict(valid=True,schema='halllab-v1'))
            before=out.read_bytes()
            for bad in ['{"values":0,"values":0,"domains":[]}','{"values":NaN,"domains":[]}',' '*65537,'{}','{"values":1,"domains":[[true]]}']:
                q=subprocess.run([sys.executable,'-m','halllab','-','--output',str(out)],input=bad,text=True,capture_output=True)
                self.assertEqual(q.returncode,2);self.assertEqual(q.stdout,'');self.assertEqual(out.read_bytes(),before)
            q=subprocess.run([sys.executable,'-m','halllab','/missing/halllab'],capture_output=True);self.assertEqual(q.returncode,2)
    def test_greedy_failure_and_canonical_order(self):
        r=analyze(CONTROLS[2]['input']);self.assertEqual(r['matching'],[1,0]);self.assertEqual(r['maximum_size'],2)
        r=analyze(CONTROLS[3]['input']);self.assertEqual(r['matching'],[0,1]);self.assertEqual(r['edges'][1]['assignment'],[1,0])
if __name__=='__main__':unittest.main()
