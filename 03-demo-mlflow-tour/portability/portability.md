# Model portability: what moves cleanly, what does not

## The honest rule

The **MLflow model folder** is portable across local MLflow, Microsoft Fabric, and Azure Machine Learning. The **run history, lineage graph, experiment UI state, and platform-specific registry metadata are not**.

That distinction is the clean Part 1 message:

- **Portable:** `MLmodel`, flavor metadata, model weights, signature, input example, requirements, and inference behavior
- **Not portable as-is:** experiment pages, run comparison UI, Fabric ML model items, AML job lineage, stage/alias semantics, endpoint objects

## Export locally

1. **Goal:** train a local model, download the model folder, and zip it for transfer.
2. **Action:**

   ```powershell
   .venv-mlflow2222\Scripts\python.exe portability\export_model_zip.py
   ```

3. **Expected result:** the `portability\out\` folder contains:
   - `model-folder\...`
   - `model-folder.zip`
   - `sample_input.csv`
   - `sample_predictions.json`
   - `training-summary.json`
4. **Duration:** about 1-2 minutes locally once the environment is built.
5. **What to say:** "This is a plain MLflow model folder. It is the portable unit, not the platform wrapper around it."
6. **What can go wrong + fix:** if `mlflow` cannot download artifacts, check the run finished successfully and the tracking URI is still reachable.
7. **Fallback:** keep a prebuilt `model-folder.zip` in the workshop pack.

## Verify folder and zip portability

1. **Goal:** prove the folder and the zip give identical predictions to the original saved model.
2. **Action:**

   ```powershell
   .venv-mlflow2222\Scripts\python.exe portability\import_check.py
   ```

3. **Expected result:** the script prints `folder_matches_reference=true` and `zip_matches_folder=true`.
4. **Duration:** under 30 seconds.
5. **What to say:** "The packaging is portable because the signature, requirements, and inference entry point live in the model folder."
6. **What can go wrong + fix:** if prediction equality fails, the folder or zip content was changed after export; rerun the export step.
7. **Fallback:** load the model folder directly instead of the zip.

## Bring the model folder into Fabric

1. **Goal:** register an already-built MLflow model in Fabric without retraining.
2. **Action:**
   - Upload the extracted model folder to **Lakehouse > Files**.
   - In a Fabric notebook, point MLflow at the current workspace and register from the local file path or a downloaded run artifact.  
   - Example registration sketch:

   ```python
   import mlflow

   mlflow.set_experiment("fleet-failure-7d")
   model_version = mlflow.register_model(
       model_uri="file:///lakehouse/default/Files/workshop/model-folder",
       name="fleet-failure-7d",
   )
   print(model_version)
   ```

3. **Expected result:** a new **ML model** item version appears in Fabric.
4. **Duration:** upload time plus about 1 minute for registration.
5. **What to say:** "Fabric registers a versioned ML model item from a standard MLflow model folder."
6. **What can go wrong + fix:** if registration fails, verify the folder contains `MLmodel`, `requirements.txt`, and the serialized flavor artifacts.
7. **Fallback:** re-log the model from the training notebook instead of importing the folder.  
   **Source:** https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model

## Bring the model folder into Azure ML

1. **Goal:** register the same portable MLflow model in AML as an `mlflow_model`.
2. **Action:**

   ```python
   from azure.ai.ml import MLClient
   from azure.ai.ml.constants import AssetTypes
   from azure.ai.ml.entities import Model
   from azure.identity import DefaultAzureCredential

   ml_client = MLClient.from_config(DefaultAzureCredential())
   model = Model(
       path="./model-folder",
       name="fleet-failure-7d",
       type=AssetTypes.MLFLOW_MODEL,
   )
   ml_client.models.create_or_update(model)
   ```

3. **Expected result:** a new AML model version appears in the workspace.
4. **Duration:** about 1-2 minutes after the folder is local to the AML client.
5. **What to say:** "AML can treat the exact same MLflow folder as a registered model asset."
6. **What can go wrong + fix:** if the environment is incompatible, verify the folder's `requirements.txt` and stay on the AML-compatible `mlflow<=2.16.2` stack.
7. **Fallback:** register from a run URI instead of a local folder.  
   **Source:** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2

## Limits to say out loud

- A portable model folder is **not** the same thing as portable platform lineage.
- Fabric and AML do **not** expose identical registry semantics.
- MLflow 3 concepts such as LoggedModel and tracing do **not** port cleanly into AML today because AML is pinned to MLflow 2.16.x.  
  **Source:** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2

