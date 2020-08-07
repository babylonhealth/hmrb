import json
from copy import deepcopy
from pathlib import Path

import pytest

from hmrb.compat.v1.core import SpacyCore

from .utils import FakeDocument, FakeToken, is_probably_equal

TEST_DIR = Path(__file__).parents[0]

with open(TEST_DIR / "fixtures/test_core.json") as fh:
    test_core_data = json.load(fh)


@pytest.mark.parametrize("test", test_core_data["rules_simple"]["test_pairs"])
def test_rules_simple(test, engine):
    input_ = test["input"]
    expected = test["expected"]
    vars, rules = test_core_data["rules_simple"]["rules"]
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test", test_core_data["rules_overlap"]["test_pairs"])
def test_rules_overlap(test, engine):
    input_ = test["input"]
    expected = test["expected"]
    vars, rules = test_core_data["rules_overlap"]["rules"]
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test", test_core_data["rules_att_mix"]["test_pairs"])
def test_rules_att_mix(test, engine):
    input_ = test["input"]
    expected = test["expected"]
    vars, rules = test_core_data["rules_att_mix"]["rules"]
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test", test_core_data["vars"]["test_pairs"])
def test_rules_var(test, engine):
    input_ = test["input"]
    expected = test["expected"]
    vars, rules = deepcopy(test_core_data["vars"]["rules"])
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test", test_core_data["sets"]["test_pairs"])
def test_rules_set(test, engine):
    input_ = test["input"]
    engine.sets = {
        "apes": {"orangutan", "ape", "gorilla"},
        "cats": {"tiger", "lion", "leopard"},
        "dogs": {"bulldog", "shepherd", "spaniel"},
    }
    expected = test["expected"]
    vars, rules = deepcopy(test_core_data["sets"]["rules"])
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test", test_core_data["callbacks"]["test_pairs"])
def test_rules_callback(test, engine):
    def callback(input_, span, data):
        data["package"] = data["package"] + "-fired"

    def bad_callback(input_, span, data):
        raise Exception("bad callback")

    input_ = test["input"]
    expected = test["expected"]
    engine.callbacks = {"clb_1": callback, "exception_clb": bad_callback}
    vars, rules = test_core_data["callbacks"]["rules"]
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test", test_core_data["regex"]["test_pairs"])
def test_rules_regex(test, engine):
    input_ = test["input"]
    expected = test["expected"]
    vars, rules = test_core_data["regex"]["rules"]
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


def test_spacy_component():
    grammar = """
Law:
    - package: "NAME"
    - callback: "clb"
(
    (orth: "John")
)
"""

    def callback(doc, span, data):
        print(doc, span, data)
        for tok in doc[span]:
            tok._.name = data["package"]

    rules = SpacyCore(callbacks={"clb": callback})
    rules.load(grammar)
    input_ = [
        FakeToken("John", "John", "NOUN"),
        FakeToken("is", "be", "VERB"),
        FakeToken("my", "my", "PRON"),
        FakeToken("name", "name", "NOUN"),
    ]
    doc = FakeDocument(input_)
    doc = rules(doc)
    assert isinstance(doc, FakeDocument)  # correct return type
    assert doc[0]._.name == "NAME"  # callback triggered


@pytest.mark.parametrize("test", test_core_data["labels"]["test_pairs"])
def test_rules_labels(test, engine):
    input_ = test["input"]
    expected = test["expected"]
    vars, rules = deepcopy(test_core_data["labels"]["rules"])
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


with open(TEST_DIR / "fixtures/test_partial_p1.bab") as fh:
    PART1 = fh.read()

with open(TEST_DIR / "fixtures/test_partial_p2.bab") as fh:
    PART2 = fh.read()


@pytest.mark.parametrize("test", test_core_data["partial"]["test_pairs"])
def test_partial_loading(test, engine):
    input_ = test["input"]
    expected = test["expected"]
    engine.load(PART1)
    engine.load(PART2)
    r = engine(input_)
    assert is_probably_equal(r, expected)


def test_partial_loading_error(engine):
    with pytest.raises(ValueError):
        engine.load(PART2)


with open(TEST_DIR / "fixtures/test_partial_p3.bab") as fh:
    PART3 = fh.read()


def test_partial_loading_override(engine):
    engine.load(PART1)
    engine.load(PART2)
    with pytest.raises(ValueError):
        engine.load(PART3)


@pytest.mark.xfail
def test_google_regex():
    import re2 as re

    r = re.compile(r"(name)\s*:")
    r.match("This is my name: Hammurabi")
