import argparse
import re
import os


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
        if self.cmd[0] == "@":
            return "A_COMMAND"
        elif "=" in self.cmd or ";" in self.cmd:
            return "C_COMMAND"
        elif self.cmd[0] == "(" and self.cmd[-1] == ")":
            return "L_COMMAND"
        else:
            raise ValueError

    @property
    def symbol(self) -> str:
        assert self.commandType in ["A_COMMAND", "L_COMMAND"]
        if self.commandType == "A_COMMAND":
            return self.cmd[1:]
        elif self.commandType == "L_COMMAND":
            return self.cmd[1:-1]

    def _split(self):
        assert self.commandType == "C_COMMAND"
        if ";" in self.cmd:
            dc, j = self.cmd.split(";")
            if "=" in self.cmd:
                d, c = dc.split("=")
            else:
                d, c = "null", dc
        else:
            d, c = self.cmd.split("=")
            j = "null"
        return d, c, j

    @property
    def dest(self) -> str:
        assert self.commandType == "C_COMMAND"
        return self._split()[0]

    @property
    def comp(self) -> str:
        assert self.commandType == "C_COMMAND"
        return self._split()[1]

    @property
    def jump(self) -> str:
        assert self.commandType == "C_COMMAND"
        return self._split()[2]


class Code:
    dest_table = {
        "null": "000",
        "M": "001",
        "D": "010",
        "MD": "011",
        "A": "100",
        "AM": "101",
        "AD": "110",
        "AMD": "111",
    }
    comp_table = {
        "0": "101010",
        "1": "111111",
        "-1": "111010",
        "D": "001100",
        "A": "110000",
        "!D": "001101",
        "!A": "110001",
        "-D": "001111",
        "-A": "110011",
        "D+1": "011111",
        "A+1": "110111",
        "D-1": "001110",
        "A-1": "110010",
        "D+A": "000010",
        "D-A": "010011",
        "A-D": "000111",
        "D&A": "000000",
        "D|A": "010101",
    }
    comp_table_m = {k.replace("A", "M"): v for k, v in comp_table.items()}
    jump_table = {
        "null": "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111",
    }

    @staticmethod
    def dest(mnemonic: str) -> str:
        return Code.dest_table[mnemonic]

    @staticmethod
    def comp(mnemonic: str) -> str:
        if "A" in mnemonic:
            return "0" + Code.comp_table[mnemonic]
        elif "M" in mnemonic:
            return "1" + Code.comp_table_m[mnemonic]
        else:
            return "0" + Code.comp_table[mnemonic]

    @staticmethod
    def jump(mnemonic: str) -> str:
        return Code.jump_table[mnemonic]

    @staticmethod
    def A(s: str) -> str:
        s = int(s[1:])
        return f"{bin(s)[2:]:0>16}"


class SymbolTable:
    def __init__(self, table=None):
        if table is None:
            self.table = dict()
        else:
            self.table = table

    def addEntry(self, symbol: str, address: int):
        self.table[symbol] = address

    def contains(self, symbol: str):
        return symbol in self.table

    def getAddress(self, symbol: str):
        return self.table[symbol]


def initialize():
    consts = {
        "SP": 0,
        "LCL": 1,
        "ARG": 2,
        "THIS": 3,
        "THAT": 4,
        "SCREEN": 16384,
        "KBD": 24576,
    }
    table = SymbolTable(consts)
    for i in range(16):
        table.addEntry(symbol=f"R{i}", address=i)
    return table


def pass1(filepath, table):
    p = Parser(filepath)

    counter = 0
    while True:
        cmd = p.cmd
        if p.commandType in ["A_COMMAND", "C_COMMAND"]:
            counter += 1
        elif p.commandType == "L_COMMAND":
            table.addEntry(symbol=p.cmd[1:-1], address=counter)
        if p.hasMoreCommands:
            p.advance()
        else:
            break
    return table


def pass2(filepath, table):
    p = Parser(filepath)

    res = ""
    available_address = 16
    while True:
        cmd = p.cmd
        if p.commandType == "A_COMMAND":
            try:
                var = cmd[1:]
                _ = int(var)
            except:
                if not table.contains(var):
                    table.addEntry(symbol=var, address=available_address)
                    available_address += 1
                cmd = "@" + str(table.getAddress(var))
            res += Code.A(cmd)
        elif p.commandType == "C_COMMAND":
            dest, comp, jump = p.dest, p.comp, p.jump
            res += "111" + Code.comp(comp) + Code.dest(dest) + Code.jump(jump)

        if p.hasMoreCommands:
            if res[-1] != "\n":
                res += "\n"
            p.advance()
        else:
            break
    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("path", help="path to asm file")

    path = parser.parse_args().path
    saveto = re.sub(r"\.\w+$", r"_me.hack", path)

    table = initialize()
    table = pass1(filepath=path, table=table)
    res = pass2(filepath=path, table=table)

    with open(saveto, "w") as f:
        f.write(res)
