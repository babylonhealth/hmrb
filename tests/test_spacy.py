import pytest
spacy = pytest.importorskip("spacy")

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

def test_spacyV2(capsys):
    if spacy.__version__ >= "3.0.0":
        pytest.skip(f"Invalid spacy version {spacy.__version__}")
    nlp = spacy.load("en_core_web_sm")
    from hmrb.core import SpacyCore
    core = SpacyCore(callbacks={"pytest": dummy_callback},
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


def test_spacyV3(capsys):
    spacy = pytest.importorskip("spacy")
    if spacy.__version__ <= "3.0.0":
        pytest.skip(f"Invalid spacy version {spacy.__version__}")
    nlp = spacy.load("en_core_web_sm")

    @spacy.registry.augmenters("jsonify_span")
    def jsonify_span_pointer(span):
        return jsonify_span(span)

    @spacy.registry.callbacks("dummy_callback")
    def dummy_callback_pointer(*args, **kwargs):
        return dummy_callback(*args, **kwargs)

    conf = {}
    conf['rules']=GRAMMAR
    conf['callbacks'] = {"pytest": "callbacks.dummy_callback"}
    conf['map_doc']="augmenters.jsonify_span"
    conf['sort_length']=True

    nlp.add_pipe("hammurabi", config=conf)
    nlp(TEXT)
    captured = capsys.readouterr()
    assert captured[0] == 'OK\n'
    nlp(TEXT2)
    captured = capsys.readouterr()
    assert captured[0] == ''
