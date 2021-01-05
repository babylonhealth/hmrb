import re
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple, Union

from addict import Dict as addict

from hmrb.node import make_key

# REGEXES
NAME_PAT = r"(?:[a-zA-Z]|_+[a-zA-Z0-9.-])[a-zA-Z0-9_.-]*"

REF_RE = re.compile(r"^\$[a-zA-Z_][a-zA-Z0-9_-]*$")
VAR_RE = re.compile(f"Var +(?P<name>{NAME_PAT}):")
LAW_RE = re.compile(f"Law( +(?P<name>{NAME_PAT}))?:")

# unit validation
Q_VALUE_PAT = r'"(?:[^"]|\\")*(?:(?<!\\)"|\\\\")'
REGEX_PAT = r"regex\(\s*{}\s*\)".format(Q_VALUE_PAT)
BOOL_PAT = r"(?:[tT]rue|[fF]alse)"
INT_PAT = r"(?:-?(?:0|(?:[1-9]\d*)))"
FLOAT_PAT = r"(?:-?(?:0|(?:[1-9]\d*)))\.\d*"
REGEX_RE = re.compile(f"^{REGEX_PAT}$")
BOOL_RE = re.compile(f"^{BOOL_PAT}$")
INT_RE = re.compile(f"^{INT_PAT}$")
FLOAT_RE = re.compile(f"^{FLOAT_PAT}$")
UNIT_VALUE_PAT = r"(?:{}|{}|{}|{}|{})".format(
    REGEX_PAT, Q_VALUE_PAT, BOOL_PAT, FLOAT_PAT, INT_PAT
)
UNIT_NAMED_VALUE_PAT = r"(?P<att_value>{}|{}|{}|{}|{})".format(
    REGEX_PAT, Q_VALUE_PAT, BOOL_PAT, FLOAT_PAT, INT_PAT
)
UNIT_RE = re.compile(
    r"\s*\("
    r"\s*{}\s*:\s*{}\s*"
    r"(,\s*{}\s*:\s*{}\s*)*"
    r"\)\s*".format(NAME_PAT, UNIT_VALUE_PAT, NAME_PAT, UNIT_VALUE_PAT)
)
# unit parsing
UNIT_ATTS_RE = re.compile(
    r"(?P<att_name>{})\s*:" r"\s*{}".format(NAME_PAT, UNIT_NAMED_VALUE_PAT)
)

# signature line parsing
VAR_SIGN_RE = re.compile("^[\t ]*Var +[a-zA-Z_][a-zA-Z0-9_-]*: *\n?$")
LAW_SIGN_RE = re.compile("^[\t ]*Law( +[a-zA-Z_][a-zA-Z0-9_-]*)?: *\n?$")
LAW_ATTS_RE = re.compile(f'\\s*-\\s(?P<name>{NAME_PAT}): *"(?P<value>[^\n]*)"')
EMPTY_BLOCK_RE = re.compile(r"^\s*(\s*[()\s\n\r]*\s*)\s*$")
OPTION_RE = re.compile(r"\s*optional(\s*not)?\s*")
LABEL_RE = re.compile(f"^{NAME_PAT}$")
ZERO_PLUS_RE = re.compile(r"\s*(zero|0) or more(\s*not)?\s*")
ONE_PLUS_RE = re.compile(r"\s*(one|1) or more(\s*not)?\s*")
AT_LEAST_RE = re.compile(r"\s*at least (?P<min>\d+)(\s*not)?\s*")
AT_MOST_RE = re.compile(r"\s*at most (?P<max>\d+)(\s*not)?\s*")
RANGE_RE = re.compile(r"\s*(?P<min>\d+) to (?P<max>\d+)(\s*not)?\s*")


INF = 10 ** 10
_TYPES = {
    "?": (0, 1),
    "*": (0, INF),
    "+": (1, INF),
}


class Types(Enum):
    """
    Types of segments and items
    """

    VAR = "var"
    LAW = "law"
    BLOCK = "block"
    UNIT = "unit"
    VAR_REF = "var_ref"


