import json
import sys
from pathlib import Path

import pytest

from hmrb.compat.v1.lang import (
    UNIT_RE,
    BlockIterator,
    Grammar,
    Law,
    Types,
    Unit,
    Var,
    char_iter,
    parse_block,
    parse_unit,
    parse_value,
    unescape,
    unique,
)
from tests.utils import is_probably_equal, parse_babylonian_data

TEST_DIR = Path(__file__).parents[0]


def test_var_parse_empty():
    var_string = """Var some_name:
(
    ( (   ) )
)"""
    lines = [(s, -1) for s in var_string.split("\n")]
    var = Var(lines, {})
    assert var.name == "some_name"
    assert len(var.body.members) == 0
    assert var.body.union is False


@pytest.mark.parametrize(
    "var_string",
    [
        "Var someнаме: (())",
        "VAR some_name: (())",
        "var some_name: (())",
        "Var $some_name: (())",
        "Var 1some_name: (())",
        "Var -some_name: (())",
    ],
)
def test_var_parse_bad_name(var_string):
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_missing_brackets():
    var_string = """Var some_name:
(
    (lemma: "word1")
    lemma: "word2"
)
"""
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_missing_bracket():
    var_string = """Var some_name:
(
    (lemma: "word1")
"""
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_escaped_quotes():
    var_string = """Var some_name:
(
    (lemma: \\"word1\\")
)
"""
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_missing_quotes():
    var_string = """Var some_name:
(
    (lemma: word1)
)"""
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_empty_ref_in_block():
    var_string = """Var some_name:
(
    ($)
)"""
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_empty_ref():
    var_string = """Var some_name:
(
    $
)"""
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_bad_block():
    var_string = """Var some_name:
(
    (bad block content)
)"""
    with pytest.raises(ValueError):
        Var(var_string.split("\n"), {})


def test_var_parse_att_escaped_quote():
    var_string = """Var some_name:
(
    (att: " \\" ")
)"""
    lines = [(s, -1) for s in var_string.split("\n")]
    var = Var(lines, {})
    assert var.name == "some_name"
    assert len(var.body.members) == 1
    assert var.body.union is False
    assert var.body.members[0].atts["att"] == ' " '


def test_var_parse_att_unescaped_quote():
    var_string = """Var some_name:
(
    (att: " " ")
)"""
    with pytest.raises(ValueError):
        lines = [(s, -1) for s in var_string.split("\n")]
        Var(lines, {})


def test_var_parse_att_quoted_brackets():
    var_string = """Var some_name:
(
    (att: " ) ")
    (att: " ( ")
    (att: " ())( ")
    (att: " )))))))))))))))) ")
)"""
    vals = [" ) ", " ( ", " ())( ", " )))))))))))))))) "]
    lines = [(s, -1) for s in var_string.split("\n")]
    var = Var(lines, {})
    assert var.name == "some_name"
    assert len(var.body.members) == 4
    assert var.body.union is False
    for m, v in zip(var.body.members, vals):
        assert m.atts["att"] == v


def test_var_parse():
    var_string = """Var some_name:
(
    (lemma: \"word1\")
    (lemma: \"word2\")
)"""
    lines = [(s, -1) for s in var_string.split("\n")]
    var = Var(lines, {})
    assert var.name == "some_name"
    assert len(var.body.members) == 2
    assert var.body.union is False


def test_var_parse_union():
    var_string = """Var some_union_name:
(
    (lemma: \"word1\")
    or
    (lemma: \"word2\")
)"""
    lines = [(s, -1) for s in var_string.split("\n")]
    var = Var(lines, {})
    assert var.name == "some_union_name"
    assert len(var.body.members) == 2
    assert var.body.union is True


def test_law_parse():
    law_string = """Law:
(
    (lemma: \"word1\")
    (lemma: \"word2\")
    )"""
    lines = [(s, -1) for s in law_string.split("\n")]
    law = Law(lines, {})
    assert law.name is None
    assert len(law.body.members) == 2
    assert law.body.union is False


