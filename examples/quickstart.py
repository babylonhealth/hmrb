import json
from hmrb.core import Core
from typing import Dict

with open("my-input.json", "r") as fh:
    input_ = json.load(fh)


def conj_be(subj: str) -> str:
    if subj == "I":
        return "am"
    elif subj == "you":
        return "are"
    else:
        return "is"


def gorilla_clb(seq: list, span: slice, data: Dict) -> None:
    subj = seq[span.start]["text"]
    be = conj_be(subj)
    print(f"{subj} {be} a gorilla person.")


def lover_clb(seq: list, span: slice, data: Dict) -> None:
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

hmb_ext = Core(callbacks=clbs)
hmb_ext.load(grammar)

print("Loaded grammar...")

# process sentences one by one
for i, sent in enumerate(input_, start=1):
    hmb_ext(sent)

# Loaded grammar...
# Processing sent 1
# I am a gorilla person.
# Processing sent 2
# Peter is a gorilla person.
# Processing sent 3
# Tarzan is a love interest of Jane.
