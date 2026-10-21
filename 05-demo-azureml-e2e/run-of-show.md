# 45-minute run of show

| Minute | On screen | Action | What to say |
|---:|---|---|---|
| 0-3 | Architecture slide + README Mermaid | Explain Fabric ETL -> Azure ML MLOps split | "The same use case, two roles: data engineering in Fabric, production ML in Azure ML." |
| 3-6 | Azure portal / Studio | Show workspace, cluster, environment, ACR | "These are the resources Fabric does not give us: serving, rollout, dedicated ML RBAC, and explicit promotion." |
| 6-8 | Terminal | Submit `az ml job create --file jobs\pipeline-train.yml` | "The pipeline starts with a contract check. If the feature table drifts, the run fails early." |
| 8-12 | Studio Jobs graph | Open `prep` and `train` while they run | "The training script reuses the same shared ML core as the laptop and Fabric demos." |
| 12-16 | Metrics tab | Show `valid_pr_auc`, `test_pr_auc`, `test_precision_at_top5pct` | "A PR-AUC near 0.38 is honest and useful in a 5% positive-rate problem." |
| 16-19 | Model registry | Open `fleet-failure-7d` version tags | "The model version carries data version, git SHA, and the gate result." |
| 19-23 | Endpoint page | Show blue deployment live, green provisioned | "This is the key AML differentiator for the workshop: blue/green and mirrored rollout." |
| 23-26 | Terminal + sample-request.json | Invoke blue | "These are real rows from the score split. The model contract is the MLflow signature." |
| 26-29 | Terminal | Mirror 10% to green and read its logs, clear the mirror, then shift live traffic 90/10 | "I can shadow a new model before I make it user-visible. A deployment is live or mirrored, never both." |
| 29-33 | Batch endpoint | Start a batch invoke | "For daily scoring, we do not need low latency. We need a reliable asynchronous contract." |
| 33-37 | `src\drift.py` or drift output | Show the four major PSI pairs | "No October labels yet, so we monitor inputs and scores first, not accuracy." |
| 37-41 | GitHub Actions templates | Walk through CI, infra, train, promote | "Infra is Bicep, identity is OIDC, and promotion is approval-gated." |
| 41-45 | `bridge-fabric-aml.md` | Close with decision guide | "Use Fabric when the center of gravity is the lakehouse. Use Azure ML when the center of gravity is production ML operations." |

## Prebuilt before the audience arrives

- Environment image built once in AML: 10-20 minutes.
- Online endpoint shell plus blue deployment created once: 10-15 minutes.
- Compute cluster warmed: 3-5 minutes.
- One successful training run, endpoint invoke, and batch run already completed.

## Live steps

- Submit the pipeline.
- Watch metrics appear in Studio.
- Invoke the online endpoint.
- Mirror to green, then shift traffic.
- Trigger one batch run.

## Break-glass order

1. Open a previously successful pipeline run.
2. Show the registered model version and endpoint state.
3. Run `local-validation\run_local.py` from the prepared venv if cloud quota blocks new runs.
