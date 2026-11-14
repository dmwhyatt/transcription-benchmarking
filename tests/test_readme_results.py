"""The README's results section and RESULTS.md must be what scripts/ computes from the committed scores, timing and
references."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_readme_results_are_current():
    run = subprocess.run([sys.executable, str(ROOT / "scripts/readme_results.py"), "--check"],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
