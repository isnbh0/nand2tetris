import os
import sys

if "compiler" in sys.path[0]:
    sys.path = [os.getcwd()] + sys.path

from compiler.utils.constants import Command, Segment, Keyword


class VMWriter:
    """output module for generating VM code"""

    def __init__(self, out_path):
        self.out_path = out_path
        self.fp = open(out_path, "w")

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
        self._w("return")

    def compile_constant(self, keyword: Keyword):
        if keyword == Keyword.NULL:
            self.writePush(segment=Segment.CONSTANT, index=0)
        elif keyword == Keyword.FALSE:
            self.writePush(segment=Segment.CONSTANT, index=0)
        elif keyword == Keyword.TRUE:
            self.writePush(segment=Segment.CONSTANT, index=1)
            self.writeArithmetic(command="neg")
        elif keyword == Keyword.THIS:
            self.writePush(segment=Segment.POINTER, index=0)


# TODO: delete later
if __name__ == "__main__":
    print("a")
    with VMWriter("a.txt") as v:
        v.writePush("haha", 3)
    print("Z")