def test_law_parse_named():
    law_string = """Law some_law:
(
    (lemma: \"word1\")
    (lemma: \"word2\")
    )"""
    lines = [(s, -1) for s in law_string.split("\n")]
    law = Law(lines, {})
    assert law.name == "some_law"
    assert len(law.body.members) == 2
    assert law.body.union is False


def test_law_parse_ref():
    law_string = """Law some_law:
(
    $some_var
    (lemma: \"word2\")
    )"""
    lines = [(s, -1) for s in law_string.split("\n")]
    law = Law(lines, {})
    assert law.name == "some_law"
    assert len(law.body.members) == 2
    assert law.body.union is False


def test_law_parse_ref_named():
    law_string = """Law some_law:
(
    (lemma: \"word1\")
    (lemma: \"word2\")
    )"""
    lines = [(s, -1) for s in law_string.split("\n")]
    law = Law(lines, {})
    assert law.name == "some_law"
    assert len(law.body.members) == 2
    assert law.body.union is False


def test_law_parse_atts():
    law_string = """Law some_law:
    - att: "value"
    - att2: "value2"
\t - att3: "value3"
(
    (lemma: \"word1\")
    (lemma: \"word2\")
    )"""
    lines = [(s, -1) for s in law_string.split("\n")]
    law = Law(lines, {})
    assert law.name == "some_law"
    assert len(law.body.members) == 2
    assert law.body.union is False
    assert list(law.atts.items()) == [
        ("att", "value"),
        ("att2", "value2"),
        ("att3", "value3"),
    ]


@pytest.mark.parametrize(
    "law_string",
    [
        "law someнаме:\n(())",
        "LAW some_name:\n(())",
        "law some_name:\n(())",
        "Law $some_name:\n(())",
        "Law 1some_name:\n(())",
        "Law -some_name:\n(())",
        "Law _:\n(())",
        "Law __:\n(())",
    ],
)
def test_law_parse_bad_name(law_string):
    with pytest.raises(ValueError):
        Law(law_string.split("\n"), {})


@pytest.mark.parametrize(
    "law_string",
    [
        "Law law_name:\n - att: not quoted value\n(())",
        'Law law_name:\n - -bad-att-name: "value"\n(())',
        'Law law_name:\n - 1bad-att-name: "value"\n(())',
        'Law law_name:\n -bad-att-name: "value"\n(())',
        'Law law_name:\n -- bad-att-name: "value"\n(())',
        'Law law_name:\n - "bad-att-name": "value"\n(())',
    ],
)
def test_law_parse_bad_att(law_string):
    with pytest.raises(ValueError):
        Law(law_string.split("\n"), {})


@pytest.mark.parametrize(
    "string, chars",
    [
        ('a\\"a', ["a", '\\"', "a"]),
        ("a\\aa", ["a", "\\a", "a"]),
        ("a\\ a", ["a", "\\ ", "a"]),
        ("a\\\\a", ["a", "\\\\", "a"]),
    ],
)
def test_char_iter(string, chars):
    assert list(sorted(char_iter(string))) == list(sorted(chars))


@pytest.mark.parametrize(
    "string, unescaped",
    [('a\\"a', 'a"a'), ("a\\ a", "a a"), ("a\\\\a", "a\\a"), ],
)
def test_unescape(string, unescaped):
    assert unescape(string) == unescaped


@pytest.mark.parametrize(
    "start_level, level, start_buffer, buffer, params, var_ref, opened",
    [
        (0, 1, [], [], (False, 1, 1), False, False),
        (1, 2, [*"optional"], ["("], (False, 0, 1), False, True),
        (1, 2, [], ["("], (False, 1, 1), False, True),
        (1, 2, [*"not"], ["("], (True, 1, 1), False, True),
        (1, 2, [*"optional not"], ["("], (True, 0, 1), False, True),
        (1, 2, [*"at least 5"], ["("], (False, 5, 10 ** 10), False, True),
        (1, 2, [*"3 to 5"], ["("], (False, 3, 5), False, True),
        (1, 2, [*"3 to 5 not"], ["("], (True, 3, 5), False, True),
        (1, 2, [*"$var_name"], ["("], (False, 1, 1), True, True),
        (3, 4, [*"(("], [*"((("], (False, 1, 1), False, True),
        (1, 2, [*"zero or more"], ["("], (False, 0, 10 ** 10), False, True),
        (1, 2, [*"one or more"], ["("], (False, 1, 10 ** 10), False, True),
        (1, 2, [*"0 or more"], ["("], (False, 0, 10 ** 10), False, True),
        (1, 2, [*"1 or more"], ["("], (False, 1, 10 ** 10), False, True),
    ],
)
def test_block_iter_open_bracket(
    start_level, level, start_buffer, buffer, params, var_ref, opened
):
    it = BlockIterator("")
    it.buffer = start_buffer
    it.level = start_level
    it.param_buffer = False, 1, 1
    it.in_var_ref = var_ref
    it.opened = opened
    it._open_bracket("(")
    assert it.level == level
    assert it.buffer == buffer
    assert it.param_buffer == params
    assert it.opened is True


