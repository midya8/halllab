# Alternating support: a spare value is not a cycle

HallLab 0.4 adds a separate finite all-different inspector. The original matching/Hall, overlapping-scope and conflict/removal APIs, schemas and test sources remain unchanged.

## The distinction

```json
{"values":2,"domains":[[0,1]]}
```

The canonical full matching is x0=v0. The original directed graph has three singleton SCCs. Nevertheless x0=v1 is supported: start at free value v1, follow unmatched v1→x0 and matched x0→v0, then flip both edges. The new full matching assigns x0=v1. SCC-only filtering on this original graph would incorrectly remove a valid edge.

A different control has three variables sharing two values. A maximum partial matching has size two; its matched edges still have no full-assignment support. Feasibility precedes the alternating support rule. Empty scope has one empty full matching, even with no supplied values. Empty domain is impossible. Unused supplied values remain visible isolated free vertices.

## Exact contract

Input remains exactly `{"values":m,"domains":[...]}`, m an integer 0..8, at most six ordered variables, each domain a strictly increasing unique list of integer value indices 0..m-1. Booleans, floats, duplicates, extra keys and out-of-range values rejected. CLI raw input is capped at 65,536 bytes; report verification at 8 MiB, duplicate JSON keys/nonfinite numbers rejected, generation/verification errors preserve an existing output file. The separate browser parser also rejects duplicate keys, decimal/exponent number syntax and >65,536 UTF-8 bytes before validation. The old browser parser is not changed.

New API `halllab.alternating.alternating` / `verify_alternating`, schema `halllab-alternating-v1`; module CLI `python -m halllab.alternating` and console `halllab-alternating`. No runtime dependencies. Native generator reuses the existing validated input, lexicographically first maximum matching (null ordered last), and forced-residual Hall-subset enumeration. It does not repeatedly force and re-match every edge for filtering.

Nodes are ordered x0..x(n-1), v0..v(m-1), with integer IDs variable i, value n+v. Every original domain edge produces one arc: matched x→v, unmatched v→x. Arc list follows variable/domain order. Adjacency lists sort target IDs. Native recursive Tarjan partitions all original vertices, including isolated vertices; each group sorts members and groups sort by first member.

`reach_layers[0]` contains every free value ID, sorted. Following layers contain all newly reached IDs from the previous layer only, sorted. A final empty frontier is included, even for an empty initial frontier. Matched edges cannot become a full support unless maximum size equals n.

For every original edge the priority of reasons is:

1. `unsatisfiable` if no full matching exists; no assignment or walk.
2. `base` if matched in the full canonical matching; its full assignment, empty walk.
3. `cycle` if its endpoints share an original SCC; prepend its unmatched value→variable arc to the shortest BFS variable-to-value return path.
4. `free-path` if its value endpoint is reachable from a free value; shortest multi-source BFS path to that value, then the edge to its variable and that variable's matched edge.
5. `pruned` otherwise; no assignment or walk.

BFS initializes roots sorted, processes a FIFO frontier and sorted adjacency, and keeps the first discovery. Walks are canonical for this implementation, not mathematically unique. Cycle walks repeat only their initial endpoint at the end. Free paths are simple and have even edge length. In a full matching each visited variable has its matched value successor; if the path had already included the selected variable, its final unmatched edge would complete an alternating cycle, selected by the earlier reason. Flip inserts unmatched edges and removes matched edges. The complete output assignment is checked injective, inside original domains and containing the selected edge. All supported edges carry that full assignment, not just a graph-theory label.

Every rejected original edge includes the first forced-residual Hall-deficient variable subset in ascending nonempty bitmask order, with sorted neighbors and positive deficit. Force xi=v by setting its domain to [v] and removing v from every other variable. This is separate from the original infeasible problem's first Hall obstruction. Tight Hall subsets alone do not prove impossibility.

`dummy_components` independently exposes the standard equivalent graph: add t=n+m, every matched value→t and t→every free value, preserving original arcs. After feasibility an unmatched edge survives iff both endpoints share an expanded SCC. This graph is a cross-check, not the generator's primary criterion. t is not a real variable, value or original edge.

## Independence and evidence

