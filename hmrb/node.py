import logging
import operator
from typing import Any, Dict, Callable, Iterator, List, Optional, Tuple, Union

from hmrb.protobuffer import Labels, Match, Responses

try:
    import re2 as re
    import re as re_fallback
except ImportError:
    logging.warning("Google RE2 not available. Falling back to Python RE.")
    import re  # type: ignore

try:
    from collections.abc import Mapping, Set, Sequence  # noqa
except ImportError:
    from collections import Mapping, Set, Sequence  # noqa


def _recurse(obj: Any, map_fn: Callable) -> Any:
    """
    based on https://github.com/pcattori/maps
    Handles recursion within FrozenMap
    """
    if isinstance(obj, (bool, int, float, complex, str)):
        return obj

    cls = type(obj)
    if isinstance(obj, Mapping):
        return map_fn(**cls((k, _recurse(v, map_fn=map_fn)) for k, v in obj.items()))
    if isinstance(obj, (Sequence, Set)):
        return tuple(cls(_recurse(v, map_fn=map_fn) for v in obj))
    return obj


class FrozenMap(Mapping):
    """
    based on https://github.com/pcattori/maps
    Creates a hashable from any object using frozensets

    """

    @classmethod
    def recurse(cls, obj: Any) -> Any:
        return _recurse(obj, map_fn=cls)

    def __init__(self, *args: Any, **kwargs: Any):
        self._data = dict(*args, **kwargs)
        self._hash: Optional[int] = None

    def __getitem__(self, key: Any) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash(frozenset(self.items()))
        return self._hash


def make_key(obj: Any) -> int:
    """
    Args:
        obj (any)  :   any type of nested / unnested object

    Returns: (int) created from the hash of the FrozenMap object

    Notes: Python's hash() is inconsistent across processes/runs.
    """
    return hash(FrozenMap.recurse(obj))


