import pytest
from hmrb import rust


class TestHammurabi:
    def _setup(self) -> None:
        pass

    def _teardown(self) -> None:
        pass

    def test_hmrb(self) -> None:
        self._setup()
        assert True
        self._teardown()

    def test_rust_example(self):
        assert rust.rust_lib.is_prime(12) is 0
        assert rust.rust_lib.is_prime(13) is 1

if __name__ == "__main__":
    pytest.main(args=[__file__])
