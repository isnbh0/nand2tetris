import argparse
import os
import re
import typing as t

from enum import Enum
from types import MethodDescriptorType

import helpers as h


# TODO: try to add decorator pattern


class T(str, Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"


class K(str, Enum):
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    CONSTRUCTOR = "constructor"
    INT = "int"
    BOOLEAN = "boolean"
    CHAR = "char"
    VOID = "void"
    VAR = "var"
    STATIC = "static"
    FIELD = "field"
    LET = "let"
    DO = "do"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    THIS = "this"


class JackTokenizer:
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


class CompilationEngine:
    def __init__(self, file_path):
        self.output = []
        self.level = 0
        self.jt = JackTokenizer(file_path=file_path)

    def _i(self, s: str) -> str:
        return "  " * self.level + s

    def _append_with_indent(self, s: str):
        to_append = self._i(s)
        self.output.append(to_append)

    def _append_and_advance(self):
        self._append_with_indent(s=repr(self.jt))
        self.jt.advance()

    def _at_keyword(self, keywords: t.Iterable) -> bool:
        return self.jt.tokenType == T.KEYWORD and self.jt.keyWord in keywords

    def _append_and_advance_keyword(self, keywords: t.Iterable):
        assert self._at_keyword(keywords=keywords)
        self._append_and_advance()

    def _at_symbol(self, symbol: str) -> bool:
        return self.jt.tokenType == T.SYMBOL and self.jt.symbol == symbol

    def _append_and_advance_symbol(self, symbol: str):
        assert self._at_symbol(symbol=symbol)
        self._append_and_advance()

    def _at_symbols(self, symbols: t.Iterable) -> bool:
        return self.jt.tokenType == T.SYMBOL and self.jt.symbol in symbols

    def _append_and_advance_symbols(self, symbols: t.Iterable):
        """Quick hack to handle unaryOp"""
        assert self._at_symbols(symbols=symbols)
        self._append_and_advance()

    def _at_type(self, with_void: bool = False) -> bool:
        if with_void:
            allowed_types = (K.INT, K.CHAR, K.BOOLEAN, K.VOID)
        else:
            allowed_types = (K.INT, K.CHAR, K.BOOLEAN)
        return (
            self.jt.tokenType == T.KEYWORD and self.jt.keyWord in allowed_types
        ) or self.jt.tokenType == T.IDENTIFIER

    def _append_and_advance_type(self, with_void: bool = False):
        assert self._at_type(with_void=with_void)
        self._append_and_advance()

    def _at_identifier(self) -> bool:
        return self.jt.tokenType == T.IDENTIFIER

    def _append_and_advance_identifier(self):
        assert self._at_identifier()
        self._append_and_advance()

    def bookend(keyword: str):
        def decorate(f):
            def f_new(self):
                self._append_with_indent(f"<{keyword}>")
                self.level += 1
                f(self)
                self.level -= 1
                self._append_with_indent(f"</{keyword}>")

            return f_new

        return decorate

    @bookend(keyword="class")
    def compileClass(self):
        # 'class'
        self._append_and_advance_keyword(keywords=(K.CLASS,))

        # className
        self._append_and_advance_identifier()

        # '{'
        self._append_and_advance_symbol("{")

        # classVarDec*
        while self._at_keyword(keywords=(K.STATIC, K.FIELD)):
            self.compileClassVarDec()

        # subroutineDec*
        while self._at_keyword(keywords=(K.CONSTRUCTOR, K.FUNCTION, K.METHOD)):
            self.compileSubroutine()

        # '}'
        self._append_and_advance_symbol("}")

    @bookend(keyword="classVarDec")
    def compileClassVarDec(self):
        # ('static' | 'field')
        self._append_and_advance_keyword(keywords=(K.STATIC, K.FIELD))

        # type
        self._append_and_advance_type()

        # varName
        self._append_and_advance_identifier()

        # (',' varName)*
        while self._at_symbol(","):
            # ','
            self._append_and_advance_symbol(",")
            # varName
            self._append_and_advance_identifier()

        # ';'
        self._append_and_advance_symbol(";")

    @bookend(keyword="subroutineDec")
    def compileSubroutine(self):
        # ('constructor' | 'function' | 'method')
        self._append_and_advance_keyword(keywords=(K.CONSTRUCTOR, K.FUNCTION, K.METHOD))

        # ('void' | type)
        self._append_and_advance_type(with_void=True)

        # subroutineName
        self._append_and_advance_identifier()

        # '('
        self._append_and_advance_symbol("(")

        # parameterList
        self.compileParameterList()

        # ')'
        self._append_and_advance_symbol(")")

        # subroutineBody
        self._append_with_indent("<subroutineBody>")
        self.level += 1

        # '{'
        self._append_and_advance_symbol("{")

        # varDec*
        while self._at_keyword(keywords=(K.VAR,)):
            self.compileVarDec()

        # statements
        self.compileStatements()

        # '}'
        self._append_and_advance_symbol("}")

        # end subroutineBody
        self.level -= 1
        self._append_with_indent("</subroutineBody>")

    @bookend(keyword="parameterList")
    def compileParameterList(self):
        # ((type varName) (',' type varName)*)?
        if self._at_type():
            # type
            self._append_and_advance()
            # varName
            self._append_and_advance_identifier()
            # (',' type varName)*
            while self._at_symbol(","):
                # ','
                self._append_and_advance_symbol(",")
                # type
                self._append_and_advance_type()
                # varName
                self._append_and_advance_identifier()

    @bookend(keyword="varDec")
    def compileVarDec(self):
        # 'var'
        self._append_and_advance_keyword(keywords=(K.VAR,))

        # type
        self._append_and_advance_type()

        # varName
        self._append_and_advance_identifier()

        # (',' varName)*
        while self._at_symbol(","):
            # ','
            self._append_and_advance_symbol(",")
            # varName
            self._append_and_advance_identifier()

        # ';'
        self._append_and_advance_symbol(";")

    @bookend(keyword="statements")
    def compileStatements(self):
        while self._at_keyword(keywords=(K.LET, K.IF, K.WHILE, K.DO, K.RETURN)):
            keyword = self.jt.keyWord
            if keyword == K.LET:
                self.compileLet()
            elif keyword == K.IF:
                self.compileIf()
            elif keyword == K.WHILE:
                self.compileWhile()
            elif keyword == K.DO:
                self.compileDo()
            elif keyword == K.RETURN:
                self.compileReturn()
            else:
                raise Exception("This point should not be reachable")

    @bookend(keyword="letStatement")
    def compileLet(self):
        # 'let'
        self._append_and_advance_keyword(keywords=(K.LET,))

        # varName
        self._append_and_advance_identifier()

        # ('[' expression ']')?
        if self._at_symbol("["):
            # '['
            self._append_and_advance_symbol("[")

            # expression
            self.compileExpression()

            # ']'
            self._append_and_advance_symbol("]")

        # '='
        self._append_and_advance_symbol("=")

        # expression
        self.compileExpression()

        # ';'
        self._append_and_advance_symbol(";")

    @bookend(keyword="ifStatement")
    def compileIf(self):
        # 'if'
        self._append_and_advance_keyword(keywords=(K.IF,))

        # '('
        self._append_and_advance_symbol("(")

        # expression
        self.compileExpression()

        # ')'
        self._append_and_advance_symbol(")")

        # '{'
        self._append_and_advance_symbol("{")

        # statements
        self.compileStatements()

        # '}'
        self._append_and_advance_symbol("}")

        # ('else' '{' statements '}')?
        if self._at_keyword(keywords=(K.ELSE,)):
            # 'else'
            self._append_and_advance_keyword(keywords=(K.ELSE,))
            # '{'
            self._append_and_advance_symbol("{")
            # statements
            self.compileStatements()
            # '}'
            self._append_and_advance_symbol("}")

    @bookend(keyword="whileStatement")
    def compileWhile(self):
        # 'while'
        self._append_and_advance_keyword(keywords=(K.WHILE,))

        # '('
        self._append_and_advance_symbol("(")

        # expression
        self.compileExpression()

        # ')'
        self._append_and_advance_symbol(")")

        # '{'
        self._append_and_advance_symbol("{")

        # statements
        self.compileStatements()

        # '}'
        self._append_and_advance_symbol("}")

    @bookend(keyword="doStatement")
    def compileDo(self):
        # 'do'
        self._append_and_advance_keyword(keywords=(K.DO,))

        # subroutineCall
        # identifier
        self._append_and_advance_identifier()

        if self._at_symbol("("):  # subroutineName
            # '('
            self._append_and_advance_symbol("(")
            # expressionList
            self.compileExpressionList()
            # ')'
            self._append_and_advance_symbol(")")
        elif self._at_symbol("."):  # (className | varName)
            # '.'
            self._append_and_advance_symbol(".")
            # subroutineName
            self._append_and_advance_identifier()
            # '('
            self._append_and_advance_symbol("(")
            # expressionList
            self.compileExpressionList()
            # ')'
            self._append_and_advance_symbol(")")
        else:
            raise ValueError("Unrecognized syntax for subroutine call")

        # ';'
        self._append_and_advance_symbol(";")

    @bookend(keyword="returnStatement")
    def compileReturn(self):
        # 'return'
        self._append_and_advance_keyword(keywords=(K.RETURN,))

        # expression?
        # TODO: fix this?
        if not self._at_symbol(";"):
            self.compileExpression()

        # ';'
        self._append_and_advance_symbol(";")

    @bookend(keyword="expression")
    def compileExpression(self):
        # term
        self.compileTerm()

        # (op term)*
        ops = ("+", "-", "*", "/", "&", "|", "<", ">", "=")
        while self._at_symbols(symbols=ops):
            # op
            self._append_and_advance_symbols(symbols=ops)
            # term
            self.compileTerm()

    @bookend(keyword="term")
    def compileTerm(self):
        token_type = self.jt.tokenType
        if token_type == T.INT_CONST:
            self._append_and_advance()
        elif token_type == T.STRING_CONST:
            self._append_and_advance()
        elif token_type == T.KEYWORD:
            assert self.jt.keyWord in (K.TRUE, K.FALSE, K.NULL, K.THIS)
            self._append_and_advance()
        elif token_type == T.IDENTIFIER:
            self._append_and_advance_identifier()
            if self._at_symbol("["):
                # '['
                self._append_and_advance_symbol("[")
                # expression
                self.compileExpression()
                # ']'
                self._append_and_advance_symbol("]")
            elif self._at_symbol("("):
                # '('
                self._append_and_advance_symbol("(")
                # expressionList
                self.compileExpressionList()
                # ')'
                self._append_and_advance_symbol(")")
            elif self._at_symbol("."):
                # '.'
                self._append_and_advance_symbol(".")
                # subroutineName
                self._append_and_advance_identifier()
                # '('
                self._append_and_advance_symbol("(")
                # expressionList
                self.compileExpressionList()
                # ')'
                self._append_and_advance_symbol(")")
            else:
                pass
        elif token_type == T.SYMBOL and self.jt.symbol == "(":
            # '(' expression ')'
            self._append_and_advance_symbol("(")
            self.compileExpression()
            self._append_and_advance_symbol(")")
        elif token_type == T.SYMBOL and self.jt.symbol in ("-", "~"):
            # unaryOp
            self._append_and_advance_symbols(symbols=("-", "~"))
            # term
            self.compileTerm()
        else:
            raise Exception("Token type not found")

    @bookend(keyword="expressionList")
    def compileExpressionList(self):
        # (expression (',' expression)*)?
        if not self._at_symbol(")"):
            # expression
            self.compileExpression()
            # (',' expression)*
            while self._at_symbol(","):
                # ','
                self._append_and_advance_symbol(",")
                # expression
                self.compileExpression()

    def to_disk(self, file_path: str):
        with open(file_path, "w") as f:
            f.writelines(f"{line}\n" for line in self.output)


def analyze_single_file(file_path):
    ce = CompilationEngine(file_path=file_path)
    try:
        ce.compileClass()
    except:
        print("\n".join(ce.output))
    ce.to_disk(file_path=file_path.replace(".jack", "out.xml"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("path", help="path to jack file")

    args = parser.parse_args()

    path = args.path

    if os.path.isdir(path):
        raise ValueError("Only supports file-level analysis")
    else:
        analyze_single_file(file_path=path)
