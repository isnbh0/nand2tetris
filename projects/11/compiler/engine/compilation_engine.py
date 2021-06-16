import argparse
import os
import sys

if "compiler" in sys.path[0]:
    sys.path = [os.getcwd()] + sys.path
import typing as t

import compiler.utils.helpers as h
from compiler.utils.constants import TokenType, Keyword, Category, Verb
from compiler.jack_tokenizer import JackTokenizer
from compiler.symbol_table import SymbolTable


class CompilationEngine:
    """recursive top-down compilation engine"""

    def __init__(self, file_path):
        self.output = []
        self.level = 0
        self.jt = JackTokenizer(file_path=file_path)
        self.st = SymbolTable()
        self.last_token = None

    def _i(self, s: str) -> str:
        return "  " * self.level + s

    def _append_with_indent(self, s: str):
        to_append = self._i(s)
        self.output.append(to_append)

    def _advance(self):
        self.last_token = self.jt.tkn
        self.jt.advance()

    def _append(self, s=None, advance=False):
        s = s or repr(self.jt)
        self._append_with_indent(s=s)  # repr(self.jt))
        if advance:
            self._advance()

    def _append_and_advance(self, s=None):
        self._append(s=s, advance=True)

    def _at_keyword(self, keywords: t.Iterable) -> bool:
        return self.jt.tokenType == TokenType.KEYWORD and self.jt.keyWord in keywords

    def _append_and_advance_keyword(self, keywords: t.Iterable):
        assert self._at_keyword(keywords=keywords)
        self._append_and_advance()

    def _at_symbol(self, symbol: str) -> bool:
        return self.jt.tokenType == TokenType.SYMBOL and self.jt.symbol == symbol

    def _append_and_advance_symbol(self, symbol: str):
        assert self._at_symbol(symbol=symbol)
        self._append_and_advance()

    def _at_symbols(self, symbols: t.Iterable) -> bool:
        return self.jt.tokenType == TokenType.SYMBOL and self.jt.symbol in symbols

    def _append_and_advance_symbols(self, symbols: t.Iterable):
        """Quick hack to handle unaryOp"""
        assert self._at_symbols(symbols=symbols)
        self._append_and_advance()

    def _at_type(self, with_void: bool = False) -> bool:
        if with_void:
            allowed_types = (Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID)
        else:
            allowed_types = (Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN)
        return (
            self.jt.tokenType == TokenType.KEYWORD and self.jt.keyWord in allowed_types
        ) or self.jt.tokenType == TokenType.IDENTIFIER

    def _append_and_advance_type(self, with_void: bool = False):
        assert self._at_type(with_void=with_void)
        self._append_and_advance()

    def _at_identifier(self) -> bool:
        return self.jt.tokenType == TokenType.IDENTIFIER

    def _append_and_advance_identifier(self):
        assert self._at_identifier()
        self._append_and_advance()

    def _append_identifier_scope(
        self,
        category: Category,
        verb: Verb,
        advance: bool = True,
        name: t.Optional[str] = None,
    ):
        assert self._at_identifier() or name is not None
        name = name or self.jt.tkn
        self._append(
            s=self._build_identifier_tag(name=name, category=category, verb=verb),
            advance=advance,
        )

    def _append_identifier_symbol(
        self,
        verb: Verb,
        type: t.Optional[str] = None,
        category: t.Optional[Category] = None,
        advance: bool = True,
        name: t.Optional[str] = None,
    ):
        assert self._at_identifier() or name is not None
        name = name or self.jt.tkn
        if verb == Verb.DEFINE:
            self.st.define(name=name, type=type, kind=h.cat2kind(category))
        elif verb == Verb.USE:
            category = self.st.kindOf(name)
        else:
            raise ValueError(f"Unrecognized verb: {verb}")
        index = self.st.indexOf(name)
        self._append(
            s=self._build_identifier_tag(
                name=name, category=category, verb=verb, index=index
            ),
            advance=advance,
        )

    def _build_identifier_tag(
        self, name: str, category: Category, verb: Verb, index: t.Optional[int] = None
    ):
        tag = "<identifier"
        tag += f' category="{category}"'
        tag += f' verb="{verb}"'
        tag += f" index={index}" if index is not None else ""
        tag += ">"
        tag += f" {name}"
        tag += " </identifier>"
        return tag

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
        self._append_and_advance_keyword(keywords=(Keyword.CLASS,))

        # className
        self._append_identifier_scope(category=Category.CLASS, verb=Verb.DEFINE)

        # '{'
        self._append_and_advance_symbol("{")

        # classVarDec*
        while self._at_keyword(keywords=(Keyword.STATIC, Keyword.FIELD)):
            self.compileClassVarDec()

        # subroutineDec*
        while self._at_keyword(
            keywords=(Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD)
        ):
            self.compileSubroutine()

        # '}'
        self._append_and_advance_symbol("}")

    @bookend(keyword="classVarDec")
    def compileClassVarDec(self):
        # ('static' | 'field')
        self._append_and_advance_keyword(keywords=(Keyword.STATIC, Keyword.FIELD))
        category = self.last_token

        # type
        self._append_and_advance_type()
        type = self.last_token

        # varName
        self._append_identifier_symbol(type=type, category=category, verb=Verb.DEFINE)

        # (',' varName)*
        while self._at_symbol(","):
            # ','
            self._append_and_advance_symbol(",")
            # varName
            self._append_identifier_symbol(
                type=type, category=category, verb=Verb.DEFINE
            )

        # ';'
        self._append_and_advance_symbol(";")

    @bookend(keyword="subroutineDec")
    def compileSubroutine(self):
        # ('constructor' | 'function' | 'method')
        self._append_and_advance_keyword(
            keywords=(Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD)
        )

        # ('void' | type)
        self._append_and_advance_type(with_void=True)

        # subroutineName
        self._append_identifier_scope(category=Category.SUBROUTINE, verb=Verb.DEFINE)

        # '('
        self._append_and_advance_symbol("(")

        # parameterList
        self.compileParameterList()

        # ')'
        self._append_and_advance_symbol(")")

        # subroutineBody
        self._compileSubroutineBody()

    @bookend(keyword="subroutineBody")
    def _compileSubroutineBody(self):
        # '{'
        self._append_and_advance_symbol("{")

        # varDec*
        while self._at_keyword(keywords=(Keyword.VAR,)):
            self.compileVarDec()

        # statements
        self.compileStatements()

        # '}'
        self._append_and_advance_symbol("}")

    @bookend(keyword="parameterList")
    def compileParameterList(self):
        # ((type varName) (',' type varName)*)?
        if self._at_type():
            # type
            self._append_and_advance()
            type = self.last_token
            # varName
            self._append_identifier_symbol(
                type=type, category=Category.ARGUMENT, verb=Verb.DEFINE
            )
            # (',' type varName)*
            while self._at_symbol(","):
                # ','
                self._append_and_advance_symbol(",")
                # type
                self._append_and_advance_type()
                type = self.last_token
                # varName
                self._append_identifier_symbol(
                    type=type, category=Category.ARGUMENT, verb=Verb.DEFINE
                )

    @bookend(keyword="varDec")
    def compileVarDec(self):
        # 'var'
        self._append_and_advance_keyword(keywords=(Keyword.VAR,))
        category = self.last_token

        # type
        self._append_and_advance_type()
        type = self.last_token

        # varName
        self._append_identifier_symbol(type=type, category=category, verb=Verb.DEFINE)

        # (',' varName)*
        while self._at_symbol(","):
            # ','
            self._append_and_advance_symbol(",")
            # varName
            self._append_identifier_symbol(
                type=type, category=category, verb=Verb.DEFINE
            )

        # ';'
        self._append_and_advance_symbol(";")

    @bookend(keyword="statements")
    def compileStatements(self):
        while self._at_keyword(
            keywords=(
                Keyword.LET,
                Keyword.IF,
                Keyword.WHILE,
                Keyword.DO,
                Keyword.RETURN,
            )
        ):
            keyword = self.jt.keyWord
            if keyword == Keyword.LET:
                self.compileLet()
            elif keyword == Keyword.IF:
                self.compileIf()
            elif keyword == Keyword.WHILE:
                self.compileWhile()
            elif keyword == Keyword.DO:
                self.compileDo()
            elif keyword == Keyword.RETURN:
                self.compileReturn()
            else:
                raise Exception("This point should not be reachable")

    @bookend(keyword="letStatement")
    def compileLet(self):
        # 'let'
        self._append_and_advance_keyword(keywords=(Keyword.LET,))

        # varName
        self._append_identifier_symbol(verb=Verb.USE)

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
        self._append_and_advance_keyword(keywords=(Keyword.IF,))

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
        if self._at_keyword(keywords=(Keyword.ELSE,)):
            # 'else'
            self._append_and_advance_keyword(keywords=(Keyword.ELSE,))
            # '{'
            self._append_and_advance_symbol("{")
            # statements
            self.compileStatements()
            # '}'
            self._append_and_advance_symbol("}")

    @bookend(keyword="whileStatement")
    def compileWhile(self):
        # 'while'
        self._append_and_advance_keyword(keywords=(Keyword.WHILE,))

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
        self._append_and_advance_keyword(keywords=(Keyword.DO,))

        # subroutineCall
        # identifier
        self._advance()
        identifier = self.last_token

        if self._at_symbol("("):  # subroutineName
            self._append_identifier_scope(
                name=identifier,
                category=Category.SUBROUTINE,
                verb=Verb.USE,
                advance=False,
            )
            # '('
            self._append_and_advance_symbol("(")
            # expressionList
            self.compileExpressionList()
            # ')'
            self._append_and_advance_symbol(")")
        elif self._at_symbol("."):  # (className | varName)
            try:
                # try to use varName
                self._append_identifier_symbol(
                    name=identifier, verb=Verb.USE, advance=False,
                )
            except ValueError:
                # no var found: do className
                self._append_identifier_scope(
                    name=identifier,
                    category=Category.CLASS,
                    verb=Verb.USE,
                    advance=False,
                )
            # '.'
            self._append_and_advance_symbol(".")
            # subroutineName
            self._append_identifier_scope(category=Category.SUBROUTINE, verb=Verb.USE)
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
        self._append_and_advance_keyword(keywords=(Keyword.RETURN,))

        # expression?
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
        if token_type == TokenType.INT_CONST:
            self._append_and_advance()
        elif token_type == TokenType.STRING_CONST:
            self._append_and_advance()
        elif token_type == TokenType.KEYWORD:
            assert self.jt.keyWord in (
                Keyword.TRUE,
                Keyword.FALSE,
                Keyword.NULL,
                Keyword.THIS,
            )
            self._append_and_advance()
        elif token_type == TokenType.IDENTIFIER:
            # identifier
            self._advance()
            identifier = self.last_token
            if self._at_symbol("["):  # varName
                self._append_identifier_symbol(
                    name=identifier, verb=Verb.USE, advance=False,
                )
                # '['
                self._append_and_advance_symbol("[")
                # expression
                self.compileExpression()
                # ']'
                self._append_and_advance_symbol("]")
            elif self._at_symbol("("):  # subroutineName
                self._append_identifier_scope(
                    name=identifier,
                    category=Category.SUBROUTINE,
                    verb=Verb.USE,
                    advance=False,
                )
                # '('
                self._append_and_advance_symbol("(")
                # expressionList
                self.compileExpressionList()
                # ')'
                self._append_and_advance_symbol(")")
            elif self._at_symbol("."):  # (className | varName)
                try:
                    # try to use varName
                    self._append_identifier_symbol(
                        name=identifier, verb=Verb.USE, advance=False,
                    )
                except ValueError:
                    # no var found: do className
                    self._append_identifier_scope(
                        name=identifier,
                        category=Category.CLASS,
                        verb=Verb.USE,
                        advance=False,
                    )
                # '.'
                self._append_and_advance_symbol(".")
                # subroutineName
                self._append_identifier_scope(
                    category=Category.SUBROUTINE, verb=Verb.USE
                )
                # '('
                self._append_and_advance_symbol("(")
                # expressionList
                self.compileExpressionList()
                # ')'
                self._append_and_advance_symbol(")")
            else:  # varName
                self._append_identifier_symbol(
                    name=identifier, verb=Verb.USE, advance=False,
                )
        elif token_type == TokenType.SYMBOL and self.jt.symbol == "(":
            # '(' expression ')'
            self._append_and_advance_symbol("(")
            self.compileExpression()
            self._append_and_advance_symbol(")")
        elif token_type == TokenType.SYMBOL and self.jt.symbol in ("-", "~"):
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
    except Exception as e:
        # print("\n".join(ce.output))
        raise (e)

    ce.to_disk(file_path=file_path.replace(".jack", "_out.xml"))


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
