import json
from collections import Counter


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, type({}.items())):
            return {str(k): v for k, v in obj}
        return json.JSONEncoder.default(self, obj)


def is_probably_equal(arg1: object, arg2: object) -> bool:
    if isinstance(arg1, dict):
        arg1 = {str(k): v for k, v in arg1.items()}
    if isinstance(arg2, dict):
        arg2 = {str(k): v for k, v in arg2.items()}
    c_a = Counter(arg1) if isinstance(arg1, str) else \
        Counter(str(json.dumps(arg1, cls=Encoder)))
    c_b = Counter(arg2) if isinstance(arg2, str) else \
        Counter(str(json.dumps(arg2, cls=Encoder)))
    return c_a == c_b


def parse_babylonian_data(fp):
    item_sep = '################################'
    atts_sep = '================================'
    with open(fp, encoding='utf-8') as fh:
        s = fh.read()
    items = [itm for itm in s.split(item_sep) if itm.strip()]
    for itm in items:
        atts_str, grammar_str = itm.split(atts_sep)
        yield parse_bab_data_atts(atts_str), grammar_str


def parse_bab_data_atts(atts_str):
    lines = atts_str.split('\n')
    atts = {line.split(':', 1)[0]: line.split(':', 1)[1].strip()
            for line in lines if line}
    for key in atts:
        if key in ['outcomes', 'inputs']:
            atts[key] = atts[key].strip().split(';')
        elif key in ['loads']:
            atts[key] = parse_bool(atts[key].strip())
        else:
            atts[key] = atts[key].strip()
    return atts


def parse_bool(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    else:
        raise ValueError(f'Incorrect boolean value: {s}')


class Underscore:
    pass


class FakeToken:
    def __init__(self, orth, lemma, pos):
        self.orth = orth
        self.lemma = lemma
        self.pos = pos
        self._ = Underscore()


class FakeDocument:

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos_ = 0

    def __iter__(self):
        return iter(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.tokens[item]
        else:
            return FakeDocument([t for t in self.tokens[item]])
