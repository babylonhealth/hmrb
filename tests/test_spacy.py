import pytest

def jsonify_span(span):
    jsn = []
    for token in span:
        jsn.append({
            'lemma': token.lemma_,
            'pos': token.pos_,
            'lower': token.lower_,
        })
    return jsn

def dummy_callback(seq: list, span: slice, data: dict) -> None:
    print("OK")

TEXT = "I feel great today."
TEXT2 = "I love icecream."
GRAMMAR = """
Law:
- callback: "pytest"
(
    ((pos: "PROPN") or (pos: "PRON"))
    (lemma: "feel")
    (lemma: "great")
)
"""
CLBS = {"pytest": dummy_callback}

def test_spacyV2(capsys):
    spacy = pytest.importorskip("spacy")
    assert spacy.__version__ == "2.3.5"
    nlp = spacy.load("en_core_web_sm")

    from hmrb.core import SpacyCore
    core = SpacyCore(callbacks=CLBS,
                 map_doc=jsonify_span,
                 sort_length=True)
    core.load(GRAMMAR)
    nlp.add_pipe(core)
    nlp(TEXT)
    captured = capsys.readouterr()
    assert captured[0] == 'OK\n'
    nlp(TEXT2)
    captured = capsys.readouterr()
    assert captured[0] == ''
