import argparse
import os
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
        self.function_call_counter = 0
        self.function_name = None

    def setFileName(self, file_name: str):
        self.file_name = file_name

    def setFunctionName(self, function_name: str):
        self.function_name = function_name

    def unsetFunctionName(self):
        self.function_name = None

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

    def writeInit(self):
        self.output += h.initialize()

    def writeLabel(self, label: str):
        self.output += h.assign_label(label, self.function_name)

    def writeGoto(self, label: str):
        self.output += h.goto_label(label, self.function_name)

    def writeIf(self, label: str):
        self.output += h.if_goto_label(label, self.function_name)

    def writeCall(self, function_name: str, num_args: int):
        self.output += h.call_function(
            function_name, num_args, self.function_call_counter
        )
        self.function_call_counter += 1

    def writeReturn(self):
        self.output += h.return_from_function()
        # self.unsetFunctionName()

    def writeFunction(self, function_name: str, num_locals: int):
        self.setFunctionName(function_name)
        self.output += h.declare_function(function_name, num_locals)

    def writeLine(self, *args):
        self.output += [f"// {' '.join(args)}"]
        if args[0] in ("add", "sub", "and", "or", "eq", "gt", "lt", "neg", "not"):
            self.writeArithmetic(*args)
        elif args[0] == "label":
            self.writeLabel(*args[1:])
        elif args[0] == "goto":
            self.writeGoto(*args[1:])
        elif args[0] == "if-goto":
            self.writeIf(*args[1:])
        elif args[0] == "call":
            function_name, num_args = args[1:]
            self.writeCall(function_name, int(num_args))
        elif args[0] == "return":
            self.writeReturn()
        elif args[0] == "function":
            function_name, num_locals = args[1:]
            self.writeFunction(function_name, int(num_locals))
        elif args[0] in ("push", "pop"):
            command, segment, index = args
            self.writePushPop(command, segment, int(index))
        else:
            raise ValueError("Command in line not recognized")

    def _finish(self):
        self.output += h.finish()

    def to_disk(self, file_path: str):
        self._finish()
        with open(file_path, "w") as f:
            f.writelines(f"{line}\n" for line in self.output)
            f.write("\n")


def translate_single_file(file_path, skip_bootstrap=False):
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
    parser.add_argument("path", help="path to asm file")
    parser.add_argument("-s", "--skip-bootstrap", action="store_true", default=False)

    args = parser.parse_args()

    path = args.path
    skip_bootstrap = args.skip_bootstrap

    if os.path.isdir(path):
        translate_directory(path=path, skip_bootstrap=skip_bootstrap)
    else:
        translate_single_file(file_path=path, skip_bootstrap=skip_bootstrap)