@pytest.mark.parametrize(
    "start_level, start_buffer, error",
    [
        (0, [*"optional"], ValueError),
        (0, [*"not"], ValueError),
        (1, [*"not optional"], ValueError),
        (1, [*"not at least 2"], ValueError),
        (1, [*"not at most 2"], ValueError),
        (1, [*"not 2 to 5"], ValueError),
        (1, [*"$var_name"], ValueError),
    ],
)
def test_block_iter_open_bracket_err(start_level, start_buffer, error):
    it = BlockIterator("")
    it.buffer = start_buffer
    it.level = start_level
    it.param_buffer = False, 1, 1
    with pytest.raises(error):
        it._open_bracket("(")


@pytest.mark.parametrize(
    "start_level, level, start_buffer, buffer, params, var_ref, start_opened,"
    "opened, it_size, member_type",
    [
        (1, 0, [], [], (False, 1, 1), False, True, False, 0, None),
        (
            2,
            1,
            [*'(att: "val"'],
            [],
            (False, 1, 1),
            False,
            True,
            True,
            1,
            Types.UNIT,
        ),
        (
            2,
            1,
            [*'((att: "val")(att: "val")'],
            [],
            (False, 1, 1),
            False,
            True,
            True,
            1,
            Types.BLOCK,
        ),
        (
            3,
            2,
            [*'((att: "val")(att: "val"'],
            [*'((att: "val")(att: "val")'],
            (False, 1, 1),
            False,
            True,
            True,
            0,
            None,
        ),
    ],
)
def test_block_iter_close_bracket(
    start_level,
    level,
    start_buffer,
    buffer,
    params,
    var_ref,
    start_opened,
    opened,
    it_size,
    member_type,
):
    it = BlockIterator("")
    it.buffer = start_buffer
    it.level = start_level
    it.param_buffer = params
    it.in_var_ref = var_ref
    it.opened = start_opened
    it._close_bracket(")")
    assert it.level == level
    assert it.buffer == buffer
    assert it.param_buffer == params
    assert it.opened is opened
    assert len(it.iterable) == it_size
    if it_size:
        assert it.iterable[-1][-2] is member_type


@pytest.mark.parametrize(
    "start_buffer, buffer, params, var_ref, it_size",
    [
        ([*"$var_name"], [], (False, 1, 1), True, 1),
        ([*"$var_name_"], [], (False, 1, 1), True, 1),
        ([*"$var-name"], [], (False, 1, 1), True, 1),
        ([*"$var-name_"], [], (False, 1, 1), True, 1),
        ([*"$_var_name"], [], (False, 1, 1), True, 1),
        ([*"$var_name1"], [], (False, 1, 1), True, 1),
    ],
)
def test_block_iter_parse_var(start_buffer, buffer, params, var_ref, it_size):
    it = BlockIterator("")
    it.buffer = start_buffer
    it.param_buffer = params
    it.in_var_ref = var_ref
    it._parse_var()
    assert it.buffer == buffer
    assert it.param_buffer == (False, 1, 1)
    assert len(it.iterable) == it_size
    if it_size:
        assert it.iterable[-1][-2] is Types.VAR_REF


