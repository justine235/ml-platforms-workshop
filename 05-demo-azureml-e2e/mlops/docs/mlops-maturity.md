# MLOps maturity mapping

| Level | Workshop mapping |
|---|---|
| 0 - No MLOps | A notebook trains a model manually and someone exports a file by hand. |
| 1 - DevOps but no MLOps | The repo has CI for code quality, but model training and deployment are still manual. |
| 2 - Automated training | `jobs\pipeline-train.yml`, `jobs\schedule.yml`, and the sweep job make training reproducible and schedulable. |
| 3 - Automated model deployment | `promote-model.yml` plus registry promotion and endpoint rollout move the model into serving with approval gates. |
| 4 - Full MLOps automated operations | Managed monitoring or the PSI drift job feeds retraining and promotion decisions with policy controls. |

The repo intentionally shows all five levels in one place so the presenter can explain both the current workshop implementation and the production target state.
