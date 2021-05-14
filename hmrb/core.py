from copy import deepcopy
import logging
import os
from typing import Any, Callable, Dict, ItemsView, List, Optional, Tuple, Union

from .lang import Grammar, unique
from .node import BaseNode
from .protobuffer import Responses

if os.environ.get("DEBUG") == "1":
    logging.getLogger().setLevel(logging.INFO)


class Core:
    """
    Class handling the main functions surrounding the rule engine

    Args:
        callbacks (dict):   dictionary of callback functions to execute
                            following a successfull call.
        sort_length (bool): sort match results according to span length in
                            ascending order (affects callback execution as
                            well.)

    Public methods:
        load        : add list of rules to engine
        __call__    : match list of input dicts with internal rules

    """

    def __init__(
        self,
        callbacks: Optional[Dict] = None,
        sets: Optional[Dict] = None,
        sort_length: bool = False,
    ):
        self.root = BaseNode()
        self.callbacks = callbacks if callbacks else {}
        self.sets = sets if sets else {}
        self.sort_length = sort_length
        self.vars: Dict = {}

    def _load(self, rules: List[List[Dict]], vars: List[List[Dict]]) -> None:
        """
        Adds list of rules to the engine

        Implementation: passes rules to the root BaseNode of the class
                        sequentially

        Args:
            rules (list) : list of rules to add to root node
            vars (list) : list of shared varHandle objects to use
        """
        for var in vars:
            for var_part in var:
                var_key = var_part[0]["vars"][0]["DEF"]
                del var_part[0]["vars"][0]
                if not var_part[0]["vars"]:
                    del var_part[0]["vars"]
                var_handle = self.vars.get(var_key)
                if not var_handle:
                    self.vars[var_key] = BaseNode()
                self.vars[var_key].consume(var_part, self.vars, self.sets)
        for rule in rules:
            self.root.consume(rule, self.vars, self.sets)

    def load(self, inputs: str) -> None:
        """
        Adds rules to the engine.

        Args:
            inputs (list) : list of rules in dialect
        """
        _grammar = deepcopy(inputs)
        bab = Grammar(_grammar, self.vars)
        vars, rules = list(bab.vars.values()), list(unique(bab.laws))
        self._load(rules=rules, vars=vars)
        logging.info(f"load: {len(vars) + len(rules)} rule(s) loaded")

    def _match(
        self, spans: List[Tuple[int, list]]
    ) -> Union[
        List[Tuple[Tuple[int, int], List[Dict]]],
        ItemsView[Tuple[int, int], List[Dict]],
    ]:
        """
        Takes a list of spans and executes matching by passing each
        to the root node.

        Args:
            spans (list)    :  list of spans to match

        Returns:
            (list)          :  list of tuples containing match results
        """
        protobuf = Responses()
        for start, span in spans:
            protobuf += self.root(span, depth=start)
            protobuf.set_start(start)
        return protobuf.format(self.sort_length)

    @staticmethod
    def default_callback(input_: list, span: slice, data: Dict) -> None:
        pass

    def _execute(
        self,
        responses: Union[
            List[Tuple[Tuple[int, int], List[Dict]]],
            ItemsView[Tuple[int, int], List[Dict]],
        ],
        input_: Any,
    ) -> None:
        if not self.callbacks:
            return
        for span, matches in responses:
            for data in matches:
                callback_name = data.get("callback")
                logging.info(f"_execute: callback <{callback_name}>")
                callback = self.callbacks.get(callback_name, Core.default_callback)
                try:
                    callback(input_, slice(*span), data)
                except Exception as ex:
                    logging.error(
                        f"_execute: callback <{callback_name} failed with {ex}"
                    )

    def __call__(
        self, input_: List[Dict]
    ) -> Union[
        List[Tuple[Tuple[int, int], List[Dict]]],
        ItemsView[Tuple[int, int], List[Dict]],
    ]:
        """
        Matches a list of input units to the parsed rules within the engine.
        units can be dictionaries or other objects. In the case of the latter
        object attributes are considered unit attributes, while for the former
        those are encoded in the regular key-value pairs.

        Implementation: handles creating the spans internally. Since the
                        BaseNode implementation is capable of handling
                        rules in passing, only the start of the spans is
                        needed to be iterated.

        Args:
            input_ (list) : list of input text to match to rules

        Returns:
            (list)      : list of tuples from matched rules in format
                          (span start,
                          list of tuples (rule data, depth from start))
        """
        spans: List[Tuple[int, list]] = [
            (start, input_[start:]) for start in range(len(input_))
        ]
        protobuf = self._match(spans)
        logging.info(f"call: {len(protobuf)} match(es)")
        self._execute(protobuf, input_)
        return protobuf


def _default_map(doc: Any) -> Any:
    return doc


class SpacyCore(Core):
    """
    Class wrapping the `Core` object into a spaCy component.

    Args:
        callbacks (dict):   dictionary of callback functions to execute
                            following a successfull call.
        sort_length (bool): sort match results according to span length in
                            ascending order (affects callback execution as
                            well.)

    Public methods:
        load        : add list of rules in the engine
        __call__    : match a spaCy Document or Span against the rule set
    """

    name = "hmrb"

    def __init__(
        self,
        callbacks: Optional[Dict] = None,
        sets: Optional[Dict] = None,
        map_doc: Callable = _default_map,
        sort_length: bool = False,
    ):
        super().__init__(callbacks=callbacks, sets=sets, sort_length=sort_length)
        self.map_doc = map_doc

    def __call__(self, doc: Any) -> Any:
        """
        Matches a spaCy Document or Span object against a set of parsed rules.

        Note:           Underscore attributes need to be specified with a
                        leading underscore and dot notation in the grammar
                        rules to be available here. For example, define an
                        attribute like `_.CITY: "New York, NY"` if you want to
                        peen into an underscore attribute called CITY.

        Implementation: handles creating the spans internally. Since the
                        BaseNode implementation is capable of handling
                        rules in passing, only the start of the spans is
                        needed to be iterated.

        Args:
            doc (Any)   : spaCy document or span

        Returns:
            (Any)       : processed spaCy document or span
        """
        mapped_doc = self.map_doc(doc)
        spans: List[Tuple[int, list]] = [
            (start, mapped_doc[start:]) for start in range(len(doc))
        ]
        protobuf = self._match(spans)
        logging.info(f"call: {len(protobuf)} match(es)")
        super()._execute(protobuf, doc)
        return doc


try:
    from spacy.language import Language
    from spacy import registry

    def spacy_factory(
        nlp: object,
        name: str,
        callbacks: dict,
        sets: dict,
        map_doc: str,
        sort_length: bool,
        rules: str,
    ) -> SpacyCore:
        map_fn = registry.get(*map_doc.split("."))
        callbacks = {
            key: registry.get(*value.split(".")) for key, value in callbacks.items()
        }
        core = SpacyCore(callbacks, sets, map_fn, sort_length)
        core.load(rules)
        return core

    Language.factory(
        "hmrb",
        default_config={
            "callbacks": {},
            "sets": {},
            "map_doc": _default_map,
            "sort_length": False,
            "rules": "",
        },
        func=spacy_factory,
    )
except (ImportError, AttributeError):
    logging.debug("disabling support for spaCy 3.0+")
