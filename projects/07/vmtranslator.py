import argparse
import re
from enum import Enum

import helpers as h


class C(str, Enum):
    ARITHMETIC = "ARITHMETIC"
    PUSH = "PUSH"
    POP = "POP"
    LABEL = "LABEL"
    GOTO = "GOTO"
    IF = "IF"
    FUNCTION = "FUNCTION"
    RETURN = "RETURN"
    CALL = "CALL"


class Parser:
    def __init__(self, filepath):
        with open(filepath, "r") as f:
            self.lines = f.readlines()
        self._clean_lines()

    def _clean_lines(self):
        self.lines = [re.sub(r"\s*//.*$", "", line.strip()) for line in self.lines]
        self.lines = [line for line in self.lines if line]

    @property
    def cmd(self):
        return self.lines[0]

    @property
    def hasMoreCommands(self) -> bool:
        return len(self.lines) > 1

    def advance(self):
        if self.hasMoreCommands:
            self.lines.pop(0)

    @property
    def commandType(self) -> str:
        first_word = self.cmd.split()[0]
        if first_word in ("add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"):
            return C.ARITHMETIC
        elif first_word == "push":
            return C.PUSH
        elif first_word == "pop":
            return C.POP
        elif first_word == "label":
            return C.LABEL
        elif first_word == "goto":
            return C.GOTO
        elif first_word == "if-goto":
            return C.IF
        elif first_word == "function":
            return C.FUNCTION
        elif first_word == "return":
            return C.RETURN
        elif first_word == "call":
            return C.CALL
        else:
            raise ValueError

    @property
    def arg1(self) -> str:
        if self.commandType == C.ARITHMETIC:
            return self.cmd.split()[0]
        elif self.commandType == C.RETURN:
            return NotImplementedError
        else:
            return self.cmd.split()[1]

    @property
    def arg2(self) -> int:
        if self.commandType in (C.PUSH, C.POP, C.FUNCTION, C.CALL):
            return self.cmd.split()[2]
        else:
            return NotImplementedError


class CodeWriter:
    def __init__(self):
        self.output = []
        self.compare_counter = 0

    def setFileName(self, file_name: str):
        self.file_name = file_name

    def writeArithmetic(self, command: str):
        if command in ("add", "sub", "and", "or"):
            self.output += h.binop(command)
        elif command in ("eq, gt, lt"):
            self.output += h.compare(command, s=self.compare_counter)
            self.compare_counter += 1
        elif command in ("neg", "not"):
            self.output += h.unop(command)
        else:
            raise NotImplementedError

    def writePushPop(self, command: str, segment: str, index: int):
        assert command.upper() in (C.PUSH, C.POP)
        assert segment in (
            "argument",
            "local",
            "static",
            "constant",
            "this",
            "that",
            "pointer",
            "temp",
        )

        try:
            if segment == "static":
                f = eval(f"h.{command}_static")
                self.output += f(index, self.file_name)
            else:
                f = eval(f"h.{command}_{segment}")
                self.output += f(index)
        except Exception as e:
            raise e

    def writeLine(self, *args):
        self.output += [f"// {' '.join(args)}"]
        if len(args) == 1:
            self.writeArithmetic(*args)
        elif len(args) == 3:
            command, segment, index = args
            self.writePushPop(command, segment, int(index))

    def _finish(self):
        self.output += ["(END)", "@END", "0;JMP"]

    def to_disk(self, file_path: str):
        self._finish()
        with open(file_path, "w") as f:
            f.writelines(f"{line}\n" for line in self.output)
            f.write("\n")


def main(file_path):
    file_name = re.findall(r"\w+", file_path)[-2]

    p = Parser(file_path)
    cw = CodeWriter()
    cw.setFileName(file_name=file_name)

    while True:
        cmd = p.cmd.split()
        cw.writeLine(*cmd)
        if p.hasMoreCommands:
            p.advance()
        else:
            break

    cw.to_disk(file_path=file_path.replace(".vm", ".asm"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("path", help="path to asm file")

    path = parser.parse_args().path

    main(file_path=path)
