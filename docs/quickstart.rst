🦍 Quick Start
===============

Hammurabi is a generic rule engine library that allows the user to match
sequences of objects with an arbitrary set of attributes against a 
grammar of rules (for more details see :ref:`syntax`).

Installation
---------------

To begin, simply install the package from a supported repository (PyPi, Gemfury, Artifactory):

.. code-block:: bash

   $ pip install hmrb


Input
--------

A great way to illustrate the use of Hammurabi is processing
annotated text against a rule grammar. Here we will implement a toy relation
extraction grammar that will look for people that love gorillas. Annotated text
is a sequence of tokens with annotation attributes -- this can be the input of
the system. For example, we can run a few sentences through
`spaCy <https://spacy.io/>`_ and serialise the output in JSON like this:

.. code-block:: python

   import json
   import spacy

   nlp = spacy.load('en_core_web_sm')
   sentences = 'I love gorillas. Peter loves gorillas. Jane loves Tarzan.'
   input_ = []
   for sent in nlp(sentences).sents:
       sent_lst = []
       for token in sent:
           token_dict = {
               'text': token.orth_,
               'lemma': token.lemma_,
               'pos': token.pos_
           }
           sent_lst.append(token_dict)
       input_.append(sent_lst)
   with open('my-input.json', 'w') as fh:
       json.dump(input_, fh, indent=2)


Content of ``my-input.json``:

.. code-block:: javascript

   [
     [
       {"text": "I", "lemma": "-PRN-", "pos": "PRON"},
       {"text": "love", "lemma": "love", "pos": "VERB"},
       {"text": "gorillas", "lemma": "gorilla", "pos": "NOUN"},
       {"text": ".", "lemma": ".", "pos": "PUNCT"}
     ],
     [
       {"text": "Peter", "lemma": "Peter", "pos": "PROPN"},
       {"text": "loves", "lemma": "love", "pos": "VERB"},
       {"text": "gorillas", "lemma": "gorilla", "pos": "NOUN"},
       {"text": ".", "lemma": ".", "pos": "PUNCT"}
     ],
     [
       {"text": "Jane", "lemma": "Jane", "pos": "PROPN"},
       {"text": "loves", "lemma": "love", "pos": "VERB"},
       {"text": "Tarzan", "lemma": "Tarzan", "pos": "PROPN"},
       {"text": ".", "lemma": ".", "pos": "PUNCT"}
     ]
   ]

Rules
--------
In order to capture the right sequence, we need to write a grammar  
with rules that would detect the sentences containing people that like gorillas.
For more details on grammar see :ref:`syntax`.
Referencing the Babylonian king, rules in Hammurabi are denoted with 
the keyword **Law**. We wrote below a simple subject-verb-object rule 
that aims to detect all *people* that love gorillas:

.. code-block::

   Law:
   (
     (pos: "PROPN")
     (text: "loves")
     (text: "gorillas")
   )

It is a very specific rule that will match only one of our input sentences, so
we may want to relax it a little bit. We can include pronouns as well as names
for the subject and abstract the number of both subject and object by using
*lemma* requirements instead of *text*:

.. code-block::

   Law:
   - callback: "gorilla people"
   (
     ((pos: "PROPN") or (pos: "PRON"))
     (lemma: "love")
     (lemma: "gorilla")
   )

Now that we've relaxed our rule, we may want to detect other things in our
input like say love interests. We can write another rule that identifies a
person that loves another person but this time keep it specific:

.. code-block::

   Law:
   - callback: "lover"
   (
     (pos: "PROPN")
     (text: "loves")
     (pos: "PROPN")
   )

Callbacks
------------

Hammurabi supports passing a callback function using the reserved `callback` attribute. 
The name provided as value is looked up against a dictionary provided to the `callbacks` parameter 
of the `Core` constructor. The functions associated with matched rules are executed 
after the matching process is complete. They are passed three positional parameters 
which then need to handle: the original object sequence `seq`, the slice of `span`
matched based on the sequence, and all the associated rule attributes from the grammar
as `data`.

All rules (**Laws**) can take an arbitrary number of attributes that will be part 
of the data structure that is passed along with a matched span. This way the user
can identify the rule that was fired and if necessary take action or access some 
specific data/information through this mechanism.



A Complete Example
-------------------

.. code-block:: python

    import json
    from hmrb.core import Core

    with open("examples/my-input.json", "r") as fh:
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
