import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from halllab.overlap import overlaps,verify_overlaps
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'docs/overlap-controls.json').read_text())
class OverlapTests(unittest.TestCase):
 def test_controls(self):
  for c in C:self.assertTrue(verify_overlaps(overlaps(c['input'])))
  a,b,c=map(lambda c:overlaps(c['input']),C[:3]);self.assertTrue(a['local_consistent']);self.assertFalse(a['satisfiable']);self.assertEqual(a['local_domains'],[[0,1]]*3);self.assertEqual(a['rejection_counts'],[4,2,2]);self.assertEqual(b['local_domains'],[[0,1],[0,1],[0,1,2]]);self.assertEqual(b['global_domains'],c['global_domains']);self.assertEqual(c['local_domains'],c['global_domains']);self.assertEqual(b['solution_count'],2)
 def test_all_three_variable_two_value_scope_networks(self):
  choices=[[],[0],[1],[0,1]];pairs=[[0,1],[1,2],[0,2]]
  for ds in itertools.product(choices,repeat=3):
   for mask in range(8):
    self.assertTrue(verify_overlaps(overlaps(dict(values=2,domains=list(ds),scopes=[s for k,s in enumerate(pairs) if mask>>k&1]))))
 def test_all_three_value_triangle_domains(self):
  domains=[[v for v in range(3) if mask>>v&1] for mask in range(8)]
  for ds in itertools.product(domains,repeat=3):self.assertTrue(verify_overlaps(overlaps(dict(values=3,domains=list(ds),scopes=[[0,1],[1,2],[0,2]]))))
 def test_seeded_and_fixedpoint_sound(self):
  rng=random.Random(4951)
  for _ in range(100):
   n=rng.randrange(7);m=rng.randrange(6);poss=[list(s) for k in range(n+1) for s in itertools.combinations(range(n),k)];rng.shuffle(poss)
   d=dict(values=m,domains=[[v for v in range(m) if rng.random()<.65] for _ in range(n)],scopes=poss[:rng.randrange(min(6,len(poss))+1)])
   r=overlaps(d);self.assertTrue(verify_overlaps(r));self.assertTrue(all(set(a)<=set(b) for a,b in zip(r['global_domains'],r['local_domains'])));self.assertEqual(overlaps(dict(d,domains=r['local_domains']))['local_domains'],r['local_domains']);self.assertLessEqual(len(r['rounds']),1+sum(map(len,d['domains'])))
 def test_checker_no_generator_calls(self):
  r=overlaps(C[1]['input'])
  with patch('halllab.overlap.overlaps',side_effect=AssertionError),patch('halllab.overlap.analyze',side_effect=AssertionError),patch('halllab.overlap.joint',side_effect=AssertionError):self.assertTrue(verify_overlaps(r))
 def test_forgery_and_terminal_round(self):
  r=overlaps(C[3]['input']);cases=[]
  t=copy.deepcopy(r);t['rounds'].pop();cases.append(t)
  t=copy.deepcopy(r);t['rounds'].append(copy.deepcopy(t['rounds'][-1]));cases.append(t)
  for k,v in [('solution_count',True),('local_consistent',1),('rejection_counts',[0,0,0]),('global_domains',r['input']['domains']),('edges',[]),('local_domains',r['input']['domains']),('schema','wrong')]:
   t=copy.deepcopy(r);t[k]=v;cases.append(t)
  for k,v in [('domains',[]),('next_domains',[]),('constraints',[])]:
   t=copy.deepcopy(r);t['rounds'][0][k]=v;cases.append(t)
  t=copy.deepcopy(r);t['rounds'][0]['constraints'][0]['edges'][0]['supported']=1;cases.append(t)
  for k in r:
   t=copy.deepcopy(r);del t[k];cases.append(t)
  t=copy.deepcopy(r);t['edges'][0]['assignment']=[0]*4;cases.append(t)
  for t in cases:
   with self.assertRaises(ValueError):verify_overlaps(t)
 def test_invalid_and_immutable(self):
  for x in [{},dict(C[0]['input'],scopes=[[False]]),dict(C[0]['input'],scopes=[[1,0]]),dict(C[0]['input'],scopes=[[0],[0]]),dict(C[0]['input'],scopes=[[3]]),dict(C[0]['input'],scopes=[[]]*7)]:
   with self.assertRaises(ValueError):overlaps(x)
  d=copy.deepcopy(C[0]['input']);r=overlaps(d);before=copy.deepcopy(r);verify_overlaps(r);self.assertEqual(before,r);self.assertEqual(d,C[0]['input'])
 def test_cli(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'overlap.json';p=subprocess.run([sys.executable,'-m','halllab.overlap','-','--output',str(out)],input=json.dumps(C[0]['input']),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(verify_overlaps(json.loads(out.read_text())))
   v=subprocess.run([sys.executable,'-m','halllab.overlap',str(out),'--verify'],capture_output=True,text=True);self.assertEqual(v.returncode,0,v.stderr);self.assertEqual(json.loads(v.stdout),dict(valid=True,schema='halllab-overlaps-v1'))
   before=out.read_bytes()
   for text in ['{}','{"values":0,"domains":[],"scopes":[],"scopes":[]}','{"values":NaN,"domains":[],"scopes":[]}',' '*65537]:
    p=subprocess.run([sys.executable,'-m','halllab.overlap','-','--output',str(out)],input=text,text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(out.read_bytes(),before)
if __name__=='__main__':unittest.main()
