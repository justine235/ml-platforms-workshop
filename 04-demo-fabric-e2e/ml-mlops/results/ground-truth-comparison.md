| metric | expected | got | OK |
|---|---:|---:|---|
| features rows | 50876 | 50876 | OK |
| labelled rows | 49028 | 49028 | OK |
| warmup rows | 3976 | 3976 | OK |
| warmup positives | 196 | 196 | OK |
| train rows | 28520 | 28520 | OK |
| train positives | 1639 | 1639 | OK |
| gap rows | 3830 | 3830 | OK |
| gap positives | 219 | 219 | OK |
| valid rows | 6591 | 6591 | OK |
| valid positives | 353 | 353 | OK |
| test rows | 6111 | 6111 | OK |
| test positives | 274 | 274 | OK |
| unlabeled rows | 1584 | 1584 | OK |
| unlabeled positives | 0 | 0 | OK |
| score rows | 264 | 264 | OK |
| score positives | 0 | 0 | OK |
| score rows | 264 | 264 | OK |
| risk band High (approx, frozen reference only) | 9 | 9 | OK |
| risk band Medium (approx, frozen reference only) | 7 | 8 | OK |
| risk band Low (approx, frozen reference only) | 248 | 247 | OK |
| drift combinations | 47 | 47 | OK |
| drift major | 4 | 4 | OK |
| drift moderate | 3 | 3 | OK |
| drift stable | 40 | 40 | OK |
| prevalence valid_pr_auc | 0.0536 | 0.0536 | OK |
| prevalence test_pr_auc | 0.0448 | 0.0448 | OK |
| rule baseline valid_pr_auc | 0.0642 | 0.0642 | OK |
| rule baseline test_pr_auc | 0.068 | 0.068 | OK |
| logistic valid_pr_auc | 0.2923 | 0.2923 | OK |
| logistic test_pr_auc | 0.2924 | 0.2924 | OK |
| hgb valid_pr_auc | 0.3356 | 0.349 | OK |
| hgb test_pr_auc | 0.3847 | 0.3882 | OK |
| hgb no fault valid_pr_auc | 0.3228 | 0.3294 | OK |
| hgb no fault test_pr_auc | 0.2841 | 0.2732 | OK |

*Band counts are only guaranteed exact for the frozen `reference_out/ml_failure_risk_score.csv` (`scenario-contract.md` lines 362-363 and 419: High 9, Medium 7, Low 248). This run (2026-10-21, local Python, Runtime-2.0-like package set: Python 3.13, pandas 2.2.3, numpy 2.5.4, scikit-learn 1.6.1) gave 9 / 8 / 247: one asset moved from Low to Medium. That is expected library-version variance, not a regression; the comparison reports the band rows as approximate (tolerance = 2 assets). The 264 scored rows, the drift counts and every PR-AUC metric (tolerance +/-0.03) matched. On the Runtime 1.3 package set the same comparison gives the same table except the two logistic-regression rows (valid / test PR-AUC 0.2929 / 0.291 instead of 0.2923 / 0.2924); every row is still OK.*
