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


def gorilla_clb(seq: list, span: slice, data: dict) -> None:
    subj = seq[span.start].text
    be = conj_be(subj)
    print(f"{subj} {be} a gorilla person.")


def lover_clb(seq: list, span: slice, data: dict) -> None:
    print(
        f"{seq[span][-1].text} is a love interest of "
        f"{seq[span.start].text}."
    )


clbs = {"loves_gorilla": gorilla_clb, "loves_someone": lover_clb}

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


def jsonify_span(span):
    return [
        {"lemma": token.lemma_, "pos": token.pos_, "lower": token.lower_}
        for token in span
    ]


from hmrb.core import SpacyCore

core = SpacyCore(callbacks=clbs, map_doc=jsonify_span, sort_length=True)

core.load(grammar)
nlp.add_pipe(core)
nlp(sentences)
