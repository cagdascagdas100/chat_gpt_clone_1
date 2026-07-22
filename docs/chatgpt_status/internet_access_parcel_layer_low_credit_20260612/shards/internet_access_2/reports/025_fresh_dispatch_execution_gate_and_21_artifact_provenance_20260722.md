# Fresh dispatch execution gate and twenty-one-artifact provenance

The canonical wrapper previously depended on an external procedure to ensure all thirteen dispatch gates passed. A direct/manual invocation could therefore reach network work without re-evaluating the current watcher, runner, queue and final-integration state.

The revised wrapper requires an eight-file dispatch evidence root and an expected final integration head SHA. Before any network request, it re-runs the read-only readiness evaluator, requires exactly 13/13 PASS, verifies a merged non-draft main PR at the expected head, requires fresh watcher and runner evidence, hashes all eight evidence files, and writes `dispatch_execution_gate_latest.json`.

The dispatch gate audit is then bound as artifact 21 into the final provenance chain. Deterministic fixtures pass dispatch gate 20/20, dispatch-bound provenance 18/18, wrapper 68/68, website 26/26 and consistency 19/19. Combined validation is 475/475. No runner was started, no queue or ownership record was written, real rows remain zero, and final_ready remains false.
