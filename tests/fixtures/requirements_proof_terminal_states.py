"""Terminal pytest states used to validate Requirements JUnit provenance."""

from _pytest.outcomes import skip


def test_skipped_by_proof() -> None:
    """Produce a collected selector with no call-phase report."""
    skip("intentional Requirements proof skip")


class TestSetupError:
    """Produce a collected selector whose setup phase fails."""

    def setup_method(self) -> None:
        raise RuntimeError("intentional Requirements proof setup error")

    def test_unreachable(self) -> None:
        raise AssertionError("setup must prevent this call phase")
