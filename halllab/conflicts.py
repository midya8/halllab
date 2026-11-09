"""Exact subset-minimal conflicts and scope-removal repairs under fixed domains."""
from itertools import product
from .overlap import validate


def subset_table(data):
    """Classify tuples once by their satisfied-scope bitmask, then aggregate supersets."""
    m=len(data['scopes']);size=1<<m
    hist=[0]*size;first=[None]*size
    rows=[[]]
    for d in data['domains']:rows=[a+[v] for a in rows for v in d]
    for a in rows:
        mask=sum(1<<k for k,s in enumerate(data['scopes']) if len({a[i] for i in s})==len(s))
        hist[mask]+=1
        if first[mask] is None:first[mask]=a
    out=[]
    for mask in range(size):
        valid=[t for t in range(size) if t&mask==mask]
        candidates=[first[t] for t in valid if first[t] is not None]
        out.append(dict(scopes=[k for k in range(m) if mask>>k&1],solution_count=sum(hist[t] for t in valid),assignment=min(candidates) if candidates else None))
    return out


def conflicts(raw):
    data=validate(raw);table=subset_table(data);m=len(data['scopes']);full=(1<<m)-1
    cores=[]
    for mask,row in enumerate(table):
        if row['solution_count']==0 and all(table[mask^(1<<k)]['solution_count']>0 for k in row['scopes']):
            cores.append(dict(scopes=row['scopes'],deletions=[dict(removed=k,scopes=table[mask^(1<<k)]['scopes'],assignment=table[mask^(1<<k)]['assignment']) for k in row['scopes']]))
    repairs=[]
    for removed in range(full+1):
        kept=full^removed;indices=[k for k in range(m) if removed>>k&1]
        if table[kept]['solution_count']>0 and all(table[kept|(1<<k)]['solution_count']==0 for k in indices):
            restorations=[]
            for k in indices:
                active=table[kept|(1<<k)]['scopes']
                core=next(c['scopes'] for c in cores if set(c['scopes'])<=set(active))
                restorations.append(dict(restored=k,scopes=active,core=core))
            repairs.append(dict(removed=indices,kept=table[kept]['scopes'],assignment=table[kept]['assignment'],restorations=restorations))
    return dict(schema='halllab-conflicts-v1',input=data,background_satisfiable=table[0]['solution_count']>0,satisfiable=table[full]['solution_count']>0,subsets=table,cores=cores,repairs=repairs)


def verify_conflicts(report):
    """Independent per-subproblem Cartesian replay and all-proper-subset minimality."""
    if type(report) is not dict or set(report)!={'schema','input','background_satisfiable','satisfiable','subsets','cores','repairs'}:raise ValueError('invalid conflict report shape')
    data=validate(report['input']);m=len(data['scopes']);universe=set(range(m));table=[]
    for mask in range(1<<m):
        chosen=[k for k in range(m) if mask>>k&1];count=0;first=None
        for a in product(*data['domains']):
            if all(all(a[i]!=a[j] for p,i in enumerate(data['scopes'][k]) for j in data['scopes'][k][p+1:]) for k in chosen):
                count+=1
                if first is None:first=list(a)
        table.append(dict(scopes=chosen,solution_count=count,assignment=first))
    sets=[set(t['scopes']) for t in table]
    minimal=[i for i,t in enumerate(table) if t['solution_count']==0 and not any(q['solution_count']==0 and sets[j]<sets[i] for j,q in enumerate(table))]
    cores=[dict(scopes=table[i]['scopes'],deletions=[dict(removed=k,scopes=sorted(sets[i]-{k}),assignment=next(t['assignment'] for j,t in enumerate(table) if sets[j]==sets[i]-{k})) for k in table[i]['scopes']]) for i in minimal]
    repairs=[]
    for indices in [t['scopes'] for t in table]:
        rem=set(indices);keep=universe-rem
        row=next(t for j,t in enumerate(table) if sets[j]==keep)
        if not row['solution_count']:continue
        if any(t['solution_count'] and rem>(universe-sets[j]) for j,t in enumerate(table)):continue
        restores=[]
        for k in indices:
            active=keep|{k};core=next(table[i]['scopes'] for i in minimal if sets[i]<=active)
            restores.append(dict(restored=k,scopes=sorted(active),core=core))
        repairs.append(dict(removed=indices,kept=sorted(keep),assignment=row['assignment'],restorations=restores))
    expected=dict(schema='halllab-conflicts-v1',input=data,background_satisfiable=bool(table[0]['solution_count']),satisfiable=bool(table[-1]['solution_count']),subsets=table,cores=cores,repairs=repairs)
    def strict(a,b):
        if type(a) is not type(b):return False
        if type(a) is dict:return set(a)==set(b) and all(strict(a[k],b[k]) for k in a)
        if type(a) is list:return len(a)==len(b) and all(strict(x,y) for x,y in zip(a,b))
        return a==b
    if not strict(report,expected):raise ValueError('conflict report disagrees with independent subset replay')
    return True


if __name__=='__main__':
    from .__main__ import main
    raise SystemExit(main(generator=conflicts,checker=verify_conflicts,schema='halllab-conflicts-v1'))
