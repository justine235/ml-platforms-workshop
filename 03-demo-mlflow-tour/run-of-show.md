# Run of show

## 25-minute live version

| Minute | On screen | What to click / run | What to say | Expected result |
|---|---:|---|---|---|
| 00:00-01:30 | Slide with concept map headline | None | "You already know MLflow. I am going to show the same concepts on a laptop, in Fabric, and in Azure ML." | Audience knows the goal is comparison, not basics |
| 01:30-04:00 | Local notebook | Show tracking URI cell and experiment creation | "Start with open-source MLflow so the vocabulary is familiar: tracking URI, experiment, run." | `sqlite:///mlflow.db`, experiment exists |
| 04:00-07:00 | Local notebook | Run nested parent/child run cell | "Three child runs under one parent: prevalence, logistic regression, and HGB." | Leaderboard shows HGB on top |
| 07:00-09:00 | Local notebook | Open params/metrics/artifacts and `MLmodel` explanation | "Params, metrics, artifacts, and the model package are the portable parts." | HGB test PR-AUC about 0.385, ROC-AUC about 0.75 |
| 09:00-11:00 | Local notebook | Trigger wrong-schema `pyfunc` prediction | "This signature is the contract. It stops silent serving mistakes." | Schema error appears for missing `temp_mean` |
| 11:00-13:00 | Local notebook | Registry section | "Open-source MLflow has versions, aliases, and stages. Keep that in mind, because the wrappers diverge next." | Local registry shows versions, aliases, and stages (empirically confirmed on all 4 target MLflow versions, see validation\matrix.md) |
| 13:00-16:00 | Fabric notebook or prebuilt Fabric Experiment item | Show experiment item and one run | "Fabric uses the same MLflow run semantics, but wraps them in Experiment and ML model items." | Run visible in Fabric UI |
| 16:00-18:00 | Fabric notebook / slide | Point at runtime version and MLflow 3 note | "Runtime 2.0 ships MLflow 2.22.0. If you want MLflow 3 traces, you install it explicitly." | Version note lands clearly |
| 18:00-20:00 | Fabric notebook / slide | Show registration or model item screenshot | "Fabric's model story is version-first. Today's docs do not push stages or aliases as the main Fabric pattern." | Audience sees the first platform difference |
| 20:00-22:30 | AML notebook / job YAML | Show MLClient tracking URI cell and AML pin | "AML also speaks MLflow, but it is pinned to MLflow 2.16.2 because of `azureml-mlflow`." | Audience sees the second platform difference |
| 22:30-24:00 | AML notebook / slide | Show `mlflow.register_model` and no-code deployment note | "The same model format is deployable in AML without a custom scoring script." | Registry and deployment story are clear |
| 24:00-25:00 | Portability slide or script output | Show folder/zip portability result | "Portable model artifact: yes. Portable run history and lineage: no." | Close with the honest takeaway |

## 10-minute short version

| Minute | Focus | Action | Message |
|---|---:|---|---|
| 00:00-02:30 | Local baseline | Show experiment, one run, one model folder | Same MLflow core everywhere |
| 02:30-05:00 | Fabric differences | Show version pin + Experiment / ML model item | Fabric wraps MLflow in workspace-native items |
| 05:00-07:30 | AML differences | Show MLflow<=2.16.2 pin + AML tracking URI | AML speaks MLflow too, but with a stricter runtime pin |
| 07:30-10:00 | Honest summary | Show concept-map top 10 differences | Portable model folder, non-identical operational wrappers |

## Break-glass live fallback

1. If local training is slow, use the prebuilt `summary.json`.
2. If Fabric is unavailable, show the local notebook plus a screenshot or prebuilt Experiment item.
3. If AML compute is cold or blocked, show the AML notebook cells and the already-validated YAML.
