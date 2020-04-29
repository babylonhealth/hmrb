from pathlib import Path

import pytest

from hmrb.core import Core
from hmrb.lang import Block, Law, Ref, Unit, Var
from hmrb.node import BaseNode, SetNode

from .utils import parse_babylonian_data

TEST_DIR = Path(__file__).parents[0]


@pytest.fixture()
def testBaseNode(scope="function"):
    return BaseNode()


@pytest.fixture()
def testChildNode(scope="function"):
    return BaseNode()


@pytest.fixture()
def testSetNode(scope="function"):
    return SetNode(rule_set={}, data={})


@pytest.fixture(scope='session')
def test_babylonian_grammars():
    return parse_babylonian_data(TEST_DIR / 'fixtures/grammar.bab')


@pytest.fixture(scope="function")
def engine():
    engine = Core()
    return engine


@pytest.fixture(scope="function")
def parallel_engine():
    engine = Core(n_proc=2)
    return engine


@pytest.fixture(scope='session')
def seg2letter():
    return {
        Unit: 'U',
        Block: 'B',
        Ref: 'R',
        Var: 'V',
        Law: 'L'
    }
