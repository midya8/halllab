"""Bounded Regin alternating-graph certificates, separate from original reports."""
from collections import deque
from copy import deepcopy
from .core import validate, canonical, halls, force


def components(adj):
    clock = 0; stack = []; on = set(); index = {}; low = {}; groups = []
    def visit(u):
        nonlocal clock
        index[u] = low[u] = clock; clock += 1; stack.append(u); on.add(u)
        for v in adj[u]:
            if v not in index: visit(v); low[u] = min(low[u], low[v])
            elif v in on: low[u] = min(low[u], index[v])
        if low[u] == index[u]:
            group = []
            while True:
                v = stack.pop(); on.remove(v); group.append(v)
                if v == u: break
            groups.append(sorted(group))
    for u in range(len(adj)):
        if u not in index: visit(u)
    return sorted(groups, key=lambda g:g[0])


def shortest(adj, starts, target):
    queue = deque([[u] for u in starts]); seen = set(starts)
    while queue:
        path = queue.popleft()
        if path[-1] == target: return path
        for v in adj[path[-1]]:
            if v not in seen: seen.add(v); queue.append(path + [v])
    raise AssertionError('missing certificate path')


def alternating(data):
    data = validate(data); ds = data['domains']; n = len(ds); m = data['values']
    match = canonical(ds); size = sum(v is not None for v in match); sat = size == n
    free = [n+v for v in range(m) if v not in match]
    adj = [[] for _ in range(n+m)]; arcs = []
    for i,d in enumerate(ds):
        for v in d:
            a,b = (i,n+v) if match[i] == v else (n+v,i)
            arcs.append(dict(variable=i,value=v,source=a,target=b,matched=match[i]==v)); adj[a].append(b)
    for row in adj: row.sort()
    scc = components(adj)
    labels = {u:k for k,g in enumerate(scc) for u in g}
    layers = [free[:]]; seen = set(free)
    while True:
        layer = sorted({v for u in layers[-1] for v in adj[u]} - seen)
        layers.append(layer); seen.update(layer)
        if not layer: break
    dummy = [row[:] for row in adj] + [[]]
    for v in range(m):
        if v in match: dummy[n+v].append(n+m)
        else: dummy[n+m].append(n+v)
    dummy_scc = components(dummy)
    edges = []; filtered = [[] for _ in ds]
    for i,d in enumerate(ds):
        for v in d:
            reason = 'unsatisfiable' if not sat else 'base' if match[i] == v else 'cycle' if labels[i] == labels[n+v] else 'free-path' if n+v in seen else 'pruned'
            keep = reason in ('base','cycle','free-path'); walk = []; witness = None; obstruction = None
            if keep:
                filtered[i].append(v); witness = match[:]
                if reason == 'cycle': walk = [n+v] + shortest(adj,[i],n+v)
                elif reason == 'free-path': walk = shortest(adj,free,n+v) + [i,n+match[i]]
                for a,b in zip(walk,walk[1:]):
                    if a >= n and b < n: witness[b] = a-n
                assert len(set(witness)) == n and all(w in ds[j] for j,w in enumerate(witness)) and witness[i] == v
            else: obstruction = next(h for h in halls(force(ds,i,v)) if h['deficit'] > 0)
            edges.append(dict(variable=i,value=v,supported=keep,reason=reason,walk=walk,assignment=witness,obstruction=obstruction))
    return dict(schema='halllab-alternating-v1',input=data,satisfiable=sat,maximum_size=size,matching=match,
                nodes=['x'+str(i) for i in range(n)]+['v'+str(v) for v in range(m)],arcs=arcs,components=scc,
                free_values=[u-n for u in free],reach_layers=layers,dummy_components=dummy_scc,
                obstruction=None if sat else next(h for h in halls(ds) if h['deficit']>0),edges=edges,filtered=filtered)