class BaseNode:
    """
    Class for handling nodes

    BaseNodes is an atomic element of our data structure. Each token is handled
    by a separate BaseNode (or one of its subclasses). The BaseNode is designed
    to build itself in a recursive manner through the consume method from a
    list of dict rules. It handles the matching of a list of incoming tokens
    through the BaseNode call method.

    Args:
        data (dict) : data associated with the node (optional: None)

    Public methods:
        consume     : handles the building of the data structure from a rule
        __call__    : handles the matching of incoming data
    """

    def __init__(self, data: Optional[Dict] = None):
        self.labels = data.get("_", {}).pop("labels", set()) if data else set()
        self.var_end = data.get("_", {}).pop("var_end", False) if data else False
        self.block_length = data.get("_", {}).pop("block_length", 1) if data else 1
        if data and not data.get("_"):
            data.pop("_", None)
        self.data = data if data else {}
        self.children: Dict = {}
        self.child_attribute_index: Dict = {}
        self.children_keys: set = set()
        self.call_order: list = []
        self.min_length = 1
        self.min_run = 1
        self.runs = 0
        self.anchor: Union[None, int] = None

    @staticmethod
    def _make_node_key(token: Dict) -> Tuple[frozenset, int]:
        """
        Creates a hashable dictionary key from a dict token

        Args:
            token (dict)  :   a token dictionary

        Returns: (frozenset, int) created from the list of (key, value) tuples
                 (sorted by default) and hash of data items

        """
        return (
            frozenset(sorted(token["key"].items())),
            make_key(token.get("data")),
        )

    @staticmethod
    def get_att(token: Any, att_name: str) -> Any:
        """
        Retrieves the value of a token attribute regardless of whether it is a
        dictionary or a normal object.

        Args:
            token (Any):        : target token
            att_name (str):     : attribute name

        Returns:
            response (Any)      : Value of the target attribute
        """
        if isinstance(token, dict):
            return token.get(att_name)
        try:
            return operator.attrgetter(att_name)(token)
        except AttributeError:
            return None

    def _build_child(self, child_key: Tuple[frozenset, int], child: "BaseNode") -> None:
        """
        Adds new child to the children of BaseNode. Updates call order
        and attribute index with the new child.

        Args:
            child_key (frozenset)   :  a hashable identifier for new child
            child (BaseNode)        :  new child BaseNode object
        """
        self.children[child_key] = child
        for key, value in child_key[0]:
            if key not in self.child_attribute_index:
                self.child_attribute_index[key] = {}
            if value not in self.child_attribute_index[key]:
                self.child_attribute_index[key][value] = set()
            self.child_attribute_index[key][value].add(child_key)
        self.call_order = list(set(self.child_attribute_index.keys()))
        self.children_keys.add(child_key)

    def optimise_call_order(self) -> None:
        raise NotImplementedError()

    def _consume_child(
        self, next_rule_token: Dict, rule: List[Dict], vars: Dict, sets: Dict
    ) -> None:
        # child_key needs to exclude var_end from underscore
        var_end = next_rule_token.get("data", {}).get("_", {}).pop("var_end", False)
        if next_rule_token.get("data") and not next_rule_token["data"].get("_"):
            next_rule_token["data"].pop("_", None)
            if not next_rule_token["data"]:
                next_rule_token.pop("data")
        child_key = self._make_node_key(next_rule_token)
        child = self.children.get(child_key)
        if not child:
            child = BaseNode(data=next_rule_token.get("data"))
            self._build_child(child_key, child)
        child.var_end |= var_end
        rest = rule[1:]
        child.consume(rest, vars, sets)

    def _consume_var(
        self, next_rule_token: Dict, rule: List[Dict], vars: Dict, sets: Dict
    ) -> None:
        var_handle_key: int = next_rule_token["vars"][0].get("REF")
        var_min_length: int = next_rule_token["vars"][0]["LENGTH"]
        var_min: int = next_rule_token["vars"][0].get("MIN", 1)
        var_max: int = next_rule_token["vars"][0].get("MAX", 1)
        data: Dict = next_rule_token.get("data", {})
        var_key = make_key(next_rule_token)
        var = self.children.get(var_key)
        if not var:
            var_handle: "BaseNode" = vars[var_handle_key]
            var = varNode(var_handle, data, var_min_length, var_min, var_max)
        self.children[var_key] = var
        self.children_keys.add(var_key)
        rest = rule[1:]
        var.consume(rest, vars, sets)

    def _consume_regex(
        self, next_rule_token: Dict, rule: List[Dict], vars: Dict, sets: Dict
    ) -> None:
        regex_key = make_key(next_rule_token)
        child = self.children.get(regex_key)
        if not child:
            child = RegexNode(next_rule_token)
        self.children[regex_key] = child
        self.children_keys.add(regex_key)
        rest = rule[1:]
        child.consume(rest, vars, sets)

    def _consume_set(
        self, next_rule_token: Dict, rule: List[Dict], vars: Dict, sets: Dict
    ) -> None:
        set_attributes: Dict = {}
        for key, value in next_rule_token["key"].items():
            if isinstance(value, list):
                value = {item for set_index in value for item in sets[set_index]}
            else:
                value = set(value)
            set_attributes[key] = value
        data = next_rule_token.get("data", {})
        set_key = make_key((set_attributes, data))
        child = self.children.get(set_key)
        if not child:
            child = SetNode(set_attributes, data)
        self.children[set_key] = child
        self.children_keys.add(set_key)
        rest = rule[1:]
        child.consume(rest, vars, sets)

    def consume(self, rule: List[Dict], vars: Dict, sets: Dict) -> None:
        """
        Builds internal representation from list of rules

        Implementation: Recursively handles the construction of the internal
                        tree structure. Passes token to the appropriate
                        BaseNode class/subclass for handling.
                        If an equivalent node already exists, the remaining
                        tokens of the rules are passed to that node. If no
                        such node exists a new node is added to the children
                        of the current node.

        Args:
            rule (List(dict)) :   list of token rule token dictionaries
            vars (dict)      :   dict of all varHandle objects created
        """
        if not rule:
            return
        next_rule_token = rule[0]
        if "vars" in next_rule_token:
            self._consume_var(next_rule_token, rule, vars, sets)
        elif any(
            [
                isinstance(value, dict) and "regex" in value.keys()
                for value in next_rule_token["key"].values()
            ]
        ):
            self._consume_regex(next_rule_token, rule, vars, sets)
        elif any(
            [isinstance(value, list) for key, value in next_rule_token["key"].items()]
        ):
            self._consume_set(next_rule_token, rule, vars, sets)
        else:
            self._consume_child(next_rule_token, rule, vars, sets)

    def _match(self, token: Dict) -> set:
        """
        (private) Handles the matching of a single token dictionary with
        the current nodes children.

        Implementation: TODO:

        Notes: In the case of missing attribute att_name, att_value is None
               and all children with att_name are removed from the matches

        Args:
            token (dict)  :   dict of (attribute, values) of a single token
        """
        matched_children: set = self.children_keys.copy()
        for att_name in self.call_order:
            token_value: Union[str, int, float, bool] = self.get_att(token, att_name)
            neg_att_values: Dict = dict(self.child_attribute_index[att_name])
            neg_att_values.pop(token_value, None)
            if neg_att_values:
                matched_children = matched_children - set.union(
                    *neg_att_values.values()
                )
            if not matched_children:
                break
        return matched_children

    def __call__(self, pattern: List[Dict], depth: int = 0) -> Union[Responses, Match]:
        """
        Matches internal representation with list of pattern tokens

        Implementation: Recursively handles the matching of the internal
                        tree structure. It checks if any of the children
                        of the current node matches the first token of
                        pattern. For each successfully matched child, it hands
                        over the remaining parts of the pattern.
                        This continues until no more pattern exists (partial
                        or subset match of a longer rule) or a node has no
                        longer children (complete match of a rule with
                        potentially longer pattern) or a node has no optional
                        children.

        Args:
            pattern (list)  :   list of token dictionaries with attributes
            depth (int)     :   integer tracking the depth of the current
                                __call__ in the call stack.

        Returns:
            response (list) :   list of tuples where each tuple is of type
                                (dict, depth) where a rule has been matched
                                for the given input pattern.
        """
        protobuf = Match(self.data, depth=depth)
        # end of input or in leaf node
        if not pattern or not self.children:
            # Add labels if exists except if this is a var node with no runs
            if (self.labels and not isinstance(self, varNode)) or (
                self.labels and isinstance(self, varNode) and not self.runs == 0
            ):
                # Labels are offset if anchor is set i.e. self is var_node
                protobuf += Labels(
                    self.labels,
                    depth,
                    (depth - self.anchor) if self.anchor is not None else 1,
                )
            if not isinstance(protobuf, Responses):
                # Capture depth in leaf node of var with no data
                protobuf.set_depth(depth)
            return protobuf
        if self.var_end and not protobuf.active:
            # Capture depth of leaf node with no data but children i.e. merged
            protobuf.set_depth(depth)
        next_token, rest = pattern[0], pattern[1:]
        matches = self._match(next_token)
        for match in matches:
            child: BaseNode = self.children[match]
            if isinstance(child, (varNode, SetNode, RegexNode)):
                # post-call pattern matching (slow) i.e. inside the Node
                protobuf += child(pattern, depth=depth)
            else:
                # pre-call pattern matching (fast) i.e. inside self._match
                protobuf += child(rest, depth=depth + 1)
        if self.labels:
            protobuf += Labels(
                self.labels,
                depth,
                (depth - self.anchor) if self.anchor is not None else 1,
            )
        return protobuf


