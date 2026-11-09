import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from halllab.conflicts import conflicts,verify_conflicts
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/conflict-controls.json').read_text())
class ConflictTests(unittest.TestCase):
 def audit(self,data):
  before=copy.deepcopy(data);r=conflicts(data);self.assertEqual(data,before);self.assertTrue(verify_conflicts(r))
  cores=[set(c['scopes']) for c in r['cores']];repairs=[set(c['removed']) for c in r['repairs']];m=len(data['scopes'])
  # Derive both hypergraph duals independently over every candidate set.
  sets=[{k for k in range(m) if mask>>k&1} for mask in range(1<<m)]
  for family,other in [(cores,repairs),(repairs,cores)]:
   hits=[s for s in sets if all(s&c for c in family)]
   minimal=[s for s in hits if not any(t<s for t in hits)]
   self.assertEqual({frozenset(s) for s in minimal},{frozenset(s) for s in other})
  for row in r['subsets']:
   active=set(row['scopes']);self.assertEqual(bool(row['solution_count']),not any(c<=active for c in cores))
  return r
 def test_controls_and_sizes(self):
  rs=[self.audit(c['input']) for c in CONTROLS]
  self.assertEqual([c['scopes'] for c in rs[0]['cores']],[[0,1,2],[0,3,4]])
  self.assertEqual([r['removed'] for r in rs[0]['repairs']],[[0],[1,3],[2,3],[1,4],[2,4]])
  self.assertEqual(len(rs[1]['repairs']),9);self.assertEqual([len(c['scopes']) for c in rs[2]['cores']],[3,1])
  self.assertEqual(rs[4]['cores'],[dict(scopes=[],deletions=[])]);self.assertEqual(rs[4]['repairs'],[])
  self.assertEqual(rs[6]['repairs'][0]['assignment'],[]);self.assertEqual(rs[7]['subsets'][0]['solution_count'],262144)
  self.assertEqual(len(rs[8]['subsets']),64)
 def test_exhaustive_tiny_networks(self):
  ds=[list(s) for n in range(3) for s in itertools.combinations(range(2),n)];pairs=[[0,1],[0,2],[1,2]]
  for domains in itertools.product(ds,repeat=3):
   for mask in range(8):self.audit(dict(values=2,domains=list(domains),scopes=[s for k,s in enumerate(pairs) if mask>>k&1]))
 def test_seeded_networks(self):
  rng=random.Random(1927)
  for _ in range(100):
   n=rng.randrange(1,5);v=rng.randrange(1,5);scopes=[list(s) for k in range(n+1) for s in itertools.combinations(range(n),k)]
   data=dict(values=v,domains=[[k for k in range(v) if rng.random()<.7] for _ in range(n)],scopes=rng.sample(scopes,min(rng.randrange(7),len(scopes))))
   self.audit(data)
 def test_scope_permutation(self):
  data=CONTROLS[0]['input'];original=conflicts(data)
  for perm in itertools.islice(itertools.permutations(range(5)),24):
   other=conflicts(dict(data,scopes=[data['scopes'][k] for k in perm]));self.assertTrue(verify_conflicts(other))
   for field,key in [('cores','scopes'),('repairs','removed')]:
    self.assertEqual({frozenset(perm[k] for k in q[key]) for q in other[field]},{frozenset(q[key]) for q in original[field]})
   for row in other['subsets']:
    mask=sum(1<<perm[k] for k in row['scopes']);self.assertEqual(row['solution_count'],original['subsets'][mask]['solution_count']);self.assertEqual(row['assignment'],original['subsets'][mask]['assignment'])
 def test_checker_independence(self):
  r=conflicts(CONTROLS[0]['input'])
  with patch('halllab.conflicts.conflicts',side_effect=AssertionError),patch('halllab.conflicts.subset_table',side_effect=AssertionError):self.assertTrue(verify_conflicts(r))
 def test_forged_reports(self):
  r=conflicts(CONTROLS[0]['input']);bad=[]
  for field in ['subsets','cores','repairs']:
   x=copy.deepcopy(r);x[field]=x[field][:-1];bad.append(x)
  x=copy.deepcopy(r);x['subsets'][0]['solution_count']=True;bad.append(x)
  x=copy.deepcopy(r);x['cores'][0]['deletions'][0]['assignment'][0]=99;bad.append(x)
  x=copy.deepcopy(r);x['repairs'][0]['restorations'][0]['core']=[];bad.append(x)
  x=copy.deepcopy(r);x['background_satisfiable']=1;bad.append(x)
  x=copy.deepcopy(r);x['cores'].reverse();bad.append(x)
  x=copy.deepcopy(r);x['extra']=0;bad.append(x)
  for x in bad:
   with self.assertRaises(ValueError):verify_conflicts(x)
 def test_cli_and_strict_json(self):
  cmd=[sys.executable,'-m','halllab.conflicts']
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'r.json';p.write_text('keep')
   r=subprocess.run(cmd+['-','--output',str(p)],input=json.dumps(CONTROLS[0]['input']),text=True,capture_output=True);self.assertEqual(r.returncode,0,r.stderr)
   self.assertTrue(verify_conflicts(json.loads(p.read_text())))
   r=subprocess.run(cmd+[str(p),'--verify'],text=True,capture_output=True);self.assertEqual(json.loads(r.stdout),dict(valid=True,schema='halllab-conflicts-v1'))
   for text in ['{}','{"values":0,"values":1,"domains":[],"scopes":[]}',json.dumps(CONTROLS[0]['input']).replace('"values": 2','"values": true'),' '*65537]:
    before=p.read_bytes();r=subprocess.run(cmd+['-','--output',str(p)],input=text,text=True,capture_output=True);self.assertEqual(r.returncode,2);self.assertEqual(p.read_bytes(),before)
 def test_invalid_inputs(self):
  for change in [dict(scopes=[[0],[0]]),dict(scopes=[[1,0]]),dict(scopes=[[True]]),dict(scopes=[[4]]),dict(values=True),dict(domains=[[2]])]:
   x=copy.deepcopy(CONTROLS[0]['input']);x.update(change)
   with self.assertRaises(ValueError):conflicts(x)
