import json
from pathlib import Path

import pytest

from hmrb.core import Core
from .utils import is_probably_equal, parse_babylonian_data

TEST_DIR = Path(__file__).parents[0]


@pytest.mark.parametrize(
    "atts, grammar_str", parse_babylonian_data(TEST_DIR / "fixtures/test_e2e.bab")
)
def test_end_to_end(atts, grammar_str):
    callbacks = {"my_callback": lambda span, value: print(span, value)}
    engine = Core(callbacks=callbacks)
    engine.load(grammar_str)
    r = engine(json.loads(atts["input"]))
    expected = json.loads(atts["output"])
    expected = {tuple(json.loads(key)): val for key, val in expected.items()}
    assert is_probably_equal(r, expected)
