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