@pytest.mark.parametrize(
    "start_buffer, params, var_ref, err",
    [
        ([*"$1var_name"], (False, 1, 1), True, ValueError),
        ([*"$va%r_name"], (False, 1, 1), True, ValueError),
        ([*"$var_name()"], (False, 1, 1), True, ValueError),
        ([*"$var_нейм"], (False, 1, 1), True, ValueError),
        ([*"$var var"], (False, 1, 1), True, ValueError),
        ([*"$ var_var"], (False, 1, 1), True, ValueError),
        ([*"$"], (False, 1, 1), True, ValueError),
    ],
)
def test_block_iter_parse_var_err(start_buffer, params, var_ref, err):
    it = BlockIterator("")
    it.buffer = start_buffer
    it.param_buffer = params
    it.in_var_ref = var_ref
    with pytest.raises(ValueError):
        it._parse_var()


@pytest.mark.parametrize(
    "buffer, params",
    [
        ([*" \n \r \t   "], (False, 1, 1)),
        ([*""], (False, 1, 1)),
        ([*"not"], (True, 1, 1)),
        ([*"  \n not \n   "], (True, 1, 1)),
        ([*"optional"], (False, 0, 1)),
        ([*"  \n optional \n   "], (False, 0, 1)),
        ([*"zero or more"], (False, 0, 100)),
        ([*"  \n zero or more \n   "], (False, 0, 100)),
        ([*"one or more"], (False, 1, 100)),
        ([*"  \n one or more \n   "], (False, 1, 100)),
        ([*"at least 3"], (False, 3, 100)),
        ([*"  \n at least 3 \n   "], (False, 3, 100)),
        ([*"at most 5"], (False, 0, 5)),
        ([*"  \n at most 5 \n   "], (False, 0, 5)),
        ([*"4 to 17"], (False, 4, 17)),
        ([*"  \n 4 to 17 \n   "], (False, 4, 17)),
    ],
)
def test_block_iter_parse_operator(buffer, params):
    it = BlockIterator("", inf=100)
    it.buffer = buffer
    assert it._parse_operator() == params


@pytest.mark.parametrize(
    "buffer",
    [
        [*" \n \u00A0 \r \t   "],
        [*"option"],
        [*"zero\nor more"],
        [*"zero    or more"],
        [*"one     or     more   "],
        [*"one\nor more"],
        [*"at\nmost 3"],
        [*"at   most 3"],
        [*"at most3"],
        [*"at\nleast 3"],
        [*"at   least 3"],
        [*"at least3"],
        [*"1  to  3"],
        [*"1 to\n3"],
        [*"1 to3"],
    ],
)
def test_block_iter_parse_operator_err(buffer):
    it = BlockIterator("")
    it.buffer = buffer
    with pytest.raises(ValueError):
        it._parse_operator()


@pytest.mark.parametrize(
    "string, atts",
    [
        ('(att: "value", att2: "value2")', {"att": "value", "att2": "value2"}),
        ('(att: "value"\natt2: "value2")', {"att": "value", "att2": "value2"}),
        ('(att: "value"att2: "value2")', {"att": "value", "att2": "value2"}),
        ('(att:"value"\n att2:"value2")', {"att": "value", "att2": "value2"}),
        ('(att:"value"att2:"value2")', {"att": "value", "att2": "value2"}),
        (
            '(att: regex("value"), att2:"value2")',
            {"att": {"regex": "value"}, "att2": "value2"},
        ),
        (
            '(att:regex("value"), att2:"value2")',
            {"att": {"regex": "value"}, "att2": "value2"},
        ),
        (
            '(att:\nregex("value"), att2:"value2")',
            {"att": {"regex": "value"}, "att2": "value2"},
        ),
        (
            '(att.att.att: "value", att2.att: "value2")',
            {"att.att.att": "value", "att2.att": "value2"},
        ),
    ],
)
def test_parse_unit(string, atts):
    # NOTE: the parser is not supposed to do validation; only extraction
    assert parse_unit(string).atts == atts


