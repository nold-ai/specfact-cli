import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts import candidate_runner as runner


class RenamedLockContract(unittest.TestCase):
    def test_direct_candidate_wheel_is_hash_bound_with_all_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "specfact_semgrep-1.179.0.post1-py3-none-any.whl"
            wheel.write_bytes(b"inert unit fixture")
            locked = root / "compiled.txt"
            locked.write_text(
                "specfact-semgrep @ file:///fixture.whl --hash=sha256:"
                + hashlib.sha256(wheel.read_bytes()).hexdigest()
                + "\nmcp==1.30.0 --hash=sha256:"
                + "a" * 64
                + "\n"
            )
            actual = {"specfact-semgrep": "1.179.0.post1", "mcp": "1.30.0"}
            runner._flat_lock(locked, actual, wheel, root / "flat.txt")
            self.assertIn(
                "specfact-semgrep==1.179.0.post1 --hash=sha256:" + hashlib.sha256(wheel.read_bytes()).hexdigest(),
                (root / "flat.txt").read_text(),
            )
            self.assertIn("mcp==1.30.0", (root / "flat.txt").read_text())


if __name__ == "__main__":
    unittest.main()