class Unit:
    """
    Represents a group of attribute constraints that form a rule unit. Units
    are typically members of a block.

    Args:
        atts [dict]     -- unit attributes
        neg [bool]      -- negated
        min [int]       -- minimum number of matches
        max [int]       -- maximum number of matches
        label [str]     -- unit label
    """

    def __init__(
        self, atts: Dict, neg: bool, min_: int, max_: int, label: Optional[str]
    ) -> None:
        self.atts: Dict = atts
        self.neg: bool = neg
        self.min: int = min_
        self.max: int = max_
        self.label: Optional[str] = label


def unique(sequence: list) -> Iterator:
    uniques: set = set()
    for value in sequence:
        if str(value) in uniques:
            continue
        uniques.add(str(value))
        yield value


class Ref:
    """
    Represents a reference to a variable.

    Args:
        ref [str]       -- variable reference
        neg [bool]      -- negated
        min [int]       -- minimum number of matches
        max [int]       -- maximum number of matches
        label [str]     -- reference label
    """

    def __init__(
        self, ref: str, neg: bool, min_: int, max_: int, label: Optional[str]
    ) -> None:
        self.ref: str = ref
        self.neg: bool = neg
        self.min: int = min_
        self.max: int = max_
        self.label: Optional[str] = label
        self.var: Optional[Var] = None


