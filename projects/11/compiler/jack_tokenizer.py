import re

from compiler.utils.constants import T, K
import compiler.utils.helpers as h


class JackTokenizer:
    """tokenizer"""

    def __init__(self, file_path):
        self.code = self._get_code(file_path)

        self.tkn = None
        self.token_iter = (found.group(0) for found in h.token_re.finditer(self.code))
        self.advance()  # Initialize token

    def _get_code(self, file_path: str) -> str:
        with open(file_path, "r") as f:
            lines = f.readlines()
        lines = [re.sub(r"\s*//.*$", "", line.strip()) for line in lines]
        lines = [line for line in lines if line]
        code = "\n".join(lines)
        code = re.sub(r"/\*.*?\*/", " ", code, flags=re.DOTALL)
        return code

    @property
    def hasMoreTokens(self) -> bool:
        result, self.token_iter = h.is_generator_empty(self.token_iter)
        return not result

    def advance(self):
        if self.hasMoreTokens:
            self.tkn = next(self.token_iter)

    @property
    def tokenType(self) -> str:
        token_type = h.get_token_type(self.tkn)
        if token_type == "keyword":
            return T.KEYWORD
        elif token_type == "symbol":
            return T.SYMBOL
        elif token_type == "identifier":
            return T.IDENTIFIER
        elif token_type == "integerConstant":
            return T.INT_CONST
        elif token_type == "stringConstant":
            return T.STRING_CONST
        else:
            raise ValueError

    def __repr__(self):
        return JackTokenizer.get_tag(self.tkn, self.tokenType)

    @staticmethod
    def get_tag(tkn, tokenType):
        if tokenType == T.STRING_CONST:
            tkn = tkn[1:-1]
        elif tokenType == T.SYMBOL:
            tkn = h.escape_token(tkn)
        else:
            tkn = tkn
        return f"<{tokenType}> {tkn} </{tokenType}>"

    @property
    def keyWord(self) -> K:
        assert self.tokenType == T.KEYWORD
        return self.tkn

    @property
    def symbol(self) -> str:
        assert self.tokenType == T.SYMBOL
        return self.tkn

    @property
    def identifier(self) -> str:
        assert self.tokenType == T.IDENTIFIER
        return self.tkn

    @property
    def intVal(self) -> int:
        assert self.tokenType == T.INT_CONST
        return self.tkn

    @property
    def stringVal(self) -> str:
        assert self.tokenType == T.STRING_CONST
        return self.tkn
