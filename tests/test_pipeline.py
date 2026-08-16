# tests/test_pipeline.py
"""Smoke test for the GenAR PADER pipeline.
Runs the pipeline on a tiny fixture CSV and checks that the three
output artefacts are created and contain expected minimal data.
"""

import os
import subprocess
import pathlib
import json

import unittest

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.repo_root = pathlib.Path(__file__).resolve().parents[1]
        self.sample_csv = self.repo_root / "scratch" / "sample.csv"
        self.out_dir = self.repo_root / "scratch" / "test_output"
        if self.out_dir.exists():
            for f in self.out_dir.iterdir():
                f.unlink()
        else:
            self.out_dir.mkdir(parents=True)

    def test_end_to_end(self):
        # Run the main script
        cmd = ["python", str(self.repo_root / "src" / "main.py"),
               "--data", str(self.sample_csv),
               "--out", str(self.out_dir),
               "--non-interactive"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"Process failed: {result.stderr}")

        # Expected output files
        report_md = self.out_dir / "pader_report.md"
        case_csv = self.out_dir / "case_listing.csv"
        run_log = self.out_dir / "run_log.json"
        for path in (report_md, case_csv, run_log):
            self.assertTrue(path.is_file(), msg=f"Missing {path.name}")
            self.assertGreater(path.stat().st_size, 0, msg=f"Empty {path.name}")

        # Basic sanity check on run_log content
        with open(run_log, "r", encoding="utf-8") as f:
            log = json.load(f)
        self.assertIn("validation", log, "run_log missing validation block")
        self.assertIn("review_log", log, "run_log missing review_log block")

if __name__ == "__main__":
    unittest.main()
