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

    def compileClass(self):
        # 'class'
        # className
        # '{'
        # classVarDec*
        # subroutineDec*
        # '}'
        raise NotImplementedError

    def compileClassVarDec(self):
        # ('static' | 'field')
        # type
        # varName
        # (',' varName)*
        # ';'
        raise NotImplementedError

    def compileSubroutine(self):
        # ('constructor' | 'function' | 'method')
        # ('void' | type)
        # subroutineName
        # '('
        # parameterList
        # ')'
        # subroutineBody
        raise NotImplementedError

    def compileParameterList(self):
        # ((type varName) (',' type varName)*)?
        raise NotImplementedError

    def compileVarDec(self):
        # 'var'
        # type
        # varName
        # (',' varName)*
        # ';'
        raise NotImplementedError

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
        # varName
        # ('[' expression ']')?
        # '='
        # expression
        # ';'
        raise NotImplementedError

    def compileIf(self):
        # 'if'
        # '('
        # expression
        # ')'
        # '{'
        # statements
        # '}'
        # ('else' '{' statements '}')?
        raise NotImplementedError

    def compileWhile(self):
        # 'while'
        # '('
        # expression
        # ')'
        # '{'
        # statements
        # '}'
        raise NotImplementedError

    def compileDo(self):
        # 'do'
        # subroutineCall
        # ';'
        raise NotImplementedError

    def compileReturn(self):
        # 'return'
        # expression?
        # ';'
        raise NotImplementedError

    def compileExpression(self):
        # term
        # (op term)*
        raise NotImplementedError

    def compileTerm(self):
        raise NotImplementedError

    def compileExpressionList(self):
        # (expression (',' expression)*)?
        raise NotImplementedError