@pytest.mark.parametrize(
    "string, valid",
    [
        ('(att: "value",)', False),
        ('(att: regex("value"))', True),
        ('(att: regex(regex("value")))', False),
        ("(att: regex())", False),
        ('(att: regex("val\\"ue"))', True),
        ('(att: regex("v(al)[ue]?"))', True),
        ('(att: "value", att2: "value2")', True),
        ('(att: "value" att2: "value2")', False),
        ('(att: "value", att2: "value2", att2: "value2")', True),
        ('(att:"value",att2:"value2",att2:"value2")', True),
        ('(  \natt: \n"value",\natt2:\n"value2",\natt2:\n"value2"\n)', True),
        ('(  \tatt: \t"value",\tatt2:\t"value2",\tatt2:\t"value2"\t)', True),
        ('(att: "value", att2: "value2", att2: "val\nue2")', True),
        ('(att: "value", att2: "value2", att2: "val\\"ue2")', True),
    ],
)
def test_validate_unit(string, valid):
    m = UNIT_RE.match(string)
    assert bool(m) is valid
    if valid:
        assert m.group() == string


@pytest.mark.parametrize(
    "string, value",
    [
        ('"value"', "value"),
        ('"value\\""', 'value"'),
        ('regex("value")', {"regex": "value"}),
        ('regex("value\\"")', {"regex": 'value"'}),
        ('regex("value[]")', {"regex": "value[]"}),
    ],
)
def test_parse_value(string, value):
    assert parse_value(string) == value


@pytest.mark.parametrize(
    "string, member_types, valid",
    [
        ('((att: "value") # comment\n(att: "value"))', "U1U1", True),
        ('((att: "value" # comment\n)(att: "value" # cmnt\n))', "U1U1", True),
        ('((att: "# comment\n")(att: "value"))', "U1U1", True),
        ('((att: "\\\\"))', "U1", True),
        ('((att: "10\\\\10"))', "U1", True),
        ("((att: true)or(att: false))", "U1U1", True),
        ("((att: True)or(att: False))", "U1U1", True),
        ("((att: True, att2: False))", "U2", True),
        ('((att: "value", att2: False))', "U2", True),
        ("((att: 12, att2: False))", "U2", True),
        ("((att: 12, att2: 12.32))", "U2", True),
        ("((att: 12, att2: ))", "", False),
        ("((att: 10)or(att: 12.09))", "U1U1", True),
        ("((att: 12.))", "U1", True),
        ("((att: -12.))", "U1", True),
        ("((att: -9))", "U1", True),
        ("((att: -12, att2: -1.9))", "U2", True),
        ("((att: 010))", "", False),
        ("((att: 010.0))", "", False),
        ("((att: 10,0))", "", False),
        ('((att: "value", att2: "value2"))', "U2", True),
        ('($some_ref (att: "value", att2: "value2"))', "R1U2", True),
        ('(() $some_ref (att: "value", att2: "value2"))', "R1U2", True),
        ("((()()))", "", True),
        ("((($)(att_name: bla)))", "", False),
        ('((($)(att: "value", att2: "value2")))', "", False),
        ('(($)(att: "value", att2: "value2"))', "", False),
        ('(($_)(att: "value", att2: "value2"))', "B1U2", True),
        ("(garbage)", "", False),
        ("()garbage", "", False),
        ('((att: regex("(value]")))', "U1", True),
        ('((att: regex("[value)")))', "U1", True),
        ('((att: regex("кирилица")))', "U1", True),
        (
            '(($_(att: "value", att2: "value2"))(att: "value", att2: "value2"))',
            "B1U2",
            True,
        ),
        ('((att: "val")(att: "val2")or(att: "var3"))', "", False),
        ('((att: "val")or(att: "val2")(att: "var3"))', "", False),
        ('((att: "val")or(att: "val2")or(att: "var3"))', "U1U1U1", True),
    ],
)
def test_parse_block(string, member_types, valid, seg2letter):
    if valid:
        block = parse_block(string, vars={})
        types = "".join(
            f"{seg2letter[m.__class__]}"
            f"{len(m.atts) if isinstance(m, Unit) else 1}"
            for m in block.members
        )
        assert types == member_types
    else:
        with pytest.raises(ValueError):
            block = parse_block(string, vars={})
            print(block)


