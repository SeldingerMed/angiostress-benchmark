from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised only on Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_package_metadata_and_dependencies() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    project = data["project"]
    assert project["name"] == "angiostress-benchmark"
    assert project["requires-python"] == ">=3.9"
    assert project["dependencies"] == []
    assert "dev" in project["optional-dependencies"]
    assert any(dep.startswith("pytest>=") for dep in project["optional-dependencies"]["dev"])


def test_pyproject_exposes_existing_benchmark_entrypoints() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    scripts = data["project"]["scripts"]
    assert scripts == {
        "angiostress-validate-contract": "benchmark.validate_contract:main",
        "angiostress-run-dias-contract": "benchmark.run_dias_contract_full_test:main",
        "angiostress-run-cathaction-subset": "benchmark.run_cathaction_contract_subset:main",
        "angiostress-run-cathaction-full-tier": "benchmark.run_cathaction_full_tier:main",
        "angiostress-run-release-audit": "benchmark.run_release_audit:main",
        "angiostress-stage-public-release": "benchmark.stage_public_release:main",
    }
