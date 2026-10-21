# Drift alert recipe

## What this demo does

- Fabric has no first-party managed model-drift monitor for classical ML models in this workshop flow.
- We build our own detector in `nb_07_drift_monitor`.
- The notebook writes `ml.drift_report` and emits machine-readable JSON with `status = alert` when major drift exists.

## Option A — pipeline-native alert

Use this path for the Friday demo because it is deterministic and already matches the authored pipeline item.

1. Open `pl_fleet_daily`.
2. Confirm `RunDriftMonitor` executes after scoring, and `RunPromotionGate` runs right after `RunDriftMonitor`.
3. Confirm `IfDriftAlert` depends on `RunPromotionGate` success (the gate and the alert are independent decisions that both wait on the drift read).
4. Confirm the true branch contains `SendDriftAlertEmail`.
5. Confirm `IfDriftAlert`'s expression reads the notebook's **exit value**, not a string search over the raw activity output:
   `@equals(json(activity('RunDriftMonitor').output.result.exitValue).status, 'alert')`.
   (An earlier draft used `@contains(string(activity('RunDriftMonitor').output), '"status": "alert"')` — that can never match, because `nb_07` exits `json.dumps(payload, indent=2, sort_keys=True)` and `string(...)` re-escapes the inner quotes to `\"status\": \"alert\"`, which never appears literally in the stringified output. Fixed in `fabric-git/pl_fleet_daily.DataPipeline/pipeline-content.json`.)
6. Replace placeholders:
   - `__OFFICE365_CONNECTION_ID__`
   - `__ALERT_TO__`
7. Test the pipeline with the workshop drift batch.
8. Expected result:
   - notebook exit value is JSON with `status: "alert"` (visible as the `RunDriftMonitor` activity's `output.result.exitValue` in the Monitor hub)
   - the pipeline takes the true branch
   - an email is sent to the configured recipients

### Why this works

- `nb_07_drift_monitor` uses PSI thresholds from shared code:
  - stable `< 0.10`
  - moderate `> 0.10`
  - major `> 0.25`
- The workshop drift batch produces 4 major combinations, so the branch should fire.

### Known caveat

- ⚠ UNVERIFIED: `output.result.exitValue` is the community-documented path to a notebook activity's exit value (it is NOT on the Fabric Learn "Notebook activity" page as of this writing). VERIFY on first live run: open the `RunDriftMonitor` activity's Output JSON in the Monitor hub, confirm `result.exitValue` exists, and confirm its parsed `status` field reads `"alert"` when `nb_07` reports major drift.
- A tiny local test (`local-validation/tests/test_drift_exit_payload.py`) checks that `nb_07`'s exit payload round-trips through `json.loads` and always has a `status` key, so the shape this expression depends on is covered outside the live tenant too.

## Option B — Activator

Use this when you want a more event-driven story than a batch schedule.

Verified current Learn facts:
- Activator is a no-code event detection engine in Fabric Real-Time Intelligence.
- It can trigger pipelines, notebooks, dataflows, Spark job definitions, copy jobs, Teams messages, emails, and Power Automate flows.
- Passing parameter values to Fabric items from Activator is ⚠ PREVIEW.

### Activator flow

1. Make `ml.drift_report` observable through the chosen Activator source path.
2. Create or open an Activator rule.
3. In the rule pane, go to **Action**.
4. Choose one of:
   - Teams message
   - Email
   - Pipeline
   - Notebook
5. If you trigger a Fabric item, select it from the OneLake catalog.
6. Save the rule.
7. Use **Test action**.
8. Start the rule.

### Recommended workshop pattern

- Keep the detector in the batch notebook.
- Use Activator only as the last-mile notifier or orchestration trigger.
- Pass summary fields such as drift status, equipment class, or sensor only if the preview parameter feature is available in the tenant.

### Activator cautions

- ⚠ PREVIEW: passing parameter values to Fabric items from Activator.
- ⚠ UNVERIFIED for this specific workshop tenant: the simplest supported source binding from `ml.drift_report` into Activator without an extra stream or report layer.

## Teams vs Outlook choice

- Pipeline path:
  - Outlook/Office 365 email is simpler because the DataPipeline definition documents `Office365Email` explicitly.
- Activator path:
  - Teams is attractive for the demo because Activator explicitly lists Teams messages as a supported action.

## What to say live

- “There is no built-in managed drift service here, so we schedule a notebook that writes a drift table and returns a machine-readable status.”
- “For the workshop we use email in the pipeline because it is deterministic. Activator is the event-driven extension point when the tenant is ready.”
