# HallLab

**Distinct is a global promise.** Inspect exact all-different propagation for tiny constraint-based AI assignment problems. Every retained variable/value has a complete injective assignment. Every pruned edge has a forced-residual Hall obstruction. Compare against full synchronous pairwise arc consistency, not a weakened one-pass baseline.

[Interactive inspector](https://midya8.github.io/halllab/) · [Exact method, boundaries and six-source ledger](METHOD.md)

```json
{"values":3,"domains":[[0,1],[0,1],[0,1,2]]}
```

Two variables reserve `{v0,v1}`. Pairwise disequalities leave all seven edges; global support leaves five, forcing x2 to v2. Each rejected edge explains the residual variable group with fewer available values than variables. A second control has three variables sharing two values: every binary constraint has support but no full assignment exists.

## Run and audit

```sh
python -m halllab input.json --output report.json
python -m halllab report.json --verify
python -m unittest discover -s tests -v
npm test                      # Node 22 + actual Chrome
bash tools/check_wheel.sh      # installed outside checkout, both CLI entry points
python -m http.server 8000 --directory docs
```

Or `pip install .`, then `halllab input.json`. Python 3.10+, no runtime dependencies; build requires pip/setuptools. Browser runs an independent exhaustive JavaScript engine, never an API or packaged native output.

```python
from halllab import analyze, verify
report = analyze({"values": 3, "domains": [[0, 1], [0, 1], [0, 1, 2]]})
assert report["filtered"] == [[0, 1], [0, 1], [2]]
assert verify(report)  # exhaustive independent oracle, no matching calls
```

## Visible evidence

- Maximum-cardinality matching, canonical ties and exact complete-assignment count.
- All original edges with either first full support assignment or first forced-residual deficient subset.
- Every original tight/deficient Hall subset; tight is not impossible.
- Original, pairwise fixed-point and globally supported domains; every synchronous binary-AC round.
- Original synthetic controls for hidden Hall bottlenecks, noninterval domains, surplus values, reassignment, symmetric supports, empty domain/scope, cascade and full 48-edge scope.
- Strict bounded JSON CLI, atomic output and exact report verification. Edits/invalid input clear stale browser reports.

12 native tests, including 8,777 exhaustive domain graphs and 120 seeded larger inputs; 682 full Python/JS report comparisons; Chrome replays every edge/subset/round at three widths. Fresh installed reproduction and CI span Python 3.10-3.13. [METHOD.md](METHOD.md) gives actual counts, semantics and source attribution.

## Limits before interpretation

At most six variables/eight values; one all-different relation, not a complete constraint solver. Classic matching/Hall theory, not a new AI algorithm. Native repeated DFS matching queries plus bitmask counting versus independent exhaustive native checker and JavaScript assignment recursion. No Régin SCC, Hopcroft-Karp, Choco or NetworkX implementation/integration. No scalability benchmark, learned model, real assignment deployment or whole-CSP guarantee. A full match for one constraint does not ensure a shared solution for several constraints. MIT license.

## Overlapping scopes: local is not joint

[Separate interactive scope-network inspector](https://midya8.github.io/halllab/overlaps.html) · [Exact overlap contract](OVERLAPS.md)

Every scope gets its own complete local report in every synchronous propagation round, then retained domains are intersected until fixed point. An independent full-assignment oracle checks the common relation. Inspect the locally viable but impossible two-color triangle, or a satisfiable triangle where local scopes still miss joint pruning. Every scope-only witness is mapped back to original variables, never presented as a joint solution. New API `halllab.overlap.overlaps` / `verify_overlaps` and `python -m halllab.overlap`; original v1 reports and test sources stay unchanged. Twenty native tests and six Node/Chrome tests now cover both report families. Tiny exact enumeration, not a production multi-constraint solver.

## Every conflict, every minimal removal

[Conflict and removal inspector](https://midya8.github.io/halllab/conflicts.html) · [Exact contract and seven-source ledger](CONFLICTS.md)

The overlapping network can now explain every inclusion-minimal conflicting scope set and every inclusion-minimal removal that repairs the whole network. Each conflict has full single-deletion witnesses; each removal has a common assignment and contained-conflict witnesses for every restoration. Inspect all active-scope subsets and hitting-set intersections. Minimal is not minimum: the default diamond has one size-one and four size-two minimal removals. Domains stay fixed; an empty-domain background cannot be repaired by scope removal.

Separate `halllab.conflicts` API/checker/module CLI. Both earlier report families and test sources preserved. 28 native tests, nine Node/Chrome tests, installed generation/verification for all three report families. At most 64 scope subsets and 262144 original tuples, not a scalable MUS/MCS solver or weighted optimizer.

## A spare value is not a cycle

[Alternating support inspector](https://midya8.github.io/halllab/alternating.html) · [Exact fourth report contract and eight-source ledger](ALTERNATING.md)

One variable with two values has three singleton alternating SCCs, yet both edges are supported: the spare value starts an even alternating path. Inspect the canonical maximum matching, every directed original edge, free-value BFS layers, SCC cycles, dummy-node equivalent classes and every explicit cycle/path flip into a complete assignment. Rejected edges retain forced-residual Hall obstructions. A maximum partial matching in an impossible graph never masquerades as support.

Separate `halllab.alternating` API/checker/module CLI and `halllab-alternating` console command. Native augmenting matching/Tarjan versus independent exhaustive partial tuples/Floyd and browser recursion/BFS. 36 Python and 12 Node/Chrome tests retain all previous tests; 5,058 exhaustive tiny graphs, 821 complete cross-language reports, 136 individually rejected primitive forgeries, installed-wheel atomic checks and real trusted downloads. Optional actual pinned Choco4.10.18 AC_REGIN propagation agrees over 821 cases, with FC/NEQS/AC strength calibrations. Six variables/eight values, classic theory, not a novel solver or scale claim. The original three workflows remain separate; their historical limits above describe those original implementations.