- Generator: augmenting DFS maximum matching plus existing canonical tie routine, Tarjan SCC, synchronous free-root reach layers and BFS certificates.
- Checker: enumerates every injective partial tuple with null last, obtains canonical maximum and full assignments without a matching routine, builds its own arcs, computes SCC equivalence through Floyd closure and separately checks support against all full assignments. All generator, Tarjan, matching, path and Hall helper calls are patched to raise in the independence test. It reconstructs the canonical certificate fields and checks strict primitive types, exact keys, arrays and order. Shared schema/theory/canonical path semantics remain shared, not an independent proof of the theorem.
- Browser: independent partial-assignment recursion, BFS from every vertex for mutual reach classes, graph paths and explicit flipped assignments. No native output injected, no API or solver service.
- 5,058 exhaustive input graphs: m=0..3 and n=0..4, including empty domains. 120 seeded bound-wide graphs with seed 61943, plus 12 original controls.
- 821 complete native/checker/browser reports: 689 exhaustive m=0..3,n=0..3 graphs, 120 deterministic JavaScript seeded graphs (LCG seed61943), 12 controls. JavaScript and Python use different seeded samplers; these seeded sets are not misrepresented as the same inputs. 3,983 arcs, 3,972 original SCCs, 2,158 reach layers, 1,112 base reasons, 712 cycle reasons, 351 free-path reasons, 402 pruned reasons and 1,406 unsatisfiable-edge reasons; 4,098 flip steps.
- 136 individual noninput primitive-leaf mutations rejected in a complete long-path report. Structure, type, key, array-order and truncation mutations tested separately.
- 36 Python tests across four workflows, retaining all original 28; 12 Node/actual-Chrome tests, retaining all original nine.
- Fresh installed wheel outside checkout: original ten single-relation, nine overlap and nine conflict controls retained; 12 alternating controls through both new entrypoints, sixth asserted site-packages module origin, 48 atomic CLI and 48 direct checker forgery rejections.
- Actual Chrome at 1280/390/320: 36 complete reports, 285 selected edges, 588 exact flip steps, 120 reach-layer selections, 141 original SCC selections and 285 exact arc rows. Twelve trusted mouse-triggered completed downloads read back from disk and pass native checker. No anchor/Blob interception. Invalid edits clear stale reports and disable download. Narrow-screen tables and graph scroll to their rightmost columns without page overflow.
- 44 full unmasked screenshots: 36 default control/width states, two narrow rightmost-scroll states, five selected certificate states and invalid input. Visual inspection is a separate release gate, not inferred from screenshot creation or DOM assertions.

The first new local browser test had a malformed quoted CSS selector in a test expression. It failed before completion; replacing the expression with a direct line-attribute filter fixed the test harness. All subsequent complete suites pass. Native generation was not changed to evade it. An actual pixel review also caught inherited horizontal scroll across controls; the new run now resets only its own scroll containers, and complete browser suites were rerun.

## Actual Choco propagation reference

Opt-in `PYTHONPATH=. python tools/check_choco.py` requires Java11+ and network access, not Maven. It downloads Choco **4.10.18**, deliberately pinned and not claimed latest, into a temporary directory, verifies SHA256 `9468194823f5344cb3639059cc1c021b1c92140dd8d41bed15275ca5a548cb19`, then executes original Java adapter source in Java source-file mode. No third-party solver code or jar is redistributed. Optional `CHOCO_JAR` must match the same hash. CI's separate external job uses Java17.

For each case it constructs enumerated `IntVar` domains, posts `allDifferent(vars,"AC_REGIN")` and calls actual `getSolver().propagate()`. Exact satisfiability and, on feasible cases, every retained domain value agree over 821 cases: 406 feasible, 415 infeasible, 1,992 retained values. This set uses 689 exhaustive graphs, 120 Python seed61943 inputs and 12 controls. Choco's internal canonical matching/SCC order/path choices are not compared or claimed equivalent.

Empty domains cannot be constructed as Choco IntVars: the adapter posts an actual false background constraint and placeholder fixed variable so actual propagation must signal contradiction. The empty scope posts a true constraint, not a zero-length Choco allDifferent. These adapters preserve relation semantics, not solver support for a constructor it rejects. Supplied unused values need no Choco variables. On contradiction no partially pruned domains are compared to all-empty global support.

