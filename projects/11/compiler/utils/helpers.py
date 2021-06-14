import itertools
import re
import typing as t

from compiler.utils.constants import Category, SymbolKind


def is_generator_empty(generator):
    a, b = itertools.tee(generator)
    try:
        next(a)
    except StopIteration:
        return True, b
    return False, b


token_dict = {
    "keyword": (
        r"class|constructor|function|"
        r"method|field|static|var|"
        r"int|char|boolean|void|true|"
        r"false|null|this|let|do|"
        r"if|else|while|return"
    ),
    "symbol": (r"\{|\}|\(|\)|\[|\]|\.|" r",|;|\+|\-|\*|/|&|" r"\||<|>|=|~"),
    "integerConstant": (
        r"3276[0-7]|327[0-5][0-9]|32[0-6][0-9]{2}|3[01][0-9]{3}|"
        r"[12][0-9]{4}|[1-9][0-9]{1,3}|[0-9]"
    ),
    "stringConstant": r'"[^\"\n]+"',
    "identifier": r"[a-zA-Z_]\w*",
}

token = (
    rf"{token_dict['keyword']}"
    rf"|{token_dict['symbol']}"
    rf"|{token_dict['integerConstant']}"
    rf"|{token_dict['stringConstant']}"
    rf"|{token_dict['identifier']}"
)

token_re = re.compile(token)


def get_token_type(token: str) -> str:
    for k, v in token_dict.items():
        if re.fullmatch(v, token):
            return k
    raise ValueError("Token type not found")


def escape_token(token: str) -> str:
    d_esc = {
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "&": "&amp;",
    }
    if token in d_esc:
        token = d_esc[token]
    return token


def is_symbol(category: Category) -> bool:
    return category in (
        Category.VAR,
        Category.ARGUMENT,
        Category.STATIC,
        Category.FIELD,
    )


def cat2kind(category: Category) -> SymbolKind:
    map_ = {
        Category.VAR: SymbolKind.VAR,
        Category.ARGUMENT: SymbolKind.ARG,
        Category.STATIC: SymbolKind.STATIC,
        Category.FIELD: SymbolKind.FIELD,
    }
    return map_[category]
