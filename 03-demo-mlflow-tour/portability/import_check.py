from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    base = Path(__file__).resolve().parent / "out"
    parser = argparse.ArgumentParser(description="Load the exported model folder and zip, then verify predictions.")
    parser.add_argument("--model-dir", default=str(base / "model-folder"))
    parser.add_argument("--model-zip", default=str(base / "model-folder.zip"))
    parser.add_argument("--sample-input", default=str(base / "sample_input.csv"))
    parser.add_argument("--reference-predictions", default=str(base / "sample_predictions.json"))
    return parser.parse_args(argv)


def predict(model_path: Path, sample: pd.DataFrame) -> list[float]:
    model = mlflow.pyfunc.load_model(str(model_path))
    return list(model.predict(sample))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sample = pd.read_csv(args.sample_input)
    reference = json.loads(Path(args.reference_predictions).read_text(encoding="utf-8"))

    folder_dir = Path(args.model_dir)
    if folder_dir.is_dir() and not (folder_dir / "MLmodel").exists():
        children = [path for path in folder_dir.iterdir() if path.is_dir()]
        if len(children) == 1:
            folder_dir = children[0]

    folder_predictions = predict(folder_dir, sample)
    extract_dir = Path(args.model_zip).resolve().parent / "_zip_check"
    if extract_dir.exists():
        for child in sorted(extract_dir.iterdir(), reverse=True):
            if child.is_dir():
                import shutil

                shutil.rmtree(child)
            else:
                child.unlink()
    extract_dir.mkdir(exist_ok=True)
    try:
        with zipfile.ZipFile(args.model_zip) as zf:
            zf.extractall(extract_dir)
        zip_predictions = predict(extract_dir, sample)
    finally:
        if extract_dir.exists():
            import shutil

            shutil.rmtree(extract_dir)

    same_as_reference = np.array_equal(np.asarray(folder_predictions), np.asarray(reference))
    zip_same = np.array_equal(np.asarray(folder_predictions), np.asarray(zip_predictions))
    payload = {
        "rows_checked": len(sample),
        "folder_matches_reference": bool(same_as_reference),
        "zip_matches_folder": bool(zip_same),
    }
    print(json.dumps(payload, indent=2))
    if not same_as_reference or not zip_same:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