class varNode(BaseNode):
    """
    Class for var nodes

    varNode is a subclass of BaseNode designed to efficiently handling
    the reuse of the same node structure (macros). The varNode wraps around
    a BaseNode object (varHandle) to support shared objects and
    the logical repitition of executions.
    The remaining parts are passed to its super BaseNode consume. In this way,
    we have a clear distinction between repeated/seperated section and
    sections that follow the repeated parts.

    Matching is done in a similar two step process. First, the incoming pattern
    is passed to the varHandle structure var_handle returning depths of
    successfull matches. Depending on parameters of the varNode, it tries to
    match the varHandle multiple times. The remaining unmatched
    tokens are passed to the children "outer" structure for matching.
    In case, min_run is 0 it also passes the original input to the "outer"
    structure.

    Args:
        var_handle (BaseNode)  :  shared BaseNode object that becomes the
                                   "inner" structure of the varNode
        data (dict)             :  data object that is returned if the
                                   varNode is matched.
        min_length (int)        :  precomputed minimum length of the inner
                                   structure. Used to determine if enough
                                   input tokens are left to do another loop.
        min_run (int)           :  minimum runs of the inner structure. If
                                   set to 0 the inner structure is optional
                                   (default 1).
        max_run (int)           :  maximum runs of the inner structure
                                   (default 1).

    Public methods:
        __call__    : handles the matching of incoming list of tokens by
                      first recursing through the shared inner varHandle
                      and then by recursing the remaining unmatched tokens
                      through the super BaseNode object ("outer").
    """

    def __init__(
        self,
        var_handle: BaseNode,
        data: Dict,
        min_length: int,
        min_run: int,
        max_run: int,
    ):
        super().__init__(data)
        self.var_handle = var_handle
        self.min_length = min_length
        self.min_run = min_run
        self.max_run = max_run

    def __call__(self, pattern: list, depth: int = 0) -> Union[Responses, Match]:
        """
        Matches both inner and outer parts of the varNode with list of
        pattern tokens

        Implementation: tries to loop the inner part of the varNode until
                        maximum run or until it no longer matches.
                        If the inner part is optional pass the entire
                        pattern to the outer part.
                        If the inner part was completed less than the
                        minimum amount of runs specified returns an empty
                        list.
                        Passes everything that hasn't been matched by the inner
                        structure to the outer BaseNode.

        Args:
            pattern (list)  :   list of token dictionaries with attributes
            depth (int)     :   integer tracking the depth of the current
                                __call__ in the call stack.

        Returns:
            response (list) :   list of tuples where each tuple is of type
                                (data dict, depth) where a rule has been
                                matched for the given input pattern.
        """
        protobuf = Responses()
        # Capture start of variable
        self.anchor = depth
        self.runs = 0
        for _ in range(self.max_run):
            proto_part = self.var_handle(pattern, depth)
            if (isinstance(proto_part, Match) and proto_part.active) or (
                proto_part.depth_reached - depth >= self.min_length
            ):
                # Variable is successfully matched for a single loop
                max_depth = proto_part.get_depth()
                proto_part.set_start(self.anchor)
                protobuf += proto_part
                rest = pattern[(max_depth - depth) :]
                self.runs += 1
                depth = max_depth
                # Avoid greedy matching and execute after each successfull loop
                if self.min_run <= self.runs:
                    protobuf += super().__call__(rest, depth)
                # Continue only if enough tokens are left
                if len(rest) >= self.min_length:
                    pattern = rest
                    continue
            break
        if (self.runs < self.min_run) or (
            self.anchor + self.block_length > protobuf.depth_reached
        ):
            # Variable unsuccessfully matched / required depth is not reached
            proto_part.active = False
            proto_part.depth_reached = 0
            return proto_part
        return protobuf