def verify_alternating(report):
    """Independent partial-tuple/Floyd oracle. No matching, Tarjan or generator calls."""
    from itertools import product
    if type(report) is not dict or 'input' not in report: raise ValueError('invalid report')
    data = validate(report['input']); rows = data['domains']; n = len(rows); m = data['values']; N=n+m
    legal=[]
    for a in product(*(d+[None] for d in rows)):
        vals=[v for v in a if v is not None]
        if len(vals)==len(set(vals)): legal.append(a)
    size=max(sum(v is not None for v in a) for a in legal)
    matching=list(next(a for a in legal if sum(v is not None for v in a)==size))
    solutions=[a for a in legal if None not in a]; sat=bool(solutions)
    arcs=[]; links=[[] for _ in range(N)]
    for i,row in enumerate(rows):
        for v in row:
            matched=matching[i]==v; a=i if matched else n+v; b=n+v if matched else i
            arcs.append(dict(variable=i,value=v,source=a,target=b,matched=matched)); links[a].append(b)
    for row in links: row.sort()
    def classes(graph):
        length=len(graph); reach=[[i==j or j in graph[i] for j in range(length)] for i in range(length)]
        for k in range(length):
            for i in range(length):
                for j in range(length): reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
        remaining=set(range(length)); out=[]
        while remaining:
            i=min(remaining); group=[j for j in sorted(remaining) if reach[i][j] and reach[j][i]]; out.append(group); remaining.difference_update(group)
        return out
    scc=classes(links); free=[n+v for v in range(m) if v not in matching]; layers=[free]; reached=set(free)
    while True:
        add=sorted({b for a in layers[-1] for b in links[a] if b not in reached}); layers.append(add); reached.update(add)
        if not add: break
    expanded=deepcopy(links)+[[]]
    for v in range(m): expanded[n+v if v in matching else N].append(N if v in matching else n+v)
    def bfs(starts,target):
        paths=[[v] for v in starts]; visited=set(starts)
        for path in paths:
            if path[-1]==target:return path
            for nxt in links[path[-1]]:
                if nxt not in visited:visited.add(nxt);paths.append(path+[nxt])
        raise ValueError('unreachable certificate')
    def deficient(domains):
        for mask in range(1,1<<n):
            variables=[i for i in range(n) if mask>>i&1]; neighbors=sorted({v for i in variables for v in domains[i]})
            if len(neighbors)<len(variables):return dict(variables=variables,neighbors=neighbors,deficit=len(variables)-len(neighbors))
        raise ValueError('missing Hall witness')
    edges=[]; filtered=[[] for _ in rows]
    for i,row in enumerate(rows):
        for v in row:
            supported=any(a[i]==v for a in solutions)
            cycle=any(i in g and n+v in g for g in scc)
            reason='unsatisfiable' if not sat else 'base' if matching[i]==v else 'cycle' if cycle else 'free-path' if n+v in reached else 'pruned'
            walk=[]; witness=None; obstruction=None
            if supported:
                filtered[i].append(v);witness=matching[:]
                if reason=='cycle':walk=[n+v]+bfs([i],n+v)
                elif reason=='free-path':walk=bfs(free,n+v)+[i,n+matching[i]]
                for a,b in zip(walk,walk[1:]):
                    if b<n:witness[b]=a-n
                if tuple(witness) not in solutions or witness[i]!=v:raise ValueError('invalid flip')
            else:obstruction=deficient([[v] if j==i else [w for w in d if w!=v] for j,d in enumerate(rows)])
            if supported != (reason in ('base','cycle','free-path')):raise ValueError('graph disagrees with enumeration')
            edges.append(dict(variable=i,value=v,supported=supported,reason=reason,walk=walk,assignment=witness,obstruction=obstruction))
    expected=dict(schema='halllab-alternating-v1',input=data,satisfiable=sat,maximum_size=size,matching=matching,
                  nodes=['x'+str(i) for i in range(n)]+['v'+str(v) for v in range(m)],arcs=arcs,components=scc,
                  free_values=[v-n for v in free],reach_layers=layers,dummy_components=classes(expanded),
                  obstruction=None if sat else deficient(rows),edges=edges,filtered=filtered)
    def strict(a,b):
        if type(a) is not type(b):return False
        if type(a) is dict:return a.keys()==b.keys() and all(strict(a[k],b[k]) for k in a)
        if type(a) is list:return len(a)==len(b) and all(strict(x,y) for x,y in zip(a,b))
        return a==b
    if not strict(report,expected):raise ValueError('report disagrees with exhaustive/Floyd oracle')
    return True


def main():
    from .__main__ import main as cli
    return cli(alternating,verify_alternating,'halllab-alternating-v1')

if __name__ == '__main__': raise SystemExit(main())