Calibration executes three additional actual propagations on the bottleneck: FC retains all seven edges; NEQS retains all seven after its solver propagation queue reaches fixed point; AC_REGIN keeps five, forcing x2=v2. No weakened single-pass pairwise baseline. This evidence checks global propagation, not our canonical report trace, parser, download handling, Hall-witness tie-breaking or UI.

## Inspected source ledger and contradictions

Sources inspected November10 2026 before implementation. Research papers, official docs/source and community implementation provide distinct source types. No novel attribution.

1. Régin, *A filtering algorithm for constraints of difference in CSPs*, AAAI1994, primary: http://cse.unl.edu/~choueiry/Documents/ReginAAAI-1994.pdf . Proposition1/algorithm2 give matched x→v, unmatched v→x; retain matching, even free-root paths and alternating cycles. Mirror https://webusers.i3s.unice.fr/~regin/Cpl/format/sample.pdf is not counted as independent. High confidence.
2. van Hoeve, *The alldifferent Constraint: A Survey*, May8 2001: https://arxiv.org/pdf/cs/0105015 . Matching theory section corroborates alternating cycle OR even path beginning at free vertex. Maximum versus maximal distinguished. High confidence.
3. Gent et al., *The AllDifferent Constraint: Exploiting Strongly-Connected Components and Other Efficiency Measures*: https://www.dcs.gla.ac.uk/~pat/cpM/papers/allDiff/alldiff-paper.pdf . Section2.2.2 gives original-orientation dummy edges matchedv→t,t→freev. Performance claims there concern its actual production implementations, not this educational inspector. High confidence.
4. INGInious MOOC AllDifferent exercise: https://inginious.org/course/mooc-cp/part5-programming . Four steps use matchedv→x, unmatchedx→v,freev→dummy,dummy→matchedv, the complete reversal of our graph. Reversing every arc preserves SCCs; mixing only some orientations does not. High confidence for teaching semantics, not an output oracle.
5. OpenSourc.es, *Constraint Solver Part4: AllDifferent*, community2019: https://opensourc.es/blog/constraint-solver-alldifferent/ . Its SCC-only explanation explicitly targets balanced Sudoku and defers free-vertex treatment. Applied to arbitrary surplus domains it is incomplete; do not average away that scope limitation. Medium confidence, restricted use.
6. NetworkX official3.7 source docs: https://networkx.org/documentation/stable/_modules/networkx/algorithms/bipartite/matching.html and https://networkx.org/documentation/stable/_modules/networkx/algorithms/components/strongly_connected.html . Inspected Hopcroft-Karp and SCC source as alternative graph building blocks, not used as a global propagation oracle or implementation dependency. High confidence.
7. Choco official modeling docs https://choco-solver.org/docs/modeling/constraints/ and https://choco-solver.org/docs/modeling/intconstraints/ . Dedicated global strengths differ, constraints must be posted. Official repository https://github.com/chocoteam/choco-solver and releases https://github.com/chocoteam/choco-solver/releases identify standalone jars, pinned4.10.18Jan27 2025 release. High confidence.
8. Exact Maven artifact directory https://repo1.maven.org/maven2/org/choco-solver/choco-solver/4.10.18/ . Downloaded pinned dependency and source jars, inspected `AllDifferent.java` and `AlgoAllDiffAC.java`; AC_REGIN selects the non-fast classic AC implementation, while AC/AC_ZHANG choose the alternative fast implementation. Inspected source jar SHA256 `4209dc9e55fe37e39a63f3f277a9b7cfdcc65a68ee011f389f2ba892f3d95323`. High confidence, actual execution above.

## Limits

One total all-different relation on at most six variables and eight supplied values; 48 original edges and 14 original graph vertices, plus one dummy. Exhaustive partial enumeration can inspect up to9^6=531,441 tuples, while full original assignments are at most8^6=262,144 before injectivity filtering. Native generator's graph filter is classical but canonical matching extraction and per-edge Hall proof enumeration are not a production asymptotic implementation. No incremental restoration, watched triggers, Hopcroft-Karp implementation, scale/time benchmark, model training, privacy-sensitive assignment data, paid API, search engine, MUS/MCS extension or whole-CSP guarantee. No machine-checked theorem proof. All controls and adapter code are original synthetic work; upstream algorithms and solvers are credited. MIT project license does not relicense Choco's separately downloaded artifact.