class Block:
    """
    Represents a rule block that may be the body or part of the body of a Law
    or a Var.

    Args:
        members [dict]  -- Block members
        neg [bool]      -- negated
        min_ [int]      -- minimum number of matches
        max_ [int]      -- maximum number of matches
    """

    def __init__(
        self,
        members: List,
        vars: Dict,
        neg: bool,
        min_: int,
        max_: int,
        label: Optional[str],
        union: bool = False,
        is_body: bool = False,
    ) -> None:
        self.members: List[Union[Block, Unit, Ref]] = members
        self.union: bool = union
        self.min: int = min_
        self.max: int = max_
        self.neg: bool = neg
        self.label: Optional[str] = label
        self.vars: Dict = vars
        self.parents: List = [[]]
        self.is_body: bool = is_body

    def _add_var(self, children: list, length: int, min_: int, max_: int) -> Any:
        var_key: int = make_key(children)
        if var_key not in self.vars:
            self.vars[var_key] = []
            for var_part in children:
                new_var = deepcopy(var_part)
                if "vars" not in new_var[0]:
                    new_var[0].vars = []
                new_var[0].vars.insert(0, addict({"DEF": var_key, "LENGTH": length}))
                new_var[-1].data._.var_end = True
                self.vars[var_key].append(new_var)
            for p in self.vars[var_key]:
                # block_length is 1 by default and lists are already handled
                if len(p) == 1 or type(p[0]) == list:
                    continue
                p[0].data._.update(addict({"block_length": len(p)}))
        var = addict()
        var.vars = [
            addict({"REF": var_key, "LENGTH": length, "MIN": min_, "MAX": max_})
        ]
        return var

    def _sequence_extend(self, block: "Block") -> None:
        new_parents: list = []
        make_opt: bool = block.min == 0
        # ? The optional arm is handling 0, so other arm is set 1
        block.min = 1 if block.min == 0 else block.min
        make_var: bool = block.max != 1
        for parent in self.parents:
            if make_opt:
                new_parents.append(deepcopy(parent))
            if make_var:
                new_parent = deepcopy(parent)
                min_length = len(min(block.parents, key=len))
                var = self._add_var(block.parents, min_length, block.min, block.max)
                if block.label:
                    var.data._.labels = set([block.label + "_B", block.label + "_E"])
                    block.label = None
                new_parent.append(var)
                new_parents.append(new_parent)
            else:
                for child in block.parents:
                    new_parent = deepcopy(parent)
                    if self.union and not self.is_body:
                        new_parent.append(deepcopy(child))
                    else:
                        new_parent.extend(deepcopy(child))
                    new_parents.append(new_parent)
        self.parents = new_parents

    def _union_extend(self, block: "Block") -> None:
        new_parents = []
        make_opt: bool = block.min == 0
        # ? The optional arm is handling 0, so other arm is set 1
        block.min = 1 if block.min == 0 else block.min
        make_var: bool = block.max != 1
        for parent in self.parents:
            if make_opt:
                new_parents.append(deepcopy(parent))
            for child in block.parents:
                if make_var:
                    inner_part_list = [
                        [inner_part] if not isinstance(inner_part, list) else inner_part
                        for inner_part in deepcopy(child)
                    ]
                    min_length = len(min(child, key=len))
                    new_parent = deepcopy(parent)
                    new_var = self._add_var(
                        inner_part_list, min_length, block.min, block.max
                    )
                    if block.label:
                        new_var.data._.labels = set(
                            [block.label + "_B", block.label + "_E"]
                        )
                    new_parent.append(new_var)
                    new_parents.append(new_parent)
                else:
                    for inner_part in child:
                        new_parent = deepcopy(parent)
                        if isinstance(inner_part, list):
                            if block.label:
                                inner_part[0].data._.labels = set(
                                    [block.label + "_B"]
                                ).union(inner_part[0].data._.labels)
                                inner_part[-1].data._.labels = set(
                                    [block.label + "_E"]
                                ).union(inner_part[-1].data._.labels)

                            new_parent.extend(deepcopy(inner_part))
                        else:
                            if block.label:
                                inner_part.data._.labels = set(
                                    [block.label + "_B", block.label + "_E"]
                                ).union(inner_part.data._.labels)
                            new_parent.append(deepcopy(inner_part))
                        new_parents.append(new_parent)
        block.label = None
        for p in new_parents:
            # block_length is 1 by default and lists are already handled
            if len(p) == 1 or type(p[0]) == list:
                continue
            p[0].data._.update(addict({"block_length": len(p)}))
        self.parents = new_parents

    def _parse_block(self, block: "Block") -> None:
        block.parse()
        if block.union:
            self._union_extend(block)
        else:
            self._sequence_extend(block)
        if block.label:
            for parent in block.parents:
                parent[0].data._.labels = set([block.label + "_B"]).union(
                    parent[0].data._.labels
                )
                parent[-1].data._.labels = set([block.label + "_E"]).union(
                    parent[-1].data._.labels
                )

    def _parse_labeled_element(self, label: str, parent: list) -> None:
        parent[-1].data._.labels = set([label + "_B", label + "_E"]).union(
            parent[-1].data._.labels
        )

    def _parse_unit(self, unit: Unit) -> None:
        make_opt: bool = unit.min == 0
        # ? The optional arm is handling 0, so other arm is set 1
        unit.min = 1 if unit.min == 0 else unit.min
        make_var: bool = unit.max != 1
        optionals: list = []
        for parent in self.parents:
            new_node = addict({"key": unit.atts})
            if make_var:
                ln = 1
                var_key: int = make_key([[new_node]])
                if var_key not in self.vars:
                    new_var = new_node
                    new_var.vars = [addict({"DEF": var_key, "LENGTH": ln})]
                    new_var.data._.var_end = True
                    self.vars[var_key] = [[new_var]]
                new_node = addict(
                    {
                        "vars": [
                            {
                                "REF": var_key,
                                "LENGTH": ln,
                                "MIN": unit.min,
                                "MAX": unit.max,
                            }
                        ]
                    }
                )
            if make_opt:
                optionals.append(deepcopy(parent))
            parent.append(new_node)
            if unit.label:
                self._parse_labeled_element(unit.label, parent)
        self.parents.extend(optionals)

    def _parse_ref(self, ref: Ref) -> None:
        make_opt: bool = ref.min == 0
        # ? The optional arm is handling 0, so other arm is set 1
        ref.min = 1 if ref.min == 0 else ref.min
        optionals: list = []
        for parent in self.parents:
            if ref.ref not in self.vars:
                raise ValueError(f"I can't find {ref.ref}")
            var = self.vars[ref.ref]
            ln = len(min(var, key=len))
            new_node = addict(
                {
                    "vars": [
                        {
                            "REF": ref.ref,
                            "LENGTH": ln,
                            "MIN": ref.min,
                            "MAX": ref.max,
                        }
                    ]
                }
            )
            if make_opt:
                optionals.append(deepcopy(parent))
            parent.append(new_node)
            if ref.label:
                self._parse_labeled_element(ref.label, parent)
        self.parents.extend(optionals)

    def parse(self) -> None:
        for member in self.members:
            if isinstance(member, Block):
                self._parse_block(member)
            elif isinstance(member, Unit):
                self._parse_unit(member)
            elif isinstance(member, Ref):
                self._parse_ref(member)
        self.parents = [parent for parent in self.parents if parent]


