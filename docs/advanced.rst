🤖 spaCy and callbacks
======================


Hammurabi in spaCy 2.X pipelines
---------------------------------
We provide native support for spaCy through the ``SpacyCore`` object.
The ``SpacyCore`` object can simply be integrated into your existing spaCy 2.X pipelines.


.. code-block:: python

   from hmrb.core import SpacyCore
   core = SpacyCore(callbacks=CALLBACKS,
                    map_doc=convert_to_json_fn,
                    sort_length=True)

   core.load(rules)
   nlp.add_pipe(core)

``SpacyCore`` takes a *dict* of callbacks, an optional *function* that converts spaCy doc type (to_json) to a representation that corresponds to your rules and a *bool* whether to sort and execute in ascending order according to match length.

Once the object is instantiated, you can load rules using the ``.load`` method.


Hammurabi in spaCy 3.X pipelines
---------------------------------
We also provide native support for spaCy 3.0+. You still have to import the `SpacyCore` object to run the component registration and the configuration syntax is slightly different versus 2.0.

We follow the new custom pipeline component API under ``spacy.language`` `[Link] <https://spacy.io/usage/processing-pipelines#custom-components>`_:

First, we have to register both our augmenter functions `map_doc` and any callback functions we would call in spaCy's registry.

Second, we have to create a configuration dictionary that contains the rules and references the callbacks and mapping functions as shown in the example below.

Finally, we can add the ``"hammurabi"`` pipeline component using our configuration to the spaCy pipeline.

.. code-block:: python

   from hmrb.core import SpacyCore

   @spacy.registry.augmenters("jsonify_span")
   def jsonify_span(span):
     return [
        {"lemma": token.lemma_, "pos": token.pos_, "lower": token.lower_}
        for token in span
    ]

   @spacy.registry.callbacks("dummy_callback")
   def dummy_callback(seq: list, span: slice, data: dict) -> None:
    print("OK")

   conf = {
       "rules" = GRAMMAR
       "callbacks" = {"my_callback": "callbacks.dummy_callback"}
       "map_doc" = "augmenters.jsonify_span"
   }
   nlp.add_pipe("hammurabi", config=conf)


Handling Callbacks
------------------
Callbacks allow defining a custom action to be executed upon matching. There are no restrictions on how callbacks can be used, but we provide a few handy patterns below.

Validation
``````````

Callbacks can be used to validate likely matches and thereby programmatically extend your rule matching capacity beyond the limits of the grammar.

.. code-block:: shell
   :caption: Example 1 - Validation with Callbacks

    Var cardinal:
    (
        (text: regex("^[1-9]+$"))
    )

    Var particle:
    (
        (text: "st)
        (text: "nd")
        (text: "rd")
        (text: "th")
    )

    Law I_want_an_Nth_icecream:
    - callback: "validate_Nth_icecream"
    (
        (text: "I")
        (text: "want")
        (text: regex("an?"))
        cardinal -> $cardinal
        particle -> $particle
        (text: "icecream")
    )

The above rule would successfully match `I want a 2nd icecream`.
It will also incorrectly match `I want a 2th ice cream` because we didn't spell out all valid English ordinal abbreviations explicitly.
Instead of writing an exhaustive list, callbacks can be used to filter out false positives post-match.
The following callback definition provides an example of post-match validation:

.. code-block:: python
   :caption: Example 2 - Callback example

    ORDINALS = {
        '1': 'st',
        '2': 'nd',
        '3': 'rd'
    }

    def validate_Nth_icecream(doc, span_range, match_data):
        cardinal_offsets = match_data['_']['labels']['cardinal']
        particle_offsets = match_data['_']['labels']['particle']

        cardinal = doc[*cardinal_offsets].text
        particle = doc[*particle_offsets].text

        if ORDINALS.get(cardinal, 'th') != particle:
            print('No ice cream for you!')
        else:
            print(f'This is your {cardinal}{particle} ice cream!'


Note how the labels `cardinal` and `particle` are used to easily identify relevant tokens in the match.

Modularity
``````````
When working with large nested rule bases, callbacks can quickly start to become very complex.
This can be prevented by applying a modular pattern within your rule base and your callback codebase:

.. code-block::
   :caption: Example 3 - Modularity with Callbacks

    Var cardinal:
    (
        (text: regex("^[1-9]+$"))
    )

    Var particle:
    (
        (text: "st")
        (text: "nd")
        (text: "rd")
        (text: "th")
    )

    Law abbreviated_ordinal:
    - callback: "validate_ordinal"
    (
        $cardinal
        $particle
    )

    Law Do_you_want_the_Nth_or_Nth_icecream:
    - callback: "validate_Nth_or_Nth_icecream"
    (
        (text: "Do")
        (text: "you")
        (text: "want")
        (text: "the")
        ordinal1 -> $abbreviated_ordinal
        (text: "or")
        ordinal2 -> $abbreviated_ordinal
        (text: "icecream")
    )

This example shows how you can delegate validation complexity to a sub-rule.
The ordinal validation behaviour is logically separated from the sentence validation behaviour. This allows to maintain a more readable grammar and have a cleaner 1-to-1 relationship between logical units, rules and callbacks:

.. code-block:: python
   :caption: Example 4 - Modularity with Callbacks

    ORDINALS = {
        '1': 'st',
        '2': 'nd',
        '3': 'rd'
    }


    def validate_ordinal(doc, span_range, match_data):
        cardinal_offsets = match_data['_']['labels']['cardinal']
        particle_offsets = match_data['_']['labels']['particle']

        cardinal = doc[*cardinal_offsets].text
        particle = doc[*particle_offsets].text

        if ORDINALS.get(cardinal, 'th') == particle:
            doc[cardinal_offsets[0]:particle_offsets[1]]._.ordinal = cardinal + particle


    def validate_Nth_or_Nth_icecream(doc, span_range, match_data):
        ordinal1_offsets = match_data['_']['labels']['ordinal1']
        ordinal2_offsets = match_data['_']['labels']['ordinal2']

        ordinal1 = doc[*ordinal1_offsets]._.ordinal
        ordinal2 = doc[*ordinal2_offsets]._.ordinal

        if ordinal1 and ordinal2 and ordinal1 == ordinal2:
            print('You mentioned the same ice cream twice! I want more choice!')
        else:
            print('These are both valid options! How can I choose?!')

Note that `validate_ordinal` is only responsible for validating the abbreviated ordinal.
If successful, it persists its results in the `doc` object. These will be picked up by `validate_Nth_or_Nth_icecream`, which does not perform any additional validation of the ordinal syntax. Instead, it checks that the two compared ordinals are different.
This example shows how frequent callback usage can be used to achieve better segregation of responsibility.
