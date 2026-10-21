# Demo data — Contoso Fleet

Synthetic data for every demo of the workshop: telematics logs, CMMS work orders and an ERP asset register that disagree on purpose.

| File | What it is |
|---|---|
| `scenario-contract.md` | The contract: story, schemas, injected problems, reconciliation rules, ML spec, expected numbers. **Read this first.** |
| `fleet_data_generator.py` | Deterministic generator of the raw files (≈ 5 s, ≈ 95 MB). |
| `fleet_reference_pipeline.py` | Reference implementation (pandas, ≈ 30 s): silver → gold → features → model → ground truth. |
| `reference_out/` | Expected results of the canonical run (≈ 6 MB): gold tables, frozen risk scores, drift report, `ground_truth.json`, `agent_eval.jsonl`. |

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install numpy pandas scikit-learn tzdata
python fleet_data_generator.py --out data --truth-dir truth --with-drift
python fleet_reference_pipeline.py --data data --out out --truth truth --with-drift
```

The last line must print `truth check ... OK` six times and `exit code 0`. Compare `out/ground_truth.json` with `reference_out/ground_truth.json`:
all counts are identical; only the ML metrics and the risk bands may move slightly with library versions.

## Rules

* Same seed → byte-identical raw files (checked across numpy 2.1/2.5 and pandas 2.2/3.0).
* `data/`, `truth/` and `out/` are generated and git-ignored. **`truth/` is the hidden answer key: never upload it to a lakehouse or give it to the agent.**
* Part 4 loads the **frozen** `reference_out/ml_failure_risk_score.csv` so the agent's answers stay deterministic.

## Break-glass path (when a live ETL step fails during the workshop)

`reference_out/` contains every gold and ml table. Upload the CSV files (decompress the two `.csv.gz` if the tool needs plain CSV) as Delta tables
named `gold.<name>` / `ml.<name>` and continue with the next demo step. Table names and row counts are listed in section 5 of the contract.