class Var:
    """
    Represents a named rule variable segment of a Babylonian grammar.

    Args:
        lines [list]    -- segment lines
    """

    def __init__(self, lines: List, vars: Dict) -> None:
        self.name: Optional[str] = None
        self.body: Optional[Block] = None
        self.vars = vars
        self._parse(lines)

    @staticmethod
    def _parse_name(first_line: str, start: int) -> str:
        m = VAR_RE.match(first_line)
        try:
            return m.group("name")  # type: ignore
        except AttributeError:
            raise ValueError(
                f"Invalid Var signature line: {first_line}" f"(line {start})"
            )

    def _parse(self, lines: List) -> None:
        name_start = lines[0][1]
        self.name = self._parse_name(lines[0][0].strip(), name_start)
        if self.name in self.vars:
            raise ValueError(
                f'Var signature "{self.name}" already in use (line {name_start})'
            )
        body_lines_str = "\n".join(line[0].strip() for line in lines[1:])
        body_start = lines[1][1]
        self.body = parse_block(body_lines_str, vars=self.vars, start=body_start)
        self.body.is_body = True


class Law:
    """
    Represents a rule segment of a Babylonian grammar. It consists of an
    optional name, a list of attributes, and a compulsory body.

    Args:
        lines [list]    -- segment lines
    """

    def __init__(self, lines: List, vars: Dict) -> None:
        self.name: Optional[str] = None
        self.atts: Dict = {}
        self.body: Optional[Block] = None
        self.var_segments: Optional[dict] = None
        self.law_segments: Optional[dict] = None
        self.vars: Dict = vars
        self._parse(lines)

    @staticmethod
    def _parse_name(first_line: str, start: int) -> str:
        m = LAW_RE.match(first_line)
        try:
            return m.group("name")  # type: ignore
        except AttributeError:
            raise ValueError(
                f"Invalid Law signature line: {first_line} " f"(line {start})"
            )

    @staticmethod
    def _parse_atts(lines: List) -> Dict:
        atts = {}
        for line, num in lines:
            m = LAW_ATTS_RE.match(line)
            try:
                atts[m.group("name")] = m.group("value")  # type: ignore
            except AttributeError:
                raise ValueError(f"Incorrect Law attribute: {line} " f"at (line {num})")
        return atts

    @staticmethod
    def _segment_lines(lines: List) -> Tuple[List, List]:
        att_lines = []
        line_idx = 0
        while lines[line_idx][0].strip().startswith("-"):
            att_lines.append(lines[line_idx])
            line_idx += 1
        body_lines = lines[line_idx:]
        return att_lines, body_lines

    def _parse(self, lines: List) -> None:
        name_start = lines[0][1]
        self.name = self._parse_name(lines[0][0].strip(), name_start)
        att_lines, body_lines = self._segment_lines(lines[1:])
        body_lines_str = "\n".join(line[0].strip() for line in body_lines)
        body_start = body_lines[0][1]
        self.atts = self._parse_atts(att_lines)
        self.body = parse_block(body_lines_str, vars=self.vars, start=body_start)
        self.body.is_body = True


