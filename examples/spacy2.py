import spacy

nlp = spacy.load("en_core_web_sm")
sentences = 'I love gorillas. Peter loves gorillas. Jane loves Tarzan.'


def conj_be(subj: str) -> str:
    if subj == "I":
        return "am"
    elif subj == "you":
        return "are"
    else:
        return "is"


def gorilla_clb(seq: list, span: slice, data: dict) -> None:
    subj = seq[span.start].text
    be = conj_be(subj)
    print(f"{subj} {be} a gorilla person.")


def lover_clb(seq: list, span: slice, data: dict) -> None:
    print(
        f'{seq[span][-1]["text"]} is a love interest of'
        f'{seq[span.start]["text"]}.'
    )


clbs = {"gorilla people": gorilla_clb, "lover": lover_clb}

grammar = """
Law:
- callback: "gorilla people"
(
((pos: "PROPN") or (pos: "PRON"))
(lemma: "love")
(lemma: "gorilla")
)
Law:
- callback: "lover"
(
(pos: "PROPN")
(text: "loves")
(pos: "PROPN")
)
"""

def jsonify_span(span):
    jsn = []
    for token in span:
        jsn.append({
            'lemma': token.lemma_,
            'pos': token.pos_,
            'lower': token.lower_,
        })
    return jsn

from hmrb.core import SpacyCore
core = SpacyCore(callbacks=clbs,
                 map_doc=jsonify_span,
                 sort_length=True)

core.load(grammar)
nlp.add_pipe(core)
nlp(sentences)
