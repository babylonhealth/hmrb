.. _syntax:

🎯 Writing Rules
=================
Adding rules to Hammurabi is straightforward using a simple human readable
syntax capable of defining complex rules.

This section walks you through steps to define rules for Hammurabi. Each subsection
introduces a new feature that can be added to better express your rule. Naturally
you can combine them as you see fit.

Basic rule syntax
------------------
The following code snippet shows the structural framework of a simple rule.
You define a rule as a ``Law`` within Hammurabi.

.. code-block:: shell

   Law <name>:
       - <return key>: "<return value>"
       - <return key>: "<return value>"
       - callback: "<callback name>"

   (
       (attribute: "value")
       ...
       (attribute: "value")
   )

- Following a ``Law`` keyword, you can **optionally** define a name for the rule. This allows the immediate re-use of the law in a subsequent rule.
- The initial head part of the ``Law`` lists key-value pairs that are returned if the rule is matched. The return key can be any string value except reserved keys ``callback`` and ``_``.
- Finally, the body part contains definition of the token sequence which the rule is intended to match.

Attributes matched by the rule engine are defined as **key-value** pairs.

- **Keys** come from your problem setting's vocabulary. For instance, in time-series, this could be any attribute of a time-step, or in Natural Language Processing this could be meta-data on your word tokens.

- **Values** define the actual token needed the pass the rule. Types supported are ``string``, ``bool``, ``int`` and ``float``. The values most importantly should align with your key vocabulary.

.. note:: **Escaping characters** is required in string values for special characters i.e. ``"`` should be entered as ``\"`` and ``\`` as ``\\``.


.. code-block:: shell
   :caption: Example 1 - Single attribute

   Law
       - package: "found number of icecreams needed"
   (
       (written_number: True)  # could match a number like "one"
       (text: "icecream")
   )


You can also define multiple attribute conditions that must be true for an element (we consider this as an ``and`` relationship between attributes). For example, in the below rule both icecream and yell attributes need to match the second sequence element.

.. code-block:: shell
   :caption: Example 2 - Multiple attributes for a token
   :emphasize-lines: 5

   Law
       - package: "found angry person demanding lots of icecream"
   (
       (text: "much")
       (text: "icecream", yell: True)
       (today: True)
   )

.. figure:: _static/alex-jones-6799-unsplash.jpg
   :align: center
   
   Photo by `Alex Jones <https://unsplash.com/photos/VPnvh8vj7lc>`_

..

Union (OR)
----------
You can also define rules that require a union logic between tokens. Unions are defined by the ``or`` keyword.
Note that unions must be wrapped in brackets (the indent is optional)

.. code-block:: shell
   :caption: Example 3 - Simple union example

   Law
       - package: "found person with small icecream appetite"
   (
       (
          (text: "small")
          or
          (text: "little")
       )
       (text: "icecream")
   )

Multiple unions can be nested in a simple structure allowing Hammurabi to define complex rules in a simple manner.

.. code-block:: shell
   :caption: Example 4 - Nested union example

   Law
       - package: "handling lots of icecream"
   (
      (
         (
            (text: "much")
            or
            (text: "little")
         )
      or
         (
            (type: "vanilla")
            or
            (type: "chocolate")
            or
            (type: "strawberry")
         )
     )
     (text: "icecream")
   )

.. note:: ``and`` syntax: by definition an intersection logic exists between sequential tokens. As mentioned earlier, an ``and`` logic exists between attribute key-value pairs.

Optionals and multiples
-----------------------

To allow compact rules, Hammurabi supports defining optionals and multiples.
Each section or element can be marked with the number of times it should be matched.
The table below summarises the available logical syntax.

================  =====  ======
Syntax             Min     Max
================  =====  ======
``optional``        0       1
``one or more``     1      inf
``zero or more``    0      inf
``X to Y``          X       Y
(default)           1       1
================  =====  ======

.. code-block:: shell
   :caption: Example 5 - Optionals example
   :emphasize-lines: 4

   Law
       - package: "found person who might be willing to pay for icecream"
   (
       optional (text: "free")
       (text: "icecream")
   )

