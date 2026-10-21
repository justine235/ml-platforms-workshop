from __future__ import annotations

import pytest

from notebooks.notebook_common import get_env_setting


class _FakeLibrary:
    def __init__(self, values: dict) -> None:
        self._values = values

    def __getattr__(self, name: str):
        if name in self._values:
            return self._values[name]
        raise AttributeError(name)


class _FakeVariableLibrary:
    def __init__(self, libraries: dict) -> None:
        self._libraries = libraries

    def getLibrary(self, name: str) -> _FakeLibrary:  # noqa: N802 -- mirrors the real NotebookUtils API name
        return _FakeLibrary(self._libraries[name])


class _FakeNotebookutils:
    def __init__(self, libraries: dict) -> None:
        self.variableLibrary = _FakeVariableLibrary(libraries)


def test_fabric_path_reads_the_named_variable() -> None:
    fake = _FakeNotebookutils({"fleet_mlops": {"driftMajorThreshold": 0.30}})
    value, source = get_env_setting("driftMajorThreshold", 0.25, notebookutils_obj=fake)
    assert value == 0.30
    assert source == "variable library"


def test_fabric_path_falls_back_on_missing_variable_name() -> None:
    fake = _FakeNotebookutils({"fleet_mlops": {"someOtherVariable": 1}})
    value, source = get_env_setting("driftMajorThreshold", 0.25, notebookutils_obj=fake)
    assert value == 0.25
    assert source == "default"


def test_fabric_path_falls_back_on_missing_library() -> None:
    fake = _FakeNotebookutils({})
    value, source = get_env_setting("driftMajorThreshold", 0.25, notebookutils_obj=fake)
    assert value == 0.25
    assert source == "default"


@pytest.fixture
def _clear_vl_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLEET_VL_DRIFTMAJORTHRESHOLD", raising=False)


def test_local_path_without_env_var_uses_default(_clear_vl_env: None) -> None:
    value, source = get_env_setting("driftMajorThreshold", 0.25)
    assert value == 0.25
    assert source == "default"


def test_local_path_with_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLEET_VL_DRIFTMAJORTHRESHOLD", "0.30")
    value, source = get_env_setting("driftMajorThreshold", 0.25)
    assert value == pytest.approx(0.30)
    assert source == "variable library"
