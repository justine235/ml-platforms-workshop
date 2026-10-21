"""Minimal percent-format (.py) to .ipynb converter for workshop notebooks."""
from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


def percent_to_notebook(source_path: Path, target_path: Path) -> None:
    source = source_path.read_text(encoding="utf-8")
    cells = []
    current_kind = "code"
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines
        text = "\n".join(current_lines).rstrip("\n")
        if not text.strip():
            current_lines = []
            return
        if current_kind == "markdown":
            cleaned = "\n".join(line[2:] if line.startswith("# ") else line.removeprefix("#") for line in text.splitlines())
            cells.append(new_markdown_cell(cleaned.strip("\n")))
        else:
            cells.append(new_code_cell(text))
        current_lines = []

    for raw_line in source.splitlines():
        if raw_line.startswith("# %%"):
            flush()
            current_kind = "markdown" if "[markdown]" in raw_line else "code"
            continue
        current_lines.append(raw_line)
    flush()

    notebook = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "file_extension": ".py"},
        },
    )
    nbformat.validate(notebook)
    target_path.write_text(nbformat.writes(notebook), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("target")
    args = parser.parse_args(argv)
    percent_to_notebook(Path(args.source), Path(args.target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
