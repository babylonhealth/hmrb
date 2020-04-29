import json
from copy import deepcopy
from pathlib import Path

import pytest

from hmrb.node import FrozenMap, make_key
from tests.utils import is_probably_equal

TEST_DIR = Path(__file__).parents[0]

with open(TEST_DIR / "fixtures/test_node.json") as fh:
    test_node_data = json.load(fh)
with open(TEST_DIR / "fixtures/test_core.json") as fh:
    test_core_data = json.load(fh)


@pytest.mark.parametrize("test", test_node_data["md5_set"])
def test_node_make_set_key(test):
    set_attributes = test["set_attributes"]
    data = test["data"]
    assert make_key((set_attributes, data)) == hash(
        FrozenMap.recurse((set_attributes, data))
    )


@pytest.mark.parametrize("test", test_node_data["md5_node"])
def test_node_make_node_key(test, testBaseNode, testChildNode):
    token = test["token"]
    expected = test["expected"].replace(
        "%%", str(hash(FrozenMap.recurse(token.get("data"))))
    )
    assert is_probably_equal(str(testBaseNode._make_node_key(token)), expected)


@pytest.mark.parametrize("test", test_node_data["node_buildchild"])
def test_node_build_child(test, testBaseNode, testChildNode):
    token = test["token"]
    expected = test["expected"].replace(
        "%%", str(hash(FrozenMap.recurse(token.get("data"))))
    )
    test_key = testBaseNode._make_node_key(token)
    testBaseNode._build_child(test_key, testBaseNode)
    assert is_probably_equal(
        str((testBaseNode.child_attribute_index)), expected
    )


@pytest.mark.parametrize(
    "test_pairs", test_core_data["rules_simple"]["test_pairs"]
)
def test_object_input_simple(test_pairs, engine):
    class InputObject:
        pass

    input_ = []
    for item in test_pairs["input"]:
        input_item = InputObject()
        input_.append(input_item)
        for key, value in item.items():
            input_item.__setattr__(key, value)
    expected = test_pairs["expected"]
    vars, rules = test_core_data["rules_simple"]["rules"]
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test_pairs", test_core_data["sets"]["test_pairs"])
def test_object_input_sets(test_pairs, engine):
    class InputObject:
        pass

    input_ = []
    for item in test_pairs["input"]:
        input_item = InputObject()
        input_.append(input_item)
        for key, value in item.items():
            input_item.__setattr__(key, value)
    expected = test_pairs["expected"]
    engine.sets = {
        "apes": {"orangutan", "ape", "gorilla"},
        "cats": {"tiger", "lion", "leopard"},
        "dogs": {"bulldog", "shepherd", "spaniel"},
    }
    vars, rules = deepcopy(test_core_data["sets"]["rules"])
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)


@pytest.mark.parametrize("test_pairs", test_core_data["regex"]["test_pairs"])
def test_object_input_regex(test_pairs, engine):
    class InputObject:
        pass

    input_ = []
    for item in test_pairs["input"]:
        input_item = InputObject()
        input_.append(input_item)
        for key, value in item.items():
            input_item.__setattr__(key, value)
    expected = test_pairs["expected"]
    vars, rules = test_core_data["regex"]["rules"]
    engine._load(vars=vars, rules=rules)
    r = engine(input_)
    assert is_probably_equal(r, expected)
