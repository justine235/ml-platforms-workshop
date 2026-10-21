from __future__ import annotations

from pathlib import Path

import nbformat


def percent_script_to_notebook_text(script_path: Path) -> str:
    lines = script_path.read_text(encoding="utf-8").splitlines()
    cells: list[nbformat.NotebookNode] = []
    current_type: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_type
        if current_type is None:
            return
        cell_id = f"cell-{len(cells) + 1:03d}"
        if current_type == "markdown":
            text = "\n".join("" if line == "#" else line.removeprefix("# ") for line in buffer)
            cells.append(nbformat.v4.new_markdown_cell(text.rstrip(), id=cell_id))
        else:
            cells.append(nbformat.v4.new_code_cell("\n".join(buffer).rstrip(), id=cell_id))
        buffer = []

    for line in lines:
        if line.startswith("# %% [markdown]"):
            flush()
            current_type = "markdown"
            continue
        if line.startswith("# %%"):
            flush()
            current_type = "code"
            continue
        if current_type is None:
            continue
        buffer.append(line)
    flush()

    notebook = nbformat.v4.new_notebook(cells=cells, metadata={"language_info": {"name": "python"}})
    nbformat.validate(notebook)
    return nbformat.writes(notebook) + "\n"


def percent_script_to_notebook(script_path: Path, notebook_path: Path) -> None:
    notebook_path.write_text(percent_script_to_notebook_text(script_path), encoding="utf-8", newline="\n")
