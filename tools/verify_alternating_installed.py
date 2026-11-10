import copy,json,os,subprocess,sys,tempfile
from pathlib import Path
controls=json.loads(Path(sys.argv[1]).read_text());counts=dict(controls=0,cli_forgeries=0,direct_forgeries=0)
with tempfile.TemporaryDirectory()as tmp:
 env=dict(os.environ);env.pop('PYTHONPATH',None)
 p=subprocess.run([sys.executable,'-c','import halllab.alternating;print(halllab.alternating.__file__)'],cwd=tmp,env=env,text=True,capture_output=True,check=True);assert 'site-packages' in p.stdout,p.stdout
 for c in controls:
  outputs=[]
  for cmd in [[sys.executable,'-m','halllab.alternating'],[str(Path(sys.executable).with_name('halllab-alternating'))]]:
   p=subprocess.run(cmd+['-'],input=json.dumps(c['input']),cwd=tmp,env=env,text=True,capture_output=True,check=True);report=json.loads(p.stdout);outputs.append(report)
   result=subprocess.run(cmd+['-','--verify'],input=p.stdout,cwd=tmp,env=env,text=True,capture_output=True,check=True);assert json.loads(result.stdout)==dict(valid=True,schema='halllab-alternating-v1')
   bad=copy.deepcopy(report);bad['maximum_size']=True
   target=Path(tmp)/'out.json';target.write_text('keep')
   result=subprocess.run(cmd+['-','--verify','--output',str(target)],input=json.dumps(bad),cwd=tmp,env=env,text=True,capture_output=True);assert result.returncode==2 and target.read_text()=='keep';counts['cli_forgeries']+=1
   bad=copy.deepcopy(report);bad['reach_layers']=[]
   result=subprocess.run(cmd+['-','--verify','--output',str(target)],input=json.dumps(bad),cwd=tmp,env=env,text=True,capture_output=True);assert result.returncode==2 and target.read_text()=='keep';counts['cli_forgeries']+=1
   for bad in [bad,dict(report,maximum_size=True)]:
    script='import json,sys;from halllab.alternating import verify_alternating\ntry:verify_alternating(json.load(sys.stdin))\nexcept ValueError:sys.exit(0)\nsys.exit(3)'
    subprocess.run([sys.executable,'-c',script],input=json.dumps(bad),cwd=tmp,env=env,text=True,capture_output=True,check=True);counts['direct_forgeries']+=1
  assert outputs[0]==outputs[1];counts['controls']+=1
 print('Installed alternating: two entrypoints, sixth asserted module origin, outside checkout; '+json.dumps(counts))
