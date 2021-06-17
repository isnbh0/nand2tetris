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
    Command,
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

    __DEFAULT_STATE = "__undefined__"

    def __init__(self, file_path):
        self.jt = JackTokenizer(file_path=file_path)
        self.st = SymbolTable()
        self.writer = VMWriter(out_path=file_path.replace(".jack", ".vm"))

        self.class_name = self.__DEFAULT_STATE
        self.subroutine_return_type = self.__DEFAULT_STATE
        self.label_count = 0

    def _get_label(self, label: str):
        new_label = f"{label}_{self.label_count}"
        self.label_count += 1
        return new_label

    def _advance(self):
        self.jt.advance()

    def _at_keyword(self, keywords: t.Iterable) -> bool:
        return self.jt.tokenType == TokenType.KEYWORD and self.jt.keyWord in keywords

    def _check_keyword_and_advance(self, keywords: t.Iterable):
        assert self._at_keyword(keywords=keywords)
        self._advance()

    def _at_symbol(self, symbol: str) -> bool:
        return self.jt.tokenType == TokenType.SYMBOL and self.jt.symbol == symbol

    def _check_symbol_and_advance(self, symbol: str):
        assert self._at_symbol(symbol=symbol)
        self._advance()

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

    def _check_and_advance_type(self, with_void: bool = False):
        assert self._at_type(with_void=with_void)
        self._advance()

    def _at_identifier(self) -> bool:
        return self.jt.tokenType == TokenType.IDENTIFIER

    def _check_and_advance_identifier(self):
        assert self._at_identifier()
        self._advance()

    def _define_and_advance(
        self, type: str, kind: SymbolKind, name: t.Optional[str] = None
    ):
        if name is None:
            assert self._at_identifier()
            name = self.jt.tkn
        self.st.define(name=name, type=type, kind=kind)
        self._advance()

    def compileClass(self):
        # 'class'
        self._check_keyword_and_advance(keywords=(Keyword.CLASS,))

        # className
        assert self._at_identifier()
        self.class_name = self.jt.tkn
        self._advance()

        # '{'
        self._check_symbol_and_advance("{")

        # classVarDec*
        while self._at_keyword(keywords=(Keyword.STATIC, Keyword.FIELD)):
            self.compileClassVarDec()

        # subroutineDec*
        while self._at_keyword(
            keywords=(Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD)
        ):
            self.compileSubroutine()

        # '}'
        self._check_symbol_and_advance("}")

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
        # reset subroutine symbol table
        self.st.startSubroutine()

        # ('constructor' | 'function' | 'method')
        assert self._at_keyword(
            keywords=(Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD)
        )
        subroutine_type = self.jt.tkn
        if self._at_keyword(keywords=(Keyword.METHOD,)):
            self._define_and_advance(
                name=Keyword.THIS, type=self.class_name, kind=SymbolKind.ARGUMENT
            )
        else:
            self._advance()

        # ('void' | type)
        assert self._at_type(with_void=True)
        self.subroutine_return_type = self.jt.tkn
        self._advance()

        # subroutineName
        assert self._at_identifier()
        function_name = self.jt.tkn
        self._advance()

        # '('
        self._check_symbol_and_advance("(")

        # parameterList
        self.compileParameterList()

        # ')'
        self._check_symbol_and_advance(")")

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
            kind = SymbolKind.ARGUMENT
            self._define_and_advance(type=type, kind=kind)
            # (',' type varName)*
            while self._at_symbol(","):
                # ','
                self._advance()
                # type
                assert self._at_type(with_void=False)
                type = self.jt.tkn
                self._advance()
                # varName
                kind = SymbolKind.ARGUMENT
                self._define_and_advance(type=type, kind=kind)

    def _compileSubroutineBody(self, subroutine_type: Keyword, function_name: str):
        # '{'
        self._check_symbol_and_advance("{")

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
            # push argument 0
            self.writer.writePush(segment=Segment.ARGUMENT, index=0)
            # pop pointer 0
            self.writer.writePop(segment=Segment.POINTER, index=0)

        # statements
        self.compileStatements()

        # '}'
        self._check_symbol_and_advance("}")

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
        self._check_symbol_and_advance(";")

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
                self.compileIf()
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
        self._check_keyword_and_advance(keywords=(Keyword.LET,))

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
            self._check_symbol_and_advance("[")

            # expression
            self.compileExpression()

            # ']'
            self._check_symbol_and_advance("]")

        # '='
        self._check_symbol_and_advance("=")

        # expression
        self.compileExpression()

        # ';'
        self._check_symbol_and_advance(";")

        # write assignment
        self.writer.writePop(segment=segment, index=index)

    def compileIf(self):
        ELSE = "else"
        END_IF = "end_if"

        # 'if'
        self._check_keyword_and_advance(keywords=(Keyword.IF,))

        # '('
        self._check_symbol_and_advance("(")

        # expression
        self.compileExpression()

        # ')'
        self._check_symbol_and_advance(")")

        # if false, goto else label. otherwise continue
        self.writer.writeArithmetic(Command.NOT)
        else_label = self._get_label(label=ELSE)
        self.writer.writeIf(else_label)

        # '{'
        self._check_symbol_and_advance("{")

        # statements
        self.compileStatements()

        # '}'
        self._check_symbol_and_advance("}")

        # goto end if label
        end_if_label = self._get_label(label=END_IF)
        self.writer.writeGoto(end_if_label)

        # if false label
        self.writer.writeLabel(else_label)

        # ('else' '{' statements '}')?
        if self._at_keyword(keywords=(Keyword.ELSE,)):
            # 'else'
            self._check_keyword_and_advance(keywords=(Keyword.ELSE,))
            # '{'
            self._check_symbol_and_advance("{")
            # statements
            self.compileStatements()
            # '}'
            self._check_symbol_and_advance("}")

        # end if label
        self.writer.writeLabel(label=end_if_label)

    def compileWhile(self):
        # 'while'
        assert self._at_keyword(keywords=(Keyword.WHILE,))
        while_label = self._get_label(label=self.jt.keyWord)
        self.writer.writeLabel(while_label)
        self._advance()

        # '('
        self._check_symbol_and_advance("(")

        # expression
        self.compileExpression()

        # ')'
        self._check_symbol_and_advance(")")

        # while branch
        self.writer.writeArithmetic(Command.NOT)
        end_while_label = self._get_label(label="end_while")
        self.writer.writeIf(end_while_label)

        # '{'
        self._check_symbol_and_advance("{")

        # statements
        self.compileStatements()

        # while loop
        self.writer.writeGoto(while_label)

        # '}'
        self._check_symbol_and_advance("}")

        # end while loop
        self.writer.writeLabel(end_while_label)

    def compileDo(self):
        # 'do'
        self._check_keyword_and_advance(keywords=(Keyword.DO,))

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
                # pop and ignore result
                self.writer.writePop(segment=Segment.TEMP, index=0)
                return
            self._advance()
            # '.'
            self._check_symbol_and_advance(".")
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

        # pop and ignore result
        self.writer.writePop(segment=Segment.TEMP, index=0)

        # ';'
        self._check_symbol_and_advance(";")
        return

    def compileReturn(self):
        # 'return'
        self._check_keyword_and_advance(keywords=(Keyword.RETURN,))

        # expression?
        if not self._at_symbol(";"):
            self.compileExpression()
        else:
            # void
            assert self.subroutine_return_type == Keyword.VOID
            self.writer.writePush(segment=Segment.CONSTANT, index=0)

        # ';'
        self._check_symbol_and_advance(";")

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
                self._check_symbol_and_advance("[")
                # expression
                self.compileExpression()
                # ']'
                self._check_symbol_and_advance("]")
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
                self._check_symbol_and_advance(".")
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
