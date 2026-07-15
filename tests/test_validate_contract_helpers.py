"""Unit coverage for contract validation helper functions.

These tests intentionally use tiny in-memory/tempfile fixtures so CI can run on a
fresh checkout without the private/source datasets referenced by the full release
audit.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmark.validate_contract import (
    get_nested,
    is_finite_number,
    numeric_equal,
    summarize,
    validate_surface,
)


class ContractHelperTests(unittest.TestCase):
    def test_get_nested_reads_dotted_keys(self) -> None:
        self.assertEqual(get_nested({"a": {"b": {"c": 3}}}, "a.b.c"), 3)

    def test_get_nested_raises_on_missing_path(self) -> None:
        with self.assertRaises(KeyError):
            get_nested({"a": {}}, "a.missing")

    def test_numeric_equal_handles_exact_and_float_values(self) -> None:
        self.assertTrue(numeric_equal(1, 1.0))
        self.assertFalse(numeric_equal(1, 2))
        self.assertTrue(numeric_equal("same", "same"))
        self.assertFalse(numeric_equal("1", 1))

    def test_is_finite_number_excludes_bool_and_nonfinite_values(self) -> None:
        self.assertTrue(is_finite_number(1.25))
        self.assertTrue(is_finite_number(3))
        self.assertFalse(is_finite_number(True))
        self.assertFalse(is_finite_number(float("nan")))
        self.assertFalse(is_finite_number("3"))

    def test_validate_surface_passes_with_minimal_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_path = root / "fixtures" / "manifest.json"
            source_path.parent.mkdir(parents=True)
            source_path.write_text(
                json.dumps({"sample_count": 2, "metrics": {"dice": 0.75}}),
                encoding="utf-8",
            )

            surface = {
                "surface_id": "fixture_surface",
                "role": "core",
                "dataset": "FixtureSet",
                "source_paths": ["fixtures/manifest.json"],
                "validation_checks": [
                    {
                        "path": "fixtures/manifest.json",
                        "json_equals": {"sample_count": 2},
                        "finite_metrics": ["metrics.dice"],
                    }
                ],
            }

            result = validate_surface(root, surface)

        self.assertTrue(result["ok"])
        self.assertEqual(result["path_checks"], [{"path": "fixtures/manifest.json", "exists": True}])
        self.assertTrue(result["json_checks"][0]["ok"])
        self.assertTrue(result["finite_metric_checks"][0]["ok"])

    def test_summarize_reports_rates(self) -> None:
        report = {
            "ok": True,
            "surface_results": [
                {
                    "surface_id": "synthetic_fixture",
                    "role": "auxiliary",
                    "path_checks": [{"exists": True}],
                    "json_checks": [{"ok": True, "key": "sample_count", "actual": 1}],
                    "finite_metric_checks": [{"ok": True}],
                },
                {
                    "surface_id": "core_fixture",
                    "role": "core",
                    "path_checks": [{"exists": False}],
                    "json_checks": [{"ok": False}],
                    "finite_metric_checks": [],
                },
            ],
        }

        metrics = summarize(report)

        self.assertEqual(metrics["benchmark_contract_surface_count"], 2.0)
        self.assertEqual(metrics["benchmark_contract_core_surface_count"], 1.0)
        self.assertEqual(metrics["benchmark_contract_auxiliary_surface_count"], 1.0)
        self.assertEqual(metrics["benchmark_contract_required_file_exists_rate"], 0.5)
        self.assertEqual(metrics["benchmark_contract_json_check_pass_rate"], 0.5)
        self.assertEqual(metrics["benchmark_contract_validation_passed"], 1.0)
        self.assertEqual(metrics["benchmark_contract_synthetic_auxiliary_marked"], 1.0)


if __name__ == "__main__":
    unittest.main()
