def mark_headache(input_, slice_, data):
    print(f'I am acting on span "{input_[slice_]}" with data "{data}".')


callbacks = {"mark_headache": mark_headache}

grammar = """
Var is_hurting:
(
    optional (lemma: "be")
    (lemma: "hurt")
)

Law:
    - package: "headache"
    - callback: "mark_headache"
    - junk_attribute: "some string"
(
    (lemma: "head", pos: "NOUN")
    $is_hurting
)
"""

input_ = [
    {"orth": "My", "lemma": "my", "pos": "PRON"},
    {"orth": "head", "lemma": "head", "pos": "NOUN"},
    {"orth": "hurts", "lemma": "hurt", "pos": "VERB"},
]

# Library use case

from hmrb.core import Core

spans = [(start, input_[start:]) for start in range(len(input_))]

hmb_ext = Core()
hmb_ext.load(grammar)

# external execution
for span, data in hmb_ext._match(spans):
    print("External execution!!!")
    slice_ = slice(span[0], span[1])
    callbacks[data[0]["callback"]](input_, slice_, data)

# External execution!!!
# I am acting on span "head hurts" with data
# "{
#      'package': 'headache',
#      'callback': 'mark_headache',
#      'junk_attribute': 'pointless strings I am passing down because I can'
# }"


# internal execution
hmb_int = Core(callbacks={"mark_headache": mark_headache})
hmb_int.load(grammar)
hmb_int(input_)
#  I am acting on span "head hurts" with data
#  "{
#       'package': 'headache',
#       'callback': 'mark_headache',
#       'junk_attribute': 'pointless strings I am passing down because I can'
#  }"
