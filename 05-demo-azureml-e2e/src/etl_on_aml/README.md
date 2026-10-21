# Optional ETL-on-AML variant

This wrapper calls the shared `02-demo-data\fleet_reference_pipeline.py` unchanged. Use it only for the workshop's small synthetic dataset or for break-glass recovery. For the intended architecture, keep ETL in Fabric or another lake engine, land curated files in OneLake or ADLS, and use Azure ML for training, evaluation, registration, and serving.
