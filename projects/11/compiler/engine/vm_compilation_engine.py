import argparse
import os
from re import sub
import sys

if "compiler" in sys.path[0]:
    sys.path = [os.getcwd()] + sys.path
import typing as t

from compiler.engine.compilation_engine import CompilationEngine
from compiler.jack_tokenizer import JackTokenizer
from compiler.symbol_table import SymbolTable
from compiler.utils.constants import (
    Segment,
    SymbolKind,
    TokenType,
    Keyword,
    Category,
    Verb,
)
import compiler.utils.helpers as h
from compiler.vm_writer import VMWriter


class VMCompilationEngine(CompilationEngine):
    """recursive top-down compilation engine"""

    def __init__(self, file_path):
        self.jt = JackTokenizer(file_path=file_path)
        self.st = SymbolTable()
        self.writer = VMWriter(out_path=file_path.replace(".jack", ".vm"))

        self.class_name = "__undefined__"

    def _append_with_indent(self, s: str):
        to_append = self._i(s)
        self.output.append(to_append)

    def _advance(self):
        self.jt.advance()

    def _append(self, s=None, advance=False):
        s = s or self.jt.get_tag()
        self._append_with_indent(s=s)
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

    def _define_and_advance(
        self, type: str, kind: SymbolKind, name: t.Optional[str] = None
    ):
        assert self._at_identifier()
        name = name or self.jt.tkn
        self.st.define(name=name, type=type, kind=kind)
        self._advance()

    def compileClass(self):
        # 'class'
        assert self._at_keyword(keywords=(Keyword.CLASS,))
        self._advance()

        # className
        assert self._at_identifier()
        self.class_name = self.jt.tkn
        self._advance()

        # '{'
        assert self._at_symbol("{")
        self._advance()

        # classVarDec*
        while self._at_keyword(keywords=(Keyword.STATIC, Keyword.FIELD)):
            self.compileClassVarDec()

        # subroutineDec*
        while self._at_keyword(
            keywords=(Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD)
        ):
            self.compileSubroutine()

        # '}'
        assert self._at_symbol("}")
        self._advance()

    def compileClassVarDec(self):
        # ('static' | 'field')
        assert self._at_keyword(keywords=(Keyword.STATIC, Keyword.FIELD))
        kind = h.cat2kind(self.jt.tkn)
        self._advance()

        # type
        assert self._at_type(with_void=False)
        type = self.jt.tkn
        self._advance()

        # varName
        self._define_and_advance(type=type, kind=kind)

        # (',' varName)*
        while self._at_symbol(","):
            # ','
            self._advance()
            # varName
            self._define_and_advance(type=type, kind=kind)

        # ';'
        self._advance()

    def compileSubroutine(self):
        # ('constructor' | 'function' | 'method')
        assert self._at_keyword(
            keywords=(Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD)
        )
        subroutine_type = self.jt.tkn
        self._advance()

        # ('void' | type)
        assert self._at_type(with_void=True)
        self._advance()

        # subroutineName
        assert self._at_identifier()
        function_name = self.jt.tkn
        self._advance()

        # '('
        assert self._at_symbol("(")
        self._advance()

        # parameterList
        self.compileParameterList()

        # ')'
        assert self._at_symbol(")")
        self._advance()

        # subroutineBody
        self._compileSubroutineBody(
            subroutine_type=subroutine_type, function_name=function_name
        )

    def compileParameterList(self):
        # ((type varName) (',' type varName)*)?
        if self._at_type():
            # type
            assert self._at_type(with_void=False)
            type = self.jt.tkn
            self._advance()
            # varName
            kind = SymbolKind.ARG
            self._define_and_advance(type=type, kind=kind)
            # (',' type varName)*
            while self._at_symbol(","):
                # ','
                self._advance()
                # type
                assert self._at_identifier()
                type = self.jt.tkn
                self._advance()
                # varName
                kind = SymbolKind.ARG
                self._define_and_advance(type=type, kind=kind)

    def _compileSubroutineBody(self, subroutine_type: Keyword, function_name: str):
        # '{'
        assert self._at_symbol("{")
        self._advance()

        # varDec*
        nLocals = 0
        while self._at_keyword(keywords=(Keyword.VAR,)):
            nLocals += self.compileVarDec()

        # write vm function command here
        name = f"{self.class_name}.{function_name}"
        self.writer.writeFunction(name=name, nLocals=nLocals)

        if subroutine_type == Keyword.CONSTRUCTOR:
            raise NotImplementedError
        elif subroutine_type == Keyword.FUNCTION:
            pass
        elif subroutine_type == Keyword.METHOD:
            # write code to set "this" to passed object
            # push argument 0
            self.writer.writePush(segment=Segment.ARGUMENT, index=0)
            # pop pointer 0
            self.writer.writePop(segment=Segment.POINTER, index=0)

        # statements
        self.compileStatements()

        # '}'
        assert self._at_symbol("}")
        self._advance()

    def compileVarDec(self) -> int:
        count = 0
        # 'var'
        assert self._at_keyword(keywords=(Keyword.VAR,))
        kind = h.cat2kind(self.jt.tkn)
        self._advance()

        # type
        assert self._at_type(with_void=False)
        type = self.jt.tkn
        self._advance()

        # varName
        self._define_and_advance(type=type, kind=kind)
        count += 1

        # (',' varName)*
        while self._at_symbol(","):
            # ','
            self._advance()
            # varName
            self._define_and_advance(type=type, kind=kind)
            count += 1

        # ';'
        assert self._at_symbol(";")
        self._advance()

        return count

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
                # self.compileIf()
                raise NotImplementedError
            elif keyword == Keyword.WHILE:
                self.compileWhile()
            elif keyword == Keyword.DO:
                self.compileDo()
            elif keyword == Keyword.RETURN:
                self.compileReturn()
            else:
                raise Exception("This point should not be reachable")

    def compileLet(self):
        # 'let'
        assert self._at_keyword(keywords=(Keyword.LET,))
        self._advance()

        # varName
        name = self.jt.tkn
        kind = self.st.kindOf(name=name)
        index = self.st.indexOf(name=name)
        segment = h.kind2segment(kind)
        self._advance()

        # ('[' expression ']')?
        if self._at_symbol("["):
            # TODO
            # '['
            self._append_and_advance_symbol("[")

            # expression
            self.compileExpression()

            # ']'
            self._append_and_advance_symbol("]")

        # '='
        assert self._at_symbol("=")
        self._advance()

        # expression
        self.compileExpression()

        # ';'
        print(";;", self.jt.tkn)
        assert self._at_symbol(";")
        self._advance()

        # write assignment
        self.writer.writePop(segment=segment, index=index)

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

    def compileWhile(self):
        # 'while'
        assert self._at_keyword(keywords=(Keyword.WHILE,))
        # TODO: START HERE.
        raise Exception("START HERE!!")

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

    def compileDo(self):
        # 'do'
        assert self._at_keyword(keywords=(Keyword.DO,))
        self._advance()

        # subroutineCall
        # identifier
        assert self._at_identifier()
        identifier = self.jt.tkn
        self._advance()

        if self._at_symbol("("):  # subroutineName
            # '('
            assert self._at_symbol("(")
            self._advance()
            # expressionList, will have pushed expressions
            nArgs = self.compileExpressionList()
            # ')'
            assert self._at_symbol(")")
            self._advance()

            # call subroutine with number of expressions
            self.writer.writeCall(name=identifier, nArgs=nArgs)
        elif self._at_symbol("."):  # (className | varName)
            try:
                # try to use varName
                type = self.st.typeOf(name=identifier)
            except ValueError:
                # no var found: do className
                class_name = identifier
                # '.'
                assert self._at_symbol(".")
                self._advance()
                # subroutineName
                subroutine_name = self.jt.tkn
                self._advance()
                # '('
                assert self._at_symbol("(")
                self._advance()
                # expressionList
                nArgs = self.compileExpressionList()
                # ')'
                assert self._at_symbol(")")
                self._advance()
                # ';'
                assert self._at_symbol(";")
                self._advance()
                # call subroutine
                self.writer.writeCall(
                    name=f"{class_name}.{subroutine_name}", nArgs=nArgs
                )
                return
            self._advance()
            # '.'
            self._append_and_advance_symbol(".")
            # subroutineName
            subroutine_name = self.jt.tkn
            self._append_identifier_scope(category=Category.SUBROUTINE, verb=Verb.USE)
            # '('
            assert self._at_symbol("(")
            self._advance()
            # expressionList
            nArgs = self.compileExpressionList()
            # ')'
            assert self._at_symbol(")")
            self._advance()

            # call subroutine
            self.writer.writeCall(name=f"{type}.{subroutine_name}", nArgs=nArgs + 1)
        else:
            raise ValueError("Unrecognized syntax for subroutine call")

        # ';'
        assert self._at_symbol(";")
        self._advance()
        return

    def compileReturn(self):
        # 'return'
        assert self._at_keyword(keywords=(Keyword.RETURN,))
        self._advance()

        # expression?
        if not self._at_symbol(";"):
            self.compileExpression()

        # ';'
        assert self._at_symbol(";")
        self._advance()

        # write return
        self.writer.writeReturn()

    def compileExpression(self):
        # term - writes vm commands
        self.compileTerm()

        # (op term)*
        while self._at_symbols(symbols=h.binops):
            # op
            op = self.jt.tkn
            self._advance()
            # term - writes vm commands
            self.compileTerm()

            # apply postfix binop
            self.writer.writeArithmetic(command=h.binop_map[op])

    def compileTerm(self):
        token_type = self.jt.tokenType
        if token_type == TokenType.INT_CONST:
            self.writer.writePush(segment=Segment.CONSTANT, index=self.jt.tkn)
            self._advance()
        elif token_type == TokenType.STRING_CONST:
            # TODO
            self._advance()
        elif token_type == TokenType.KEYWORD:
            assert self.jt.keyWord in (
                Keyword.TRUE,
                Keyword.FALSE,
                Keyword.NULL,
                Keyword.THIS,
            )
            self.writer.compile_constant(self.jt.keyWord)
            self._advance()
        elif token_type == TokenType.IDENTIFIER:
            # identifier
            identifier = self.jt.tkn
            self._advance()
            if self._at_symbol("["):  # varName
                # TODO
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
                class_name = self.class_name
                subroutine_name = identifier
                # '('
                assert self._at_symbol("(")
                self._advance()
                # expressionList
                nArgs = self.compileExpressionList()
                # ')'
                assert self._at_symbol(")")
                self._advance()

                # call subroutine -- (TODO:) always method?
                name = f"{class_name}.{subroutine_name}"
                self.writer.writeCall(name=name, nArgs=nArgs + 1)
            elif self._at_symbol("."):  # (className | varName)
                try:
                    # try to use varName
                    type = self.st.typeOf(name=identifier)
                except ValueError:
                    # no var found: do className
                    class_name = identifier
                    # '.'
                    assert self._at_symbol(".")
                    self._advance()
                    # subroutineName
                    subroutine_name = self.jt.tkn
                    self._advance()
                    # '('
                    assert self._at_symbol("(")
                    self._advance()
                    # expressionList
                    nArgs = self.compileExpressionList()
                    # ')'
                    assert self._at_symbol(")")
                    self._advance()

                    # call subroutine
                    self.writer.writeCall(
                        name=f"{class_name}.{subroutine_name}", nArgs=nArgs
                    )
                    return
                self._advance()
                # '.'
                self._append_and_advance_symbol(".")
                # subroutineName
                subroutine_name = self.jt.tkn
                self._append_identifier_scope(
                    category=Category.SUBROUTINE, verb=Verb.USE
                )
                # '('
                assert self._at_symbol("(")
                self._advance()
                # expressionList
                nArgs = self.compileExpressionList()
                # ')'
                assert self._at_symbol(")")
                self._advance()

                # call subroutine
                self.writer.writeCall(name=f"{type}.{subroutine_name}", nArgs=nArgs + 1)
            else:  # varName
                name = identifier
                kind = self.st.kindOf(name=name)
                segment = h.kind2segment(kind=kind)
                index = self.st.indexOf(name=name)
                self.writer.writePush(segment=segment, index=index)

        elif token_type == TokenType.SYMBOL and self.jt.symbol == "(":
            # '(' expression ')'
            assert self._at_symbol("(")
            self._advance()
            self.compileExpression()
            assert self._at_symbol(")")
            self._advance()
        elif token_type == TokenType.SYMBOL and self.jt.symbol in ("-", "~"):
            # unaryOp
            op = self.jt.tkn
            self._advance()
            # term
            self.compileTerm()
            # apply postfix unop
            self.writer.writeArithmetic(command=h.unop_map[op])
        else:
            raise Exception("Token type not found")

    def compileExpressionList(self) -> int:
        count = 0
        # (expression (',' expression)*)?
        if not self._at_symbol(")"):
            # expression, will have pushed 1 expression
            self.compileExpression()
            count += 1
            # (',' expression)*
            while self._at_symbol(","):
                # ','
                self._advance()
                # expression, will have pushed 1 expression
                self.compileExpression()
                count += 1
        return count


def analyze_single_file(file_path):
    ce = VMCompilationEngine(file_path=file_path)
    try:
        ce.compileClass()
    except Exception as e:
        # print("\n".join(ce.output))
        raise (e)


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
