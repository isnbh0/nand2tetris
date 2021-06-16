import os
import sys

if "compiler" in sys.path[0]:
    sys.path = [os.getcwd()] + sys.path

import re

from compiler.utils.constants import Command, Segment
import compiler.utils.helpers as h


class VMWriter:
    """output module for generating VM code"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.fp = open(file_path, "w")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.fp.close()
    
    def _w(self, s: str):
        self.fp.write(f"{s}\n")

    def writePush(self, segment: Segment, index: int):
        self._w(f"push {segment} {index}")

    def writePop(self, segment: Segment, index: int):
        self._w(f"pop {segment} {index}")

    def writeArithmetic(self, command: Command):
        self._w(f"{command}")

    def writeLabel(self, label: str):
        self._w(f"label {label}")

    def writeGoto(self, label: str):
        self._w(f"goto {label}")

    def writeIf(self, label: str):
        self._w(f"if-goto {label}")

    def writeCall(self, name: str, nArgs: int):
        self._w(f"call {name} {nArgs}")

    def writeFunction(self, name: str, nLocals: int):
        self._w(f"function {name} {nLocals}")

    def writeReturn(self):
        self._w(f"return")


# TODO: delete later
if __name__ == "__main__":
    print("a")
    with VMWriter("a.txt") as v:
        v.writePush("haha", 3)
    print("Z")
