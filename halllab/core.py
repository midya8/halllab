"""Tiny all-different supports; deterministic matching, no third-party solver."""
from itertools import product
from copy import deepcopy


def validate(data):
    if type(data) is not dict or set(data) != {'values', 'domains'}:
        raise ValueError('input needs exactly values and domains')
    m, ds = data['values'], data['domains']
    if type(m) is not int or not 0 <= m <= 8:
        raise ValueError('values must be an integer in 0..8')
    if type(ds) is not list or len(ds) > 6:
        raise ValueError('domains must be a list of at most 6 lists')
    for d in ds:
        if type(d) is not list or any(type(v) is not int or not 0 <= v < m for v in d):
            raise ValueError('domain values must be integer indices')
        if d != sorted(set(d)):
            raise ValueError('domains must be strictly increasing, no duplicates')
    return deepcopy(data)


def cardinality(ds):
    """DFS augmenting paths. Right vertices visited once per augmentation."""
    owner = {}
    def augment(i, seen):
        for v in ds[i]:
            if v in seen:
                continue
            seen.add(v)
            if v not in owner or augment(owner[v], seen):
                owner[v] = i
                return True
        return False
    return sum(augment(i, set()) for i in range(len(ds)))


def canonical(ds):
    """Lexicographically first maximum assignment; null is ordered last."""
    target = cardinality(ds)
    chosen, used, filled = [], set(), 0
    for i, d in enumerate(ds):
        for v in [v for v in d if v not in used] + [None]:
            u = used | ({v} if v is not None else set())
            k = filled + (v is not None)
            tail = [[a for a in row if a not in u] for row in ds[i+1:]]
            if k + cardinality(tail) == target:
                chosen.append(v)
                used, filled = u, k
                break
    return chosen


def halls(ds):
    bits = [sum(1 << v for v in d) for d in ds]
    out = []
    for mask in range(1, 1 << len(ds)):
        vs = [i for i in range(len(ds)) if mask >> i & 1]
        union = 0
        for i in vs:
            union |= bits[i]
        if union.bit_count() <= len(vs):
            out.append({'variables': vs, 'neighbors': [v for v in range(8) if union >> v & 1],
                        'deficit': len(vs)-union.bit_count()})
    return out


def force(ds, i, v):
    return [[v] if j == i else [a for a in d if a != v] for j, d in enumerate(ds)]


def pairwise(ds):
    rounds = [deepcopy(ds)]
    while True:
        old = rounds[-1]
        new = [[v for v in d if all(i == j or any(v != a for a in e)
                                   for j, e in enumerate(old))]
               for i, d in enumerate(old)]
        rounds.append(new)
        if new == old:
            return rounds


def count_assignments(ds):
    dp = {0: 1}
    for d in ds:
        nxt = {}
        for used, count in dp.items():
            for v in d:
                if not used >> v & 1:
                    key = used | (1 << v)
                    nxt[key] = nxt.get(key, 0) + count
        dp = nxt
    return sum(dp.values())


def analyze(data):
    data = validate(data)
    ds = data['domains']
    edges, filtered = [], [[] for _ in ds]
    for i, d in enumerate(ds):
        for v in d:
            fd = force(ds, i, v)
            supported = cardinality(fd) == len(ds)
            if supported:
                filtered[i].append(v)
            edges.append({'variable': i, 'value': v, 'supported': supported,
                          'assignment': canonical(fd) if supported else None,
                          'obstruction': None if supported else next(h for h in halls(fd) if h['deficit'] > 0)})
    matching = canonical(ds)
    size = sum(v is not None for v in matching)
    return {'schema': 'halllab-v1', 'input': data, 'satisfiable': size == len(ds),
            'maximum_size': size, 'matching': matching, 'solution_count': count_assignments(ds),
            'hall_sets': halls(ds), 'edges': edges, 'filtered': filtered, 'pairwise_rounds': pairwise(ds)}


def verify(report):
    """Independent Cartesian partial-assignment and Hall-set oracle, no matching calls."""
    if type(report) is not dict or set(report) != {'schema','input','satisfiable','maximum_size','matching','solution_count','hall_sets','edges','filtered','pairwise_rounds'}:
        raise ValueError('invalid report shape')
    data = validate(report['input']); ds = data['domains']; n = len(ds)
    partial = list(product(*(d + [None] for d in ds)))
    legal = [a for a in partial if len([v for v in a if v is not None]) == len({v for v in a if v is not None})]
    best = max(sum(v is not None for v in a) for a in legal)
    maximum = next(a for a in legal if sum(v is not None for v in a) == best)
    solutions = [a for a in legal if None not in a]
    def oracle_halls(rows):
        out=[]
        for mask in range(1,2**n):
            inds=[i for i in range(n) if mask & 2**i]
            neighbors=sorted({v for i in inds for v in rows[i]})
            if len(neighbors)<=len(inds):
                out.append(dict(variables=inds,neighbors=neighbors,deficit=len(inds)-len(neighbors)))
        return out
    edges=[]; filtered=[[] for _ in ds]
    for i,d in enumerate(ds):
        for v in d:
            ss=[a for a in solutions if a[i]==v]
            rows=[[v] if j==i else [w for w in r if w!=v] for j,r in enumerate(ds)]
            if ss: filtered[i].append(v)
            edges.append(dict(variable=i,value=v,supported=bool(ss),assignment=list(ss[0]) if ss else None,
                              obstruction=None if ss else next(h for h in oracle_halls(rows) if h['deficit']>0)))
    rounds=[deepcopy(ds)]
    while True:
        old=rounds[-1]; new=[list(d) for d in old]
        for i,d in enumerate(old):
            for v in d:
                if any(i!=j and not any(v!=w for w in e) for j,e in enumerate(old)):
                    new[i].remove(v)
        rounds.append(new)
        if new==old: break
    expected=dict(schema='halllab-v1', input=data, satisfiable=best==n, maximum_size=best, matching=list(maximum),
                  solution_count=len(solutions),hall_sets=oracle_halls(ds),edges=edges,filtered=filtered,pairwise_rounds=rounds)
    def strict(a,b):
        if type(a) is not type(b): return False
        if type(a) is dict: return set(a)==set(b) and all(strict(a[k],b[k]) for k in a)
        if type(a) is list: return len(a)==len(b) and all(strict(x,y) for x,y in zip(a,b))
        return a==b
    if not strict(report,expected): raise ValueError('report disagrees with independent exhaustive oracle')
    return True