class Grammar:
    """
    Represents a Babylonian grammar. It may consist of Var and Law segments.

    Args:
        string [str]    -- grammar string to be parsed
    """

    parser_map = {Types.VAR: Var, Types.LAW: Law}

    def __init__(self, string: str, vars_: Dict) -> None:
        self.segments: List = []
        self.laws: List = []
        # add length helper integers
        self.vars: Dict = {k: [[0] * v.min_length] for k, v in vars_.items()}
        self._build(string)
        self._deploy()

    @staticmethod
    def end_var(parent_end: Any) -> None:
        parent_end.data._.var_end = True

    def _deploy(self) -> None:
        for segment in self.segments:
            handler = segment
            handler.body.parse()
            if isinstance(segment, Law) and not segment.name:
                if segment.atts:
                    for parent in handler.body.parents:
                        parent[-1].data.update(segment.atts)
                self.laws.extend(handler.body.parents)
                self.vars.update(handler.body.vars)
            elif isinstance(segment, Law):
                ln = len(min(handler.body.parents, key=len))
                for parent in handler.body.parents:
                    if "vars" in parent[0]:
                        parent[0].vars.insert(
                            0, addict({"DEF": segment.name, "LENGTH": ln})
                        )
                    else:
                        parent[0].vars = [addict({"DEF": segment.name, "LENGTH": ln})]
                    if segment.atts:
                        parent[-1].data.update(segment.atts)
                    else:
                        self.end_var(parent[-1])
                self.vars[segment.name] = handler.body.parents
                new_law = [
                    [
                        addict(
                            {
                                "vars": [
                                    {
                                        "REF": segment.name,
                                        "LENGTH": ln,
                                        "MIN": handler.body.min,
                                        "MAX": handler.body.max,
                                    }
                                ]
                            }
                        )
                    ]
                ]
                self.laws.extend(new_law)
            elif isinstance(segment, Var):
                ln = len(min(handler.body.parents, key=len))
                for parent in handler.body.parents:
                    if "vars" in parent[0]:
                        parent[0].vars.insert(
                            0, addict({"DEF": segment.name, "LENGTH": ln})
                        )
                    else:
                        parent[0].vars = [addict({"DEF": segment.name, "LENGTH": ln})]
                    self.end_var(parent[-1])
                self.vars[segment.name] = handler.body.parents
        # clean up helper integers
        self.vars = {
            k: v
            for k, v in self.vars.items()
            if not any([isinstance(i[0], int) for i in v])
        }

    @staticmethod
    def _parse_segment_type(line: str) -> Optional[Types]:
        """
        Determines the type of grammar segment: Law or Var.

        Args:
            line:       -- segment lines

        Returns:
            [Types]     -- segment type
        """
        if VAR_SIGN_RE.match(line):
            return Types.VAR
        elif LAW_SIGN_RE.match(line):
            return Types.LAW
        return None

    def _segment(self, string: str) -> Generator:
        """
        Segments the grammar into laws (Law) and variables (Var). Yields
        the type of the segment as well as all the lines.

        Args:
            string:     -- string representation of the segment
        """
        buff: List = []
        segment_start = 1
        type_: Optional[Types] = None
        for i, line in enumerate(string.split("\n"), start=1):
            line_type = self._parse_segment_type(line)
            if line_type is not None:
                if type_ is not None:
                    yield type_, buff
                    segment_start = i + 1
                buff = []
                type_ = line_type
            buff.append((line + "\n", i))
        if buff:
            if type_ is None:
                raise ValueError(
                    f"Most likely missing Var name at " f"line {segment_start}"
                )
            yield type_, buff

    def _map_segments(self, type_: Any) -> Dict:
        """
        Collects all segments of particular type and creates a mapping between
        their names and the objects themselves.

        Returns:
            [dict]      -- mapping between variable names and segments
        """
        mapping: Dict = {}
        for seg in self.segments:
            if seg.name and isinstance(seg, type_):
                if mapping.get(seg.name) and mapping.get(seg.name) != seg:
                    raise ValueError(f"Duplicate segment: {seg.name}")
                mapping[seg.name] = seg
        return mapping

    def _build(self, string: str) -> None:
        for type_, segment in self._segment(string):
            self.segments.append(self.parser_map[type_](segment, self.vars))
        self.var_segments = self._map_segments(Var)
        self.law_segments = self._map_segments(Law)


