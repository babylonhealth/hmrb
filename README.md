# Hammurabi [hmrb] 🏺

Upholds the law for sequences.

### 1. Installation

To begin, simply install the package from PyPI:
```shell
$ pip install hmrb
```

### 2. Documentation

Documentation is available at https://hmrb.readthedocs.io.
Instructions to build and run locally:

```shell
$ pip install -r doc_requirements.txt
$ pip install -e .
$ make docs
$ make html
```

### 3. Definitions

Hammurabi works as a rule engine to parse input using a defined set of rules.
It uses a simple and readable syntax to define complex rules to handle phrase matching.

The engine takes as input any type of sequences of units with associated attributes.
Our usecase currently is to handle language annotation, but we expect it to work
equally well on a variety of complex sequence tasks (time-series, logging).

The attributes do not have to be consistent across all units or between the
units and the grammar. The lack of an attribute is simply considered as a
non-match.

Features:
- Attribute level rule definitions using key-values pairs
- Efficient matching of sequence using hash tables with no limit on length
- Support for nested boolean expressions and wildcard operators similar to regular expressions
- Variables can be side-loaded and reused throughout different rule sets
- User-defined rule-level callback functions triggered by a match
- Labels to tag and retrieve matched sequence segments

#### 3.1 Writing Rules

Rules are defined in a custom syntax. The syntax was defined
with the aim to keep it simple to read, but expressive at the same time.

The basic components are `Law` and `Var`. Both `Law` and `Var` declare a sequence of attributes.
However, while a `Law` can be matched on its own, a `Var` defines a sequence that is likely to be reused (a.k.a macros) within `Laws` or other `Vars`. Since a `Var` is never matched on its own, it requires a name and only exists as part of a rule body.

The example below shows a fictional case of capturing strings such as `"head is hurting"` or `"head hurts"`.
Note that the variable `is_hurting` cannot match *is hurting*.

```
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
```

#### 3.2 Input format

Hammurabi requires a sequence of attribute dictionaries as input.
It will attempt to find matching rules in the given input.
The most widely-used input format is a simple JSON list of dictionaries:

```json
[
    {"orth": "My", "lemma": "my", "pos": "PRON"},
    {"orth": "head", "lemma": "head", "pos": "NOUN"},
    {"orth": "hurts", "lemma": "hurt", "pos": "VERB"}
]
```

#### 3.3 Callbacks, labels and data

When a rule matches an input, the following information is returned as a
"match": the original input, a slice representing the span it was triggered on
and all the data (labels, callback function and attributes) based on
the matched rule. There are two ways to act upon these matches.
You can use delegate the execution of the callback function to `hammurabi`
or you can do the execution yourself. The former is done by passing the input
to the `__call__` method, which executes callback functions right after
the matches are returned. However, this has a slight drawback, which is that
your callback functions need to adhere to a specific signature to allow them
to be called correctly from inside `hammurabi`.


```python
# callback function called from inside hammurabi
def mark_headache(input_, slice_, data):
    print(f'I am acting on span "{input_[slice_]}" with data "{data}".')
```

The callback functions are passed down as a mapping between their string alias
used in the rule grammar, i.e. how do you refer to it in the `callback`
attribute of the law that was matched.

```python
callbacks = {
    'mark_headache': mark_headache
}
```

### 4. Usage

#### 4.1  Worked-out example with callbacks

The rule engine is initialized through a `Core` instance. We can pass various optional
objects to the constructor of `Core` (callbacks, sets) that we intend to later use in our rules.

The `Core.load` method adds rules to the engine.
It is possible to load multiple rule files sequentially.

The `Core` library usage pattern allows the user to either get the
matches and act on them in a different place through the use of the `match`
method, or to pass a callback mapping and allow `hammurabi` to execute the
callbacks through the use of the `__call__` method.

```python
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
#      'junk_attribute': 'some string'
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
```

You can find this worked out example under `examples/readme.py`.

#### 4.2 spaCy component example (NLP)

The spaCy component class `SpacyCore` extends the internal execution shown
above to allow the use of `hammurabi` in spaCy natural language processing
pipelines. Optionally a function (jsonify) can be passed into the SpacyCore
to convert the `Token` objects to JSON.

```python
import spacy
from hmrb.core import SpacyCore

# This will be used to turn a span (subsequence) of a spaCy document object
# into a list of dictionaries input representation.
def jsonify(span):
    jsn = []
    for token in span:
        jsn.append({
            'orth': token.orth_,
            'lemma': token.lemma_,
            'pos': token.pos_,
            'tag': token.tag_
        })
    return jsn

hmb = SpacyCore(callbacks={'mark_headache': mark_headache}, map_doc=jsonify,
                sort_length = True)
hmb.load(grammar)

nlp = spacy.load('en_core_web_sm')
nlp.add_pipe(hmb, last=True)
nlp('My head hurts')
#  I am acting on span "head hurts" with data
#  "{
#       'package': 'headache',
#       'callback': 'mark_headache',
#       'junk_attribute': 'pointless strings I am passing down because I can'
#  }"
```

### 5. Tests & debugging

To run tests use (this inclused setting the correct `HASH_SEED`):
```shell
$ make tests
```

To display additional information for debugging purposes use `DEBUG=1` environment variable.
```shell
$ DEBUG=1 python example.py
```

### 6. Maintainers

<!-- HTML:START -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/bodak"><img src="https://avatars3.githubusercontent.com/u/6807878?v=4" width="100px;" alt=""/><br /><sub><b>Kristian Boda</b></sub></a></td>
    <td align="center"><a href="http://sasho.io"><img src="https://avatars2.githubusercontent.com/u/1086604?v=4" width="100px;" alt=""/><br /><sub><b>Sasho Savkov</b></sub></a></td>
    <td align="center"><a href="https://github.com/mlehl88"><img src="https://avatars2.githubusercontent.com/u/17163719?s=460&u=683f6b5583ed3df64b0e9812f7ec6bdd19b94a5e&v=4" width="100px;" alt=""/><br /><sub><b>Maria Lehl</b></sub></a></td>
  </tr>
</table>
<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- HTML:END -->
