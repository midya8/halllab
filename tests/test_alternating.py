import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from halllab.alternating import alternating,verify_alternating
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/alternating-controls.json').read_text())
class AlternatingTests(unittest.TestCase):
 def audit(self,data):
  before=copy.deepcopy(data);r=alternating(data);self.assertEqual(data,before);self.assertTrue(verify_alternating(r));n=len(data['domains'])
  for e in r['edges']:
   self.assertEqual(e['supported'],r['satisfiable'] and (r['matching'][e['variable']]==e['value'] or any(e['variable'] in g and n+e['value'] in g for g in r['dummy_components'])))
   walk=e['walk']
   if walk:
    self.assertEqual(len(walk)%2,1);self.assertEqual(len(walk)-1,len(set(walk))) if e['reason']=='cycle' else self.assertEqual(len(walk),len(set(walk)))
    for k,(u,v) in enumerate(zip(walk,walk[1:])):
     arc=next(a for a in r['arcs'] if a['source']==u and a['target']==v);self.assertEqual(arc['matched'],bool(k%2))
    if e['reason']=='cycle':self.assertEqual(walk[0],walk[-1])
    else:self.assertIn(walk[0]-n,r['free_values']);self.assertGreaterEqual(walk[-1],n);self.assertIn(walk[-1]-n,r['matching']);self.assertEqual(len(walk),len(set(walk)))
  return r
 def test_controls(self):
  rs=[self.audit(c['input'])for c in CONTROLS]
  self.assertEqual([e['reason']for e in rs[0]['edges']],['base','free-path']);self.assertEqual(rs[0]['components'],[[0],[1],[2]]);self.assertEqual(rs[0]['edges'][1]['assignment'],[1]);self.assertEqual(rs[0]['edges'][1]['walk'],[2,0,1])
  self.assertEqual(rs[1]['filtered'],[[0,1],[0,1],[2]]);self.assertEqual(rs[4]['maximum_size'],2);self.assertFalse(any(e['supported']for e in rs[4]['edges']));self.assertEqual(rs[8]['matching'],[]);self.assertTrue(rs[9]['satisfiable']);self.assertEqual(len(rs[-1]['edges']),48)
 def test_exhaustive_domain_graphs(self):
  count=0
  for m in range(4):
   domains=[list(s)for k in range(m+1)for s in itertools.combinations(range(m),k)]
   for n in range(5):
    for ds in itertools.product(domains,repeat=n):self.audit(dict(values=m,domains=list(ds)));count+=1
  self.assertEqual(count,5058)
 def test_seeded_full_bounds(self):
  rng=random.Random(61943)
  for _ in range(120):
   m=rng.randrange(9);n=rng.randrange(7);self.audit(dict(values=m,domains=[[v for v in range(m)if rng.random()<.65]for i in range(n)]))
 def test_all_primitive_forgeries(self):
  r=alternating(CONTROLS[3]['input']);paths=[]
  def leaves(x,p=()):
   if type(x)is dict:
    for k,v in x.items():
     if p==()and k=='input':continue
     leaves(v,p+(k,))
   elif type(x)is list:
    for k,v in enumerate(x):leaves(v,p+(k,))
   else:paths.append((p,x))
  leaves(r)
  for path,value in paths:
   bad=copy.deepcopy(r);node=bad
   for k in path[:-1]:node=node[k]
   node[path[-1]]=not value if type(value)is bool else value+1 if type(value)is int else value+'!' if type(value)is str else False
   with self.assertRaises(ValueError,msg=str(path)):verify_alternating(bad)
  print('alternating primitive forgeries rejected',len(paths))
 def test_structure_type_and_order(self):
  r=alternating(CONTROLS[1]['input']);bad=[]
  for field in ['nodes','arcs','components','reach_layers','dummy_components','edges','filtered']:
   x=copy.deepcopy(r);x[field]=x[field][:-1];bad.append(x)
  x=copy.deepcopy(r);x['maximum_size']=True;bad.append(x)
  x=copy.deepcopy(r);x['edges'].reverse();bad.append(x)
  x=copy.deepcopy(r);x['extra']=0;bad.append(x)
  x=copy.deepcopy(r);del x['obstruction'];bad.append(x)
  for x in bad:
   with self.assertRaises(ValueError):verify_alternating(x)
 def test_checker_independence(self):
  r=alternating(CONTROLS[3]['input'])
  with patch('halllab.alternating.alternating',side_effect=AssertionError),patch('halllab.alternating.components',side_effect=AssertionError),patch('halllab.alternating.shortest',side_effect=AssertionError),patch('halllab.alternating.canonical',side_effect=AssertionError),patch('halllab.alternating.halls',side_effect=AssertionError),patch('halllab.alternating.force',side_effect=AssertionError):self.assertTrue(verify_alternating(r))
 def test_invalid_inputs(self):
  for data in [None,[],{},dict(values=True,domains=[]),dict(values=9,domains=[]),dict(values=2,domains=[[1,0]]),dict(values=2,domains=[[0,0]]),dict(values=1,domains=[[True]]),dict(values=0,domains=[[0]]),dict(values=1,domains=[[]]*7)]:
   with self.assertRaises(ValueError):alternating(data)
 def test_cli_and_atomic_failures(self):
  cmd=[sys.executable,'-m','halllab.alternating']
  with tempfile.TemporaryDirectory()as t:
   p=Path(t)/'r.json';p.write_text('keep')
   for c in CONTROLS:
    a=subprocess.run(cmd+['-','--output',str(p)],input=json.dumps(c['input']),text=True,capture_output=True);self.assertEqual(a.returncode,0,a.stderr);self.assertTrue(verify_alternating(json.loads(p.read_text())))
    a=subprocess.run(cmd+[str(p),'--verify'],text=True,capture_output=True);self.assertEqual(a.returncode,0,a.stderr);self.assertEqual(json.loads(a.stdout),dict(valid=True,schema='halllab-alternating-v1'))
   for text in ['{}','{"values":1,"values":2,"domains":[]}','{"values":NaN,"domains":[]}','{"values":1.0,"domains":[]}',' '*65537]:
    before=p.read_bytes();a=subprocess.run(cmd+['-','--output',str(p)],input=text,text=True,capture_output=True);self.assertEqual(a.returncode,2);self.assertEqual(p.read_bytes(),before)
   r=alternating(CONTROLS[3]['input']);r['edges'][1]['walk']=[]
   p.write_text('keep');a=subprocess.run(cmd+['-','--verify','--output',str(p)],input=json.dumps(r),text=True,capture_output=True);self.assertEqual(a.returncode,2);self.assertEqual(p.read_text(),'keep')