.. code-block:: shell
   :caption: Example 6 - Complex optionals example
   :emphasize-lines: 4,6

   Law
       - package: "found person only looking for (very) big icecream"
   (
       zero or more (text: "very")
       (text: "big")
       1 to 2 (text: "icecream")
   )

Naturally, this functionality can be combined with any other syntax on any level.

.. code-block:: shell
   :caption: Example 7 - Nested optionals example

   Law
       - package: "found person only looking for bright icecream of any flavor"
   (
       (text: "bright")
       optional (
            (type: "vanilla")
            or
            (type: "chocolate")
            or
            (type: "strawberry")
       )
       (text: "icecream")
   )


Regular Expression
------------------
Hammurabi also supports defining attribute values as regular expressions (see `Python RE library <https://docs.python.org/3/library/re.html/>`_).
The full syntax is as (attribute: regex("<regex expression>")) and can be used on any string value.

.. code-block:: shell
   :caption: Example 8 - Regex example
   :emphasize-lines: 5

   Law
       - package: "found person only looking for some quantity of icecream"
   (
       optional (text: "around")
       (text: regex("([0-9])\w+"))
       (text: "icecream")
   )

.. note:: **Escaping character inside Regex** needs to be doubled for special characters i.e. ``\.`` should be entered as ``\\.`` and ``\\`` as ``\\\``.


Variables
---------
Variables allow the reuse of rules, which makes the grammar more readable as well as more efficient.
There are two types of variabels supported in Hammurabi: ``Var`` and ``named Law``.

**Definitions:**

- ``Var <name>:`` To reuse a sequence of token rules simply define it as a variable. The variable definition uses a similar syntax to defining laws with the addition of naming the variable. This allows us to refer to it in subsequent code. Note that variable definitions are not actually rules. They are elements to be used in Laws and will not be matched on their own. For this same reason, they consist solely of the body (i.e. no head part). To support functionality where you want to not only define a rule but also reuse it in other rules, we added named laws (see below).
- ``Law <name>:`` To reuse a Law as a variable add a name to its definition. You can refer to it in exactly the same way as a variable `$name`.

**References:**

- ``$<name>`` use references to add a sequence defined in a variable to your rule (or to another variable). A reference is defined as the name of a defined variable preceded by ``$``. Variable references can be used in conjunction with other features of the language such as optionals and labels.

.. code-block:: shell
   :caption: Example 9 - Variable example
   :emphasize-lines: 1-11,18

   Var flavored_icecream:
   (
      (
         (type: "vanilla")
         or
         (type: "chocolate")
         or
         (type: "strawberry")
      )
      (text: "icecream")
   )
   
   Law
      - package: "found person only looking for some quantity of icecream"
   (
      (text: "we")
      (text: "want")
      $flavored_icecream
   )

When redefining the same as named law (as shown in the below example) you will receive matches for both sections.

.. code-block:: shell
   :caption: Example 10 - Named law example
   :emphasize-lines: 1

   Law flavored_icecream:
   (
       (
            (type: "vanilla")
            or
            (type: "chocolate")
            or
            (type: "strawberry")
       )
       (text: "icecream")
   )

   Law
       - package: "found person only looking for some quantity of icecream"
   (
       (text: "we")
       (text: "want")
       $flavored_icecream
   )


Callbacks and Labels
--------------------

Hammurabi also makes it easy to work with the actual matches. We support both
retrieval of data through labels and defining a custom action to be executed on match.

**Definitions:**

- ``<label> ->`` is the syntax that defines a label. It can be added to any element of the rule. Hammurabi will return the (start, end) offsets of the label within the original sequence in the match object.

- ``- callback: "<callback_name>"`` is the syntax used to attach a callback to a ``Law``, ``named Law`` or ``Var``. The ``<callback_name>`` string needs to match the key in the (key, function) dictionary that is passed in during the construction of the engine.

.. code-block:: shell
   :caption: Example 11 - Labels and callbacks
   :emphasize-lines: 3, 15

   Law flavored_icecream:
   (
       flavour -> (
            (type: "vanilla")
            or
            (type: "chocolate")
            or
            (type: "strawberry")
       )
       (text: "icecream")
   )

   Law
       - package: "found person only looking for some quantity of icecream"
       - callback: "handle_icecream_van"
   (
       (text: "we")
       (text: "want")
       $flavored_icecream
   )





