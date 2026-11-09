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
