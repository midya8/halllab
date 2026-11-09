import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
controls=json.loads(Path(sys.argv[1]).read_text())
with tempfile.TemporaryDirectory() as tmp:
    env=dict(os.environ);env.pop('PYTHONPATH',None)
    script='import halllab,halllab.core,halllab.__main__,json;print(json.dumps([m.__file__ for m in (halllab,halllab.core,halllab.__main__)]))'
    p=subprocess.run([sys.executable,'-c',script],cwd=tmp,env=env,capture_output=True,text=True,check=True)
    origins=json.loads(p.stdout)
    assert all('site-packages' in f for f in origins),origins
    for c in controls:
        generated=[]
        for cmd in [[sys.executable,'-m','halllab'],[str(Path(sys.executable).with_name('halllab'))]]:
            r=subprocess.run(cmd+['-'],input=json.dumps(c['input']),cwd=tmp,env=env,capture_output=True,text=True,check=True)
            obj=json.loads(r.stdout);generated.append(obj)
            v=subprocess.run(cmd+['-','--verify'],input=r.stdout,cwd=tmp,env=env,capture_output=True,text=True,check=True)
            assert json.loads(v.stdout)==dict(valid=True,schema='halllab-v1')
        assert generated[0]==generated[1]
    print('Installed: 10 controls, both CLI entry points generation/verification, three site-packages origins, outside checkout')
if len(sys.argv)>2:
    scope_controls=json.loads(Path(sys.argv[2]).read_text())
    with tempfile.TemporaryDirectory() as tmp:
        script='import halllab.overlap;print(halllab.overlap.__file__)'
        origin=subprocess.run([sys.executable,'-c',script],cwd=tmp,env=env,text=True,capture_output=True,check=True).stdout.strip()
        assert 'site-packages' in origin
        for c in scope_controls:
            cmd=[sys.executable,'-m','halllab.overlap']
            r=subprocess.run(cmd+['-'],input=json.dumps(c['input']),cwd=tmp,env=env,capture_output=True,text=True,check=True)
            v=subprocess.run(cmd+['-','--verify'],input=r.stdout,cwd=tmp,env=env,capture_output=True,text=True,check=True)
            assert json.loads(v.stdout)==dict(valid=True,schema='halllab-overlaps-v1')
        print('Installed overlaps: 9 controls through module CLI generation/verification, fourth site-packages module origin, outside checkout')

if len(sys.argv)>3:
    conflict_controls=json.loads(Path(sys.argv[3]).read_text())
    with tempfile.TemporaryDirectory() as tmp:
        script='import halllab.conflicts;print(halllab.conflicts.__file__)'
        origin=subprocess.run([sys.executable,'-c',script],cwd=tmp,env=env,text=True,capture_output=True,check=True).stdout.strip()
        assert 'site-packages' in origin
        for c in conflict_controls:
            cmd=[sys.executable,'-m','halllab.conflicts']
            r=subprocess.run(cmd+['-'],input=json.dumps(c['input']),cwd=tmp,env=env,capture_output=True,text=True,check=True)
            v=subprocess.run(cmd+['-','--verify'],input=r.stdout,cwd=tmp,env=env,capture_output=True,text=True,check=True)
            assert json.loads(v.stdout)==dict(valid=True,schema='halllab-conflicts-v1')
        print('Installed conflicts: 9 controls through module generation/verification, fifth site-packages origin, outside checkout')
