# Verify before Friday

Every `⚠ UNVERIFIED` or `⚠ PREVIEW` item below must be checked in the target tenant before the live workshop.

## Fabric

1. **`⚠ UNVERIFIED` exact notebook `Files/` path for importing `03-demo-mlflow-tour\code`**  
   Check the actual lakehouse or Git-mirror path used in rehearsal.
2. **`⚠ UNVERIFIED` exact Fabric UI button labels and placement for run comparison**  
   Rehearse the Experiment item clicks in the real workspace.
3. **`⚠ UNVERIFIED` nested-run UI behavior in Fabric**  
   Verify whether parent/child runs are visually obvious enough for the live story.
4. **`⚠ UNVERIFIED` Fabric-native alias/stage semantics**  
   Current docs do not make them a safe primary pattern; verify only if you plan to mention them.
5. **`⚠ PREVIEW` ML model endpoints**  
   Verify the tenant setting and regional availability in the actual workspace.

## Azure ML

6. **`⚠ UNVERIFIED` AML alias support in current docs and runtime**  
   Do not depend on aliases unless verified live.
7. **`⚠ UNVERIFIED` exact AML compute-instance relative paths for the shared code folder**  
   Rehearse the notebook import path.
8. **`⚠ UNVERIFIED` job YAML validation against the live workspace asset names**  
   Confirm `fleet-features-ref:1`, `cpu-cluster`, and the final environment name.
9. **`⚠ UNVERIFIED` AML stage UI visibility for the exact workspace experience**  
   The docs say stages are MLflow-SDK-only; rehearse that message in Studio.

## Cross-platform demo

10. **RESOLVED (2026-10-19)** local MLflow registry alias AND stage behavior empirically validated across all 4 target MLflow versions (2.12.2, 2.16.2, 2.22.0, 3.17.0), sqlite backend. See `validation\matrix.md` for the full table. Both work in all 4; stage APIs carry a deprecation warning everywhere.
    Superseded by the empirical result above; still worth one live rehearsal pass for timing, not for correctness.
11. **`⚠ UNVERIFIED` portability registration-from-folder flow into Fabric**  
    Rehearse the import into a real Fabric workspace before saying it live.
12. **`⚠ UNVERIFIED` portability registration-from-folder flow into AML with the chosen environment**  
    Rehearse the import with `MLClient.models.create_or_update`.

## General pre-flight

13. **RESOLVED (2026-10-19)** `.ipynb` rebuilt from percent-format source, `nbformat.validate`
    passes, AND fully executed headlessly end to end (23 cells, zero errors) after fixing a real
    `NameError` (`__file__` undefined in a notebook kernel) and a real registry bug (an unlogged
    model version breaking `models:/<name>/latest`). See `RESULTS.md` for the fix and run details.
14. **RESOLVED (2026-10-19)** `py_compile`, `ruff`, and `pytest` all pass (7/7 tests, including 3 new tests for the skops-trusted-types fix).
15. **RESOLVED (2026-10-19)** `validation\matrix.md` refreshed with real runs from the 4 current venvs (`.venv-mlflow2122`, `.venv-mlflow2162`, `.venv-mlflow2222`, `.venv-mlflow3`), plus a portability cross-version check and the stages/aliases table.
16. **RESOLVED (2026-10-19)** Contract metrics reconfirmed by all 4 training runs (byte-identical): test PR-AUC 0.3882, test ROC-AUC 0.7551 — both within the +/-0.03 tolerance of the contract targets below.
    - HGB test PR-AUC about **0.385**
    - HGB test ROC-AUC about **0.75**
    - tolerance **+/- 0.03**
