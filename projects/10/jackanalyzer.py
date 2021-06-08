import argparse
import os
import re
from enum import Enum

import helpers as h


class T(str, Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"


class K(str, Enum):
    CLASS = "CLASS"
    METHOD = "METHOD"
    FUNCTION = "FUNCTION"
    CONSTRUCTOR = "CONSTRUCTOR"
    INT = "INT"
    BOOLEAN = "BOOLEAN"
    CHAR = "CHAR"
    VOID = "VOID"
    VAR = "VAR"
    STATIC = "STATIC"
    FIELD = "FIELD"
    LET = "LET"
    DO = "DO"
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    RETURN = "RETURN"
    TRUE = "TRUE"
    FALSE = "FALSE"
    NULL = "NULL"
    THIS = "THIS"


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
        code = re.sub(r"/\*.*\*/", " ", code, flags=re.DOTALL)
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
        return f"<{self.tokenType}> {self.tkn} </{self.tokenType}>"

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
    def __init__(self):
        self.output = []
        self.compare_counter = 0
        self.function_call_counter = 0
        self.function_name = None

    def compileClass(self):
        pass

    def compileClassVarDec(self):
        pass

    def compileSubroutine(self):
        pass

    def compileParameterList(self):
        pass

    def compileVarDec(self):
        pass

    def compileStatements(self):
        pass

    def compileDo(self):
        pass

    def compileLet(self):
        pass

    def compileWhile(self):
        pass

    def compileReturn(self):
        pass

    def compileIf(self):
        pass

    def compileExpression(self):
        pass

    def compileTerm(self):
        pass

    def compileExpressionList(self):
        pass

    def to_disk(self, file_path: str):
        with open(file_path, "w") as f:
            f.writelines(f"{line}\n" for line in self.output)
            f.write("\n")


def analyze_single_file(file_path):
    file_name = re.findall(r"\w+", file_path)[-2]

    p = Parser(file_path)
    cw = CodeWriter()
    cw.setFileName(file_name=file_name)

    if not skip_bootstrap:
        cw.writeInit()
    while True:
        cmd = p.cmd.split()
        cw.writeLine(*cmd)
        if p.hasMoreCommands:
            p.advance()
        else:
            break
    cw.to_disk(file_path=file_path.replace(".vm", ".asm"))


def translate_directory(path, skip_bootstrap=False):
    directory_name = re.findall(r"\w+", path)[-1]
    file_paths = [
        os.path.join(path, file) for file in os.listdir(path) if file.endswith(".vm")
    ]

    ps = [Parser(file_path) for file_path in file_paths]
    file_names = [re.findall(r"\w+", file_path)[-2] for file_path in file_paths]

    cw = CodeWriter()
    if not skip_bootstrap:
        cw.writeInit()
    for p, file_name in zip(ps, file_names):
        cw.setFileName(file_name=file_name)

        while True:
            cmd = p.cmd.split()
            cw.writeLine(*cmd)
            if p.hasMoreCommands:
                p.advance()
            else:
                break
    cw.to_disk(file_path=(os.path.join(path, directory_name + ".asm")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("path", help="path to jack file")

    args = parser.parse_args()

    path = args.path

    if os.path.isdir(path):
        translate_directory(path=path, skip_bootstrap=skip_bootstrap)
    else:
        analyze_single_file(file_path=path)