def parse_block(
    string: str,
    vars: Dict,
    neg: bool = False,
    min_: int = 1,
    max_: int = 1,
    label: Optional[str] = None,
    start: int = -1,
) -> Block:
    """
    Parses a block string into a Block object. Takes quantifiers and negation
    modifier parameters. Recursively calls itself or `parse_unit` to parse
    nested blocks and units.

    Args:
        string [str]    -- block string
        neg [bool]      -- True if negated
        min_ [int]      -- minimum number of matches
        max_ [int]      -- maximum number of matches
        label [str]     -- block label
        start [int]     -- block start line number

    Returns:
        [Block]         -- Block object representing the parsed string
    """
    it: BlockIterator = BlockIterator(string, start=start)
    members: List[Union[Block, Unit, Ref]] = []
    block = Block(members, vars, neg=neg, min_=min_, max_=max_, label=label)
    for content, neg, min_, max_, label, type_, line_num in it:
        if type_ == Types.BLOCK:
            members.append(parse_block(content, vars, neg, min_, max_, label, line_num))
        elif type_ == Types.UNIT:
            members.append(parse_unit(content, neg, min_, max_, label))
        elif type_ == Types.VAR_REF:
            members.append(Ref(content, neg, min_, max_, label))
    # use this after the iteration is complete
    block.union = it.is_union
    if not block.members and not EMPTY_BLOCK_RE.match(string):
        raise ValueError(
            f"Cannot parse block contents: {string} " f"starting at {start}"
        )
    return block


def parse_unit(
    string: str,
    neg: bool = False,
    min_: int = 1,
    max_: int = 1,
    label: Optional[str] = None,
) -> Unit:
    """
    Parses a unit string into a Unit object. Unit is a list of key-value pairs
    inside a pair of brackets. Key-value pairs are separated by a comma. There
    are colons between keys and values. Values are set inside double quotes,
    while keys are alphanumeric var-like names. Hyphens and underscores are
    allowed in the key names, but numbers and hyphens are not allowed in the
    beginning. An arbitrary amount of space separators is allowed between each
    of the components of the Unit (key, value, colon and comma).

    Examples:
        - (att_name: "attribute value", att-name2: "attribute value")
        - (att_name:"attribute value",att-name2:"attribute value")

    Args:
        string [str]    -- unit string
        neg [bool]      -- True if negated
        min_ [int]      -- minimum number of matches
        max_ [int]      -- maximum number of matches

    Returns:
        [Unit]         -- Unit object representing the parsed string
    """
    it = UNIT_ATTS_RE.findall(string)
    atts = {att_name: parse_value(att_value) for att_name, att_value in it}
    return Unit(atts=atts, neg=neg, min_=min_, max_=max_, label=label)


def parse_value(string: str) -> Union[str, dict, bool, int, float]:
    """
    Unescapes a Unit attribute value and determines whether it is a regular
    string or a Regex.

    Args:
        string [str]    -- attribute value

    Returns:
        [Union[str, Regex, bool, int, float]] -- parsed value
    """
    unesc_str = unescape(string)
    stripped = string.strip()
    if REGEX_RE.match(stripped):
        return {"regex": unesc_str.strip()[7:-2]}
    elif BOOL_RE.match(stripped):
        return stripped.lower() == "true"
    elif INT_RE.match(stripped):
        return int(stripped)
    elif FLOAT_RE.match(stripped):
        return float(stripped)
    else:
        return unesc_str[1:-1]


def unescape(string: str) -> str:
    """
    Unescaping escaped characters typically inside attribute values.

    Args:
        string [str]    -- string to be unescaped

    Returns:
        [str]           -- unescaped string

    """
    return re.sub(r"\\(.)", r"\1", string)


def char_iter(string: str) -> Generator:
    """
    Iterate over the characters of a string while preserving escaped chars. The
    point is to allow escaped characters to be treated differently during char
    iteration (parsing) and then unescaped inside the final data structure.

    Args:
        string [str]    -- regex string

    Returns:
        [Generator]     -- generator iterating over the characters of the
                           string
    """
    for slash, ch in re.findall(r"(\\?)([\s\S])", string):
        yield slash + ch