@pytest.mark.parametrize(
    "atts, grammar_str",
    parse_babylonian_data(TEST_DIR / "fixtures/test_lang.bab"),
)
def test_grammar(grammar_str, atts, seg2letter):
    if atts["loads"]:
        grammar = Grammar(grammar_str)
        types = "".join([seg2letter[m.__class__] for m in grammar.segments])
        assert types == atts["segment_types"]
    else:
        with pytest.raises((KeyError, ValueError)):
            Grammar(grammar_str)


@pytest.mark.skipif(sys.version_info < (3, 6, 8), reason="hash values differ")
@pytest.mark.parametrize(
    "atts, grammar_str",
    parse_babylonian_data(TEST_DIR / "fixtures/test_lang_interpret.bab"),
)
def test_babylonian_translator(grammar_str, atts):
    # needs export PYTHONHASHSEED=42 before Python interpreter
    internal = json.loads(atts["internal"])
    bab = Grammar(grammar_str)
    vars, rules = list(bab.vars.values()), list(unique(bab.laws))
    assert is_probably_equal([vars, rules], internal)


@pytest.mark.parametrize(
    "string, label, lbl_idx, valid",
    [
        ('(my_label -> (att: "value"))', "my_label", 0, True),
        ('(my_label ->\n(att: "value"))', "my_label", 0, True),
        ('(my_label\n-> (att: "value"))', "my_label", 0, True),
        ('(\nmy_label-> (att: "value"))', "my_label", 0, True),
        ('(my_label-> optional (att: "value"))', "my_label", 0, True),
        ('(my_label-> optional ((att: "value")) $ref)', "my_label", 0, True),
        ("(my_label-> $ref)", "my_label", 0, True),
        ("((inner_label->$ref) my_label-> $ref)", "my_label", 1, True),
        ('(($ref (att: "value")) my_label -> $ref)', "my_label", 1, True),
        ('(($ref (att: "value")) my_label --> $ref)', "my_label", None, False),
        ('(($ref (att: "value")) my_label <- $ref)', "my_label", None, False),
    ],
)
def test_babylonian_labels(string, label, lbl_idx, valid):
    if valid:
        block = parse_block(string, vars={})
        for idx, mem in enumerate(block.members):
            if idx == lbl_idx:
                assert mem.label == label
            else:
                assert mem.label != label
    else:
        with pytest.raises(ValueError):
            parse_block(string, vars={})


@pytest.mark.parametrize(
    "err_line_num,grammar_str",
    [
        ("3", 'Law:\n - foo: "goo"\n(lemma: "foo")'),
        ("4", 'Law:\n - foo: "goo"\n(\n(lemma: "foo")'),
        ("4", 'Law:\n - foo: "goo"\n(\n(lemma: "foo))'),
        ("4", 'Law:\n - foo: "goo"\n(\n(lemma: foo"))'),
        ("4", 'Var foo:\n\n(\n(lemma: "foo")'),
        (
            "4",
            'Law:\n - foo: "bar"\n((lemma: "foo"))\n'
            'Var:\n\n(\n(lemma: "foo")',
        ),
        ("1", 'Var:\n\n(\n(lemma: "foo")'),
        (
            "6",
            'Law:\n - foo: "goo"\n((lemma: "foo"))\n'
            'Law:\n - foo2: "goo"\n(lemma: "foo")',
        ),
        ("2", 'Law:\n -foo: "bar"\n((lemma: "foo"))'),
        ("2", 'Law:\n - foo: "bar\n((lemma: "foo"))'),
        ("4", 'Law:\n - foo: "bar"\n((lemma: "foo")\npr\n(lemma: "foo"))'),
        ("3", 'Law:\n - foo: "bar"\n((lemma: "foo") pr (lemma: "foo"))'),
        (
            "6",
            'Law:\n - foo: "bar"\n((lemma: "foo")\nor\n'
            '(lemma: "foo")\n(lemma: "bar"))',
        ),
        (
            "6",
            'Law:\n - foo: "bar"\n((lemma: "foo")\nor\n'
            '(lemma: "foo")\n(lemma: "bar"))',
        ),
    ],
)
def test_line_num_in_error(grammar_str, err_line_num):
    with pytest.raises(ValueError) as err:
        _ = Grammar(grammar_str)
    assert f"line {err_line_num}" in str(err.value)
