import shutil
import subprocess
from pathlib import Path

from django.test import SimpleTestCase


class PendingActionsJavaScriptSmokeTests(SimpleTestCase):
    def test_pending_form_helper_preserves_data_fields(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for the pending-actions smoke test")

        script = Path(__file__).resolve().parent / "js" / "pending_actions_smoke.js"
        result = subprocess.run(
            [node, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr or result.stdout or "pending-actions smoke test failed",
        )