class BlockIterator:
    """
    Provides an iterator that iterates over the top-level block segments. These
    segments could be blocks (see also Block), units (see also Unit), and
    variable references (see also Ref). These blocks are validated but parsed
    later on. This iterator will produce tuples of the following shape:
    (content_string, negated, min_match_num, max_match_num)

    Args:
        block_str [str]     -- block string
        inf [int]           -- infinity value
        start [int]         -- start line
    """

    def __init__(self, block_str: str, inf: int = INF, start: int = 1) -> None:
        self.buffer: List = []
        self.opened: bool = False
        self.param_buffer: Tuple = (False, 1, 1)
        self.label_buffer: Optional[str] = None
        self.in_var_ref: bool = False
        self.in_value: bool = False
        self.in_comment: bool = False
        self.n_ors: int = 0
        self.level: int = 0
        self.iterable: List[Tuple] = []
        self.inf: int = inf
        self.line_number = start
        self._consume(block_str)
        self._pos: int = 0

    @property
    def is_union(self) -> bool:
        return bool(self.n_ors) and self.n_ors == (len(self.iterable) - 1)

    def _open_bracket(self, ch: str) -> None:
        """
        Handles opening bracket.

        Level 0: checks for no operators and opens the block
        Level 1: parses operator into operator buffer and adds char to buffer
        Other levels: add to buffer

        Args:
            ch:     -- open bracket char
        """
        if self.in_var_ref:
            self._parse_var()
        if self.level == 0:
            ops = "".join(self.buffer).strip()
            if ops:
                raise ValueError(
                    f'Body-level operators not allowed: "{ops}"'
                    f" at line {self.line_number}"
                )
            self.opened = True
        elif self.level == 1:
            self.param_buffer = self._parse_operator()
            self.buffer = [ch]
        else:
            self.buffer.append(ch)
        self.level += 1

    def _close_bracket(self, ch: str) -> None:
        """
        Handles a closing bracket.

        Level 0: checks for an open variable reference and closes the block
        Level 1: checks type of segment (block/unit) and adds to iterable
        Other levels: adds character to the buffer

        Args:
            ch:     -- closing bracket character
        """
        self.level -= 1
        if self.level == 0:
            string = "".join(self.buffer).strip()
            # hadle reference at the end of the body
            if self.in_var_ref:
                self._parse_var()
            elif "".join(self.buffer).strip():
                raise ValueError(
                    f"Unable to parse: {string} " f"at line {self.line_number}"
                )
            self.opened = False
            self.param_buffer = False, 1, 1
            self.buffer = []
        elif self.level == 1:
            string = "".join(self.buffer) + ch
            type_ = Types.UNIT if UNIT_RE.match(string) else Types.BLOCK
            if not EMPTY_BLOCK_RE.match(string):
                item = (
                    string,
                    *self.param_buffer,
                    self.label_buffer,
                    type_,
                    self.line_number,
                )
                self.iterable.append(item)
            self.param_buffer = False, 1, 1
            self.buffer = []
            self.label_buffer = None
        else:
            self.buffer.append(ch)

    def _parse_var(self) -> None:
        """
        Parses a variable reference name and adds it to the iterable.
        """
        ref_str = "".join(self.buffer)
        if not REF_RE.match(ref_str):
            raise ValueError(
                f"Bad var reference name: {ref_str}" f"at line {self.line_number}"
            )
        item = (
            ref_str[1:],
            *self.param_buffer,
            self.label_buffer,
            Types.VAR_REF,
            self.line_number,
        )
        self.iterable.append(item)
        self.buffer = []
        self.param_buffer = False, 1, 1
        self.label_buffer = None
        self.in_var_ref = False

    def _parse_label(self) -> None:
        label = "".join(self.buffer[:-1]).strip()
        if not LABEL_RE.match(label.strip()):
            raise ValueError(f'Invalid label: "{label}" ' f"at line {self.line_number}")
        self.label_buffer = label
        self.buffer = []

    def _check_body_level(self) -> None:
        buff = "".join(self.buffer).strip()
        if self.level == 0 and buff:
            raise ValueError(
                f'Body-level operators not allowed: "{buff}"'
                f" at line {self.line_number}"
            )

    def _parse_operator(self) -> Tuple:
        """
        Assumes that there is an operator in the buffer and parses it. Spaces
        are important for all operators. They are matched as show below.
        Number placeholders can be replaced with any valid integer.

        Examples:
            - not
            - optional
            - zero or more
            - one or more
            - at least {number}
            - at most {number}
            - {number} to {number}

        Raises:
            ValueError  -- when buffer doesn't contain a valid operator and is
                           not empty

        Returns:
            [Tuple]     -- negated[bool], min # matches, max # matches

        """
        string = "".join(self.buffer)
        negated = string.endswith("not")
        if not string.strip("\t\n\r "):
            params = False, 1, 1
        elif string.strip() == "not":
            params = True, 1, 1
        elif OPTION_RE.match(string):
            params = negated, 0, 1
        elif ZERO_PLUS_RE.match(string):
            params = negated, 0, self.inf
        elif ONE_PLUS_RE.match(string):
            params = negated, 1, self.inf
        elif AT_LEAST_RE.match(string):
            m = AT_LEAST_RE.match(string)
            params = negated, int(m.group("min")), self.inf  # type: ignore
        elif AT_MOST_RE.match(string):
            m = AT_MOST_RE.match(string)
            params = negated, 0, int(m.group("max"))  # type: ignore
        elif RANGE_RE.match(string):
            m = RANGE_RE.match(string)
            min_ = int(m.group("min"))  # type: ignore
            max_ = int(m.group("max"))  # type: ignore
            params = negated, min_, max_
        else:
            tail_lines = 0
            while string[-(tail_lines + 1)] == "\n":
                tail_lines += 1
            raise ValueError(
                f'Can\'t parse "{string}" as an operator'
                f"at line {self.line_number - tail_lines}."
            )
        return params

    def _consume(self, block: str) -> None:
        """
        Consumes a block string a character at a time. Note that escaped
        characters are treated differently through the character iterator.
        The iterator acts on all brackets but it validates only variable
        references and operators from level 1 (the top content level).

        Args:
            block [str]     -- block string
        """
        self.buffer = []
        self.level = 0
        last_char = "START"
        for ch in char_iter(block):
            if ch in "\n\r":
                self._check_body_level()
                self.line_number += 1
            if self.in_comment:
                if ch == "\n":
                    self.in_comment = False
            elif ch in " \n\t\r" and last_char in " \n\t\r":
                pass
            elif ch == "#" and not self.in_value and not self.in_var_ref:
                self.in_comment = True
            elif not self.in_value and ch == "(":
                self._open_bracket(ch)
            elif not self.in_value and ch == ")":
                self._close_bracket(ch)
            elif ch == '"':
                self.in_value = not self.in_value
                self.buffer.append(ch)
            elif self.level == 1:
                if (
                    ch == "r"
                    and last_char == "o"
                    and "".join(self.buffer).strip() == "o"
                ):
                    self.n_ors += 1
                    self.buffer = []
                elif ch == "$":
                    self.param_buffer = self._parse_operator()
                    self.in_var_ref = True
                    self.buffer = [ch]
                elif self.in_var_ref and ch in " \n\r\t":
                    self._parse_var()
                elif ch == ">" and last_char == "-":
                    self._parse_label()
                else:
                    self.buffer.append(ch)
            else:
                self.buffer.append(ch)
            last_char = ch
        if self.opened:
            raise ValueError(
                f"Unmatched opening bracket " f"at line {self.line_number}"
            )
        if self.n_ors and not self.is_union:
            raise ValueError(f'Missing "or" operator ' f"at line {self.line_number}")

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> Tuple:
        if self._pos < len(self):
            pos = self._pos
            self._pos += 1
            return self.iterable[pos]
        else:
            raise StopIteration()

    def __len__(self) -> int:
        return len(self.iterable)
