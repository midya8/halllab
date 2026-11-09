"""Overlapping finite all-different scopes; local propagation is not joint support."""
from copy import deepcopy
from itertools import product
from .core import validate as base_validate, analyze, verify


def validate(data):
    if type(data) is not dict or set(data) != {'values','domains','scopes'}:
        raise ValueError('input needs exactly values, domains and scopes')
    base_validate({k:data[k] for k in ['values','domains']})
    scopes=data['scopes'];n=len(data['domains'])
    if type(scopes) is not list or len(scopes)>6:
        raise ValueError('scopes must be a list of at most 6 lists')
    for scope in scopes:
        if type(scope) is not list or any(type(i) is not int or not 0<=i<n for i in scope) or scope != sorted(set(scope)):
            raise ValueError('scopes must be strictly increasing variable indices')
    if len({tuple(s) for s in scopes}) != len(scopes):
        raise ValueError('duplicate scopes')
    return deepcopy(data)


def joint(data):
    """Iterative partial-tuple expansion, reject at the first violated input scope."""
    ds,scopes=data['domains'],data['scopes']
    tuples=[[]]
    for d in ds:
        tuples=[a+[v] for a in tuples for v in d]
    count=0;bins=[0]*len(scopes);support=[[None for _ in d] for d in ds]
    for a in tuples:
        bad=next((k for k,s in enumerate(scopes) if len({a[i] for i in s})!=len(s)),None)
        if bad is not None:
            bins[bad]+=1;continue
        count+=1
        for i,v in enumerate(a):
            k=ds[i].index(v)
            if support[i][k] is None:support[i][k]=a
    return count,bins,support


def overlaps(raw):
    data=validate(raw);ds=deepcopy(data['domains']);rounds=[]
    while True:
        local=[analyze(dict(values=data['values'],domains=[ds[i] for i in s])) for s in data['scopes']]
        nxt=[list(d) for d in ds]
        for s,r in zip(data['scopes'],local):
            for j,i in enumerate(s):nxt[i]=[v for v in nxt[i] if v in r['filtered'][j]]
        rounds.append(dict(domains=ds,constraints=local,next_domains=nxt))
        if nxt==ds:break
        ds=nxt
    count,bins,support=joint(data)
    edges=[];glob=[[] for _ in ds]
    for i,d in enumerate(data['domains']):
        for k,v in enumerate(d):
            a=support[i][k]
            if a is not None:glob[i].append(v)
            edges.append(dict(variable=i,value=v,local=v in ds[i],supported=a is not None,assignment=a))
    return dict(schema='halllab-overlaps-v1',input=data,rounds=rounds,local_domains=ds,
                local_consistent=all(ds) and all(r['satisfiable'] for r in rounds[-1]['constraints']),
                satisfiable=count>0,solution_count=count,rejection_counts=bins,global_domains=glob,edges=edges)


def verify_overlaps(report):
    """Replay each old certificate, independently enumerate all joint tuples and rounds."""
    keys={'schema','input','rounds','local_domains','local_consistent','satisfiable','solution_count','rejection_counts','global_domains','edges'}
    if type(report) is not dict or set(report)!=keys:raise ValueError('invalid overlap report shape')
    data=validate(report['input']);ds=deepcopy(data['domains']);scopes=data['scopes']
    rounds=[];stable=False
    if type(report['rounds']) is not list or not report['rounds'] or len(report['rounds'])>50:raise ValueError('invalid propagation rounds')
    for record in report['rounds']:
        if type(record) is not dict or set(record)!={'domains','constraints','next_domains'}:raise ValueError('invalid round shape')
        if type(record['constraints']) is not list or len(record['constraints'])!=len(scopes):raise ValueError('invalid constraints')
        keep=[set(d) for d in ds]
        for s,r in zip(scopes,record['constraints']):
            verify(r)
            if r['input']!=dict(values=data['values'],domains=[ds[i] for i in s]):raise ValueError('wrong local input')
            # Independent local tuple supports rather than the generated filtered domains.
            rows=[ds[i] for i in s]
            tuples=[a for a in product(*rows) if len(set(a))==len(a)]
            for j,i in enumerate(s):keep[i]&={a[j] for a in tuples}
        nxt=[[v for v in d if v in keep[i]] for i,d in enumerate(ds)]
        rounds.append(dict(domains=ds,constraints=record['constraints'],next_domains=nxt))
        if nxt==ds:
            stable=True;break
        ds=nxt
    if not stable:raise ValueError('missing fixed-point round')
    if rounds[-1]['next_domains']!=ds:raise ValueError('missing fixed-point round')
    count=0;bins=[0]*len(scopes);supports={};glob=[set() for _ in ds]
    for a in product(*data['domains']):
        bad=None
        for k,s in enumerate(scopes):
            if any(a[i]==a[j] for ii,i in enumerate(s) for j in s[ii+1:]):bad=k;break
        if bad is not None:bins[bad]+=1
        else:
            count+=1
            for i,v in enumerate(a):glob[i].add(v);supports.setdefault((i,v),list(a))
    edges=[dict(variable=i,value=v,local=v in ds[i],supported=(i,v) in supports,assignment=supports.get((i,v))) for i,d in enumerate(data['domains']) for v in d]
    expected=dict(schema='halllab-overlaps-v1',input=data,rounds=rounds,local_domains=ds,
                  local_consistent=all(ds) and all(r['satisfiable'] for r in rounds[-1]['constraints']),
                  satisfiable=count>0,solution_count=count,rejection_counts=bins,
                  global_domains=[[v for v in d if v in glob[i]] for i,d in enumerate(data['domains'])],edges=edges)
    def strict(a,b):
        if type(a) is not type(b):return False
        if type(a) is dict:return set(a)==set(b) and all(strict(a[k],b[k]) for k in a)
        if type(a) is list:return len(a)==len(b) and all(strict(x,y) for x,y in zip(a,b))
        return a==b
    if not strict(report,expected):raise ValueError('overlap report disagrees with independent enumeration')
    return True

if __name__=='__main__':
    from .__main__ import main
    raise SystemExit(main(generator=overlaps,checker=verify_overlaps,schema='halllab-overlaps-v1'))