class SetNode(BaseNode):
    """
    Class for Set nodes

    SetNode is a subclass of BaseNode designed to efficiently handling the
    matching of sets.

    Args:
        rule_set (dict)         :  global dictionary of sets to check
        data (dict)             :  data object that is returned if the
                                   SetNode is matched.

    Public methods:
        __call__    : handles the matching of incoming list of tokens by
                      checking if the token is present in the rule_set.
    """

    def __init__(self, rule_set: Dict, data: Dict):
        super().__init__(data)
        self.set = rule_set

    def __call__(self, pattern: List[Dict], depth: int = 0) -> Union[Responses, Match]:
        """
        Matches a predefined set of tokens with list of pattern tokens

        Args:
            pattern (list)  :   list of token dictionaries with attributes
            depth (int)     :   integer tracking the depth of the current
                                __call__ in the call stack.

        Returns:
            response (list) :   list of tuples where each tuple is of type
                                (data dict, depth) where a rule has been
                                matched for the given input pattern.
        """
        depth += 1
        protobuf = Match(self.data, depth=depth)
        if not pattern:
            protobuf.active = False
            return protobuf
        next_token, rest = pattern[0], pattern[1:]
        # Actual set matching
        for key in self.set.keys():
            if self.get_att(next_token, key) not in self.set[key]:
                # Set matching unsuccessfull
                protobuf.active = False
                return protobuf
        if any([child.min_run for child in self.children.values()]) and not rest:
            # Set matching unsuccessfull if no further input but node has
            # non-optional children
            protobuf.active = False
            return protobuf
        elif self.children:
            protobuf += super().__call__(rest, depth)
            if not protobuf.active:
                return protobuf
        if self.labels:
            protobuf += Labels(self.labels, depth)
        protobuf.set_depth(depth)
        return protobuf


class StarNode(BaseNode):
    pass


class RegexNode(BaseNode):
    def __init__(self, token: Dict):
        super().__init__(token.get("data"))
        self.regex: Dict = {}
        for key, value in token["key"].items():
            regex_raw = value["regex"] if isinstance(value, dict) else value
            try:
                regex_compiled = re.compile(regex_raw)
            except Exception:
                regex_compiled = re_fallback.compile(regex_raw)
            finally:
                self.regex[key] = regex_compiled

    def __call__(self, pattern: List[Dict], depth: int = 0) -> Union[Responses, Match]:
        depth += 1
        protobuf = Match(self.data, depth=depth)
        if not pattern:
            protobuf.active = False
            return protobuf
        next_token, rest = pattern[0], pattern[1:]
        # Actual regex matching
        for key, value in self.regex.items():
            if not self.get_att(next_token, key) or not value.match(
                self.get_att(next_token, key)
            ):
                # Regex matching unsuccessfull
                protobuf.active = False
                return protobuf
        if any([child.min_run for child in self.children.values()]) and not rest:
            # Regex matching unsuccessfull if no further input but node has
            # non-optional childrenn
            protobuf.active = False
            return protobuf
        elif self.children:
            protobuf += super().__call__(rest, depth)
            if not protobuf.active:
                return protobuf
        if self.labels:
            protobuf += Labels(self.labels, depth)
        protobuf.set_depth(depth)
        return protobuf
