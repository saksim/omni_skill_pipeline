from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORK_ORDERS_PATH = REPO_ROOT / "docs" / "current" / "architecture" / "skill-distillation-v2-work-orders.md"
TP_ID_PATTERN = re.compile(r"TP-E\d{1,2}-\d{2,3}(?!\d)")


class TPRegistryScriptTests(unittest.TestCase):
    def _extract_tp_ids(self, raw_text: str) -> set[str]:
        return {item.group(0) for item in TP_ID_PATTERN.finditer(raw_text)}

    def test_list_command_exposes_known_work_orders(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_tp_tests.py", "--list"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("TP-E4-01", completed.stdout)
        self.assertIn("TP-E6-02", completed.stdout)

        work_orders_text = WORK_ORDERS_PATH.read_text(encoding="utf-8")
        work_order_tp_ids = self._extract_tp_ids(work_orders_text)
        self.assertTrue(work_order_tp_ids)

        listed_tp_ids = self._extract_tp_ids(completed.stdout)
        missing = sorted(work_order_tp_ids - listed_tp_ids)
        self.assertFalse(missing, "Missing TP mappings in run_tp_tests.py: %s" % ", ".join(missing))
        extra = sorted(listed_tp_ids - work_order_tp_ids)
        self.assertFalse(
            extra,
            "Undocumented TP mappings in run_tp_tests.py (not found in work-orders): %s"
            % ", ".join(extra),
        )

    def test_all_dry_run_builds_unittest_command(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_tp_tests.py", "--all", "--dry-run", "--python", sys.executable],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Selected TP IDs:", completed.stdout)
        self.assertIn("Command:", completed.stdout)
        self.assertIn("-m unittest", completed.stdout)


if __name__ == "__main__":
    unittest.main()
