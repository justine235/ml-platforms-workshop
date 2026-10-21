# CI/CD notes for the Fabric ML workshop

## Honest promotion story

Git integration and deployment pipelines for Fabric ML experiments and ML models are currently ⚠ PREVIEW and metadata-only. Experiment runs and model versions stay in workspace storage and are not versioned or promoted by Git sync or deployment pipelines. For this workshop, that means the promotion unit is code plus item metadata. The model artifact itself is re-trained or re-logged in each workspace, and `nb_08_promotion_gate` **computes** which version should become champion -- but the daily pipeline runs it report-only (`RunPromotionGate` passes no parameters, so `apply_pointer_update` stays `False` by default); `ml.model_pointer` is only updated when someone re-runs `nb_08` with `apply_pointer_update = True`. We do not claim cross-workspace model copying as the main Friday path.

## Files in this folder

- `deploy.py` — current-doc-pattern deploy entry point for `fabric-cicd`
- `config.yml` — deployment config template
- `parameter.yml` — environment-specific replacements for workspace, lakehouse, connection, and alert values (notebook/pipeline IDs are resolved natively by fabric-cicd from each item's own `.platform` logicalId, not by this file)
- `github-workflows\fabric-mlops-deploy.yml` — GitHub Actions workflow with OIDC login and dev/test/prod environments

## Deploy script

- Authentication pattern: `azure/login@v2` in CI, then `AzureCliCredential()` in Python
- Deployment API pattern: `deploy_with_config(...)`
- Repository directory: `../fabric-git`
- Item types in scope:
  - `Notebook`
  - `DataPipeline`
  - `VariableLibrary`

## Parameter file

The parameter file replaces:
- target workspace ID inside item definitions
- lakehouse ID
- Office 365 connection ID
- alert recipient list

It does NOT carry notebook or pipeline IDs: every `TridentNotebook` activity in
`pl_fleet_daily` already stores the real `notebookId` (each target notebook's own
`.platform` `config.logicalId`, computed by `tools/build_notebooks.py`) alongside a
zero-GUID `workspaceId` (meaning "this workspace"), which is exactly the pattern the
public `fabric-cicd` sample uses -- `fabric-cicd` resolves logicalId -> real item ID
natively during Git sync/deploy, so no notebook-ID placeholder or find/replace is
needed. Replace the remaining placeholder GUIDs before any real deployment.

## Variable Library design

Native Fabric variable-library concepts used here:
- one library item: `fleet_mlops`
- value sets: `DEV`, `TEST`, `PROD`
- shared values:
  - workspace ID
  - `lh_fleet` item reference
  - alert connection and recipient list
  - experiment/model/table names
  - drift thresholds 0.10 and 0.25

What the code actually reads from it today: only the two drift thresholds (`driftModerateThreshold`, `driftMajorThreshold`), read by `nb_07_drift_monitor` via `notebookutils.variableLibrary.getLibrary("fleet_mlops")` with a hardcoded fallback (0.10 / 0.25) on any lookup failure. Every other value in the library (workspace ID, lakehouse reference, connection/recipient, experiment/model/table names) is **not read by any notebook or pipeline activity** -- those are still supplied the classic way, by `parameter.yml` find/replace at deploy time. The pipeline's own native alternative for its own parameters, not used by the shipped `pipeline-content.json`, is the Library variables tab (`@pipeline().libraryVariables.<ref>`) -- documented in `rebuild-guide.md` as an optional exercise. VERIFY live: `nb_07` should print `thresholds source: variable library`; if it prints `default`, check the library/variable names and active value set.

## Deployment pipelines recipe

Recommended stages:
1. Dev
2. Test
3. Prod

Recommended rules:
- workspace bindings per stage
- lakehouse and connection rebinding per stage
- deployment plan only if you must force an order beyond dependency inference

Use deployment pipelines when:
- the workspace is already Git-connected
- the team wants side-by-side compare/deploy UX
- metadata promotion is enough

Use `fabric-cicd` when:
- you want GitHub Actions or Azure DevOps automation
- you need repository-driven deployments from code review
- you want parameter-file control over placeholder IDs

Do not claim either path promotes trained model versions between workspaces today.
