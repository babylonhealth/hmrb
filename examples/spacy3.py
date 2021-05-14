import spacy

nlp = spacy.load("en_core_web_sm")
sentences = "I love gorillas. Peter loves gorillas. Jane loves Tarzan."


def conj_be(subj: str) -> str:
    if subj == "I":
        return "am"
    elif subj == "you":
        return "are"
    else:
        return "is"


@spacy.registry.callbacks("gorilla_callback")
def gorilla_clb(seq: list, span: slice, data: dict) -> None:
    subj = seq[span.start].text
    be = conj_be(subj)
    print(f"{subj} {be} a gorilla person.")


@spacy.registry.callbacks("lover_callback")
def lover_clb(seq: list, span: slice, data: dict) -> None:
    print(
        f"{seq[span][-1].text} is a love interest of "
        f"{seq[span.start].text}."
    )


grammar = """
Law:
- callback: "loves_gorilla"
(
((pos: "PROPN") or (pos: "PRON"))
(lemma: "love")
(lemma: "gorilla")
)
Law:
- callback: "loves_someone"
(
(pos: "PROPN")
(lower: "loves")
(pos: "PROPN")
)
"""


@spacy.registry.augmenters("jsonify_span")
def jsonify_span(span):
    return [
        {"lemma": token.lemma_, "pos": token.pos_, "lower": token.lower_}
        for token in span
    ]


from hmrb.core import SpacyCore

conf = {
    "rules": grammar,
    "callbacks": {
        "loves_gorilla": "callbacks.gorilla_callback",
        "loves_someone": "callbacks.lover_callback",
    },
    "map_doc": "augmenters.jsonify_span",
    "sort_length": True,
}

nlp.add_pipe("hmrb", config=conf)
nlp(sentences)
