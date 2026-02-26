from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DIFFERENTIAL_TEST_FILES = [
    "packages/domain/tests/test_differential_candidates_perl.py",
    "packages/domain/tests/test_differential_execute_perl.py",
    "packages/domain/tests/test_differential_tree_perl.py",
    "packages/domain/tests/test_differential_semantics_perl.py",
]


def _sum_junit_counts(report_path: Path) -> dict[str, int]:
    root = ET.parse(report_path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.attrib.get(key, "0"))
    return totals


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl not found")
def test_perl_compatibility_rate_is_100_percent() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "differential-report.xml"
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *DIFFERENTIAL_TEST_FILES,
            f"--junitxml={report_path}",
        ]
        env = os.environ.copy()
        py_paths = [str(PROJECT_ROOT / "packages" / "domain" / "src"), str(PROJECT_ROOT / "apps" / "api")]
        if env.get("PYTHONPATH"):
            py_paths.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = ":".join(py_paths)

        completed = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
        assert report_path.exists(), (
            "JUnit report was not generated.\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
        totals = _sum_junit_counts(report_path)
        executed = totals["tests"] - totals["skipped"]
        passed = executed - totals["failures"] - totals["errors"]
        compatibility_rate = (passed / executed * 100.0) if executed > 0 else 0.0

        assert executed > 0, (
            "No executed differential tests found for compatibility calculation.\n"
            f"totals={totals}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
        assert completed.returncode == 0, (
            "Differential test command failed.\n"
            f"totals={totals}\n"
            f"compatibility_rate={compatibility_rate:.2f}%\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
        assert totals["failures"] == 0 and totals["errors"] == 0
        assert compatibility_rate == 100.0, (
            f"Perl compatibility rate must be 100%. got={compatibility_rate:.2f}% "
            f"(passed={passed}, executed={executed}, totals={totals})"
        )
