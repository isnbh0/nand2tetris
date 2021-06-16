import re

from compiler.utils.constants import TokenType, Keyword
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
            return TokenType.KEYWORD
        elif token_type == "symbol":
            return TokenType.SYMBOL
        elif token_type == "identifier":
            return TokenType.IDENTIFIER
        elif token_type == "integerConstant":
            return TokenType.INT_CONST
        elif token_type == "stringConstant":
            return TokenType.STRING_CONST
        else:
            raise ValueError

    def get_tag(self):
        if self.tokenType == TokenType.STRING_CONST:
            tkn = self.tkn[1:-1]
        elif self.tokenType == TokenType.SYMBOL:
            tkn = h.escape_token(self.tkn)
        else:
            tkn = self.tkn
        return f"<{self.tokenType}> {tkn} </{self.tokenType}>"

    @property
    def keyWord(self) -> Keyword:
        assert self.tokenType == TokenType.KEYWORD
        return self.tkn

    @property
    def symbol(self) -> str:
        assert self.tokenType == TokenType.SYMBOL
        return self.tkn

    @property
    def identifier(self) -> str:
        assert self.tokenType == TokenType.IDENTIFIER
        return self.tkn

    @property
    def intVal(self) -> int:
        assert self.tokenType == TokenType.INT_CONST
        return self.tkn

    @property
    def stringVal(self) -> str:
        assert self.tokenType == TokenType.STRING_CONST
        return self.tkn
