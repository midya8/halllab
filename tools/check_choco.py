"""Opt-in actual Choco 4.10.18 AC_REGIN propagation; not a runtime dependency."""
import hashlib,itertools,json,os,random,subprocess,tempfile,urllib.request
from pathlib import Path
from halllab.alternating import alternating,verify_alternating
ROOT=Path(__file__).resolve().parents[1]
URL='https://repo1.maven.org/maven2/org/choco-solver/choco-solver/4.10.18/choco-solver-4.10.18-jar-with-dependencies.jar'
SHA='9468194823f5344cb3639059cc1c021b1c92140dd8d41bed15275ca5a548cb19'

def cases():
 out=[c['input']for c in json.loads((ROOT/'docs/alternating-controls.json').read_text())]
 for m in range(4):
  choices=[list(s)for k in range(m+1)for s in itertools.combinations(range(m),k)]
  for n in range(4):out.extend(dict(values=m,domains=list(ds))for ds in itertools.product(choices,repeat=n))
 rng=random.Random(61943)
 for _ in range(120):
  m=rng.randrange(9);n=rng.randrange(7);out.append(dict(values=m,domains=[[v for v in range(m)if rng.random()<.65]for i in range(n)]))
 return out

def run(jar,inputs,mode='AC_REGIN'):
 raw=''.join(' '.join(map(str,[len(d['domains']),d['values']]+[x for row in d['domains']for x in [len(row)]+row]))+'\n'for d in inputs)
 p=subprocess.run(['java','-cp',str(jar),str(ROOT/'tools/HallReference.java'),mode],input=raw,text=True,capture_output=True,timeout=180,check=True)
 lines=p.stdout.splitlines();assert len(lines)==len(inputs),(len(lines),len(inputs),p.stdout,p.stderr)
 out=[]
 for line,data in zip(lines,inputs):
  if line=='U':out.append(None)
  else:
   assert line.startswith('S|'),line
   rows=line[2:].split(';')if data['domains']else []
   out.append([[int(v)for v in row.split(',')]for row in rows])
 return out

def main():
 with tempfile.TemporaryDirectory(prefix='halllab-choco-')as tmp:
  jar=Path(os.environ['CHOCO_JAR'])if os.environ.get('CHOCO_JAR')else Path(tmp)/'choco-4.10.18.jar'
  if not jar.exists():urllib.request.urlretrieve(URL,jar)
  assert hashlib.sha256(jar.read_bytes()).hexdigest()==SHA,'external artifact checksum mismatch'
  inputs=cases();expected=[alternating(d)for d in inputs]
  assert all(verify_alternating(r)for r in expected)
  actual=run(jar,inputs);counts=dict(reports=len(inputs),satisfiable=0,unsatisfiable=0,domain_values=0)
  for data,r,domains in zip(inputs,expected,actual):
   assert (domains is not None)==r['satisfiable'],(data,r,domains)
   if domains is not None:
    assert domains==r['filtered'],(data,r,domains);counts['satisfiable']+=1;counts['domain_values']+=sum(map(len,domains))
   else:counts['unsatisfiable']+=1
  bottleneck=dict(values=3,domains=[[0,1],[0,1],[0,1,2]])
  assert run(jar,[bottleneck],'FC')==[bottleneck['domains']]
  assert run(jar,[bottleneck],'NEQS')==[bottleneck['domains']]
  assert run(jar,[bottleneck],'AC_REGIN')==[[[0,1],[0,1],[2]]]
  print(json.dumps(dict(external='Choco 4.10.18 AC_REGIN actual propagation',artifact_sha256=SHA,**counts,calibration_runs=3),sort_keys=True))
if __name__=='__main__':main()
