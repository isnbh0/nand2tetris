from collections import Counter
from dataclasses import dataclass
from os import name
import re
import typing as t

from compiler.utils.constants import SymbolKind


@dataclass
class Entry:
    type: str
    kind: t.Union[SymbolKind.STATIC, SymbolKind.FIELD, SymbolKind.ARG, SymbolKind.VAR]
    index: int = 0


class SymbolTable:
    """symbol table"""

    def __init__(self):
        self.c: t.Dict[str, Entry] = dict()
        self.s: t.Dict[str, Entry] = dict()
        self.tables = (self.s, self.c)

    def startSubroutine(self):
        self.s = []

    def _get_table(self, kind) -> t.List[Entry]:
        return self.c if kind in (SymbolKind.STATIC, SymbolKind.FIELD) else self.s

    def define(
        self,
        name: str,
        type: str,
        kind: t.Union[
            SymbolKind.STATIC, SymbolKind.FIELD, SymbolKind.ARG, SymbolKind.VAR
        ],
    ):
        table = self._get_table(kind)
        i = self.varCount(kind)
        table[name] = Entry(type=type, kind=kind, index=i)

    def varCount(self, kind: SymbolKind) -> int:
        table = self._get_table(kind)
        return Counter([e.kind for e in table.values()])[kind]

    def _get_attribute(self, name: str, attr: str) -> t.Union[SymbolKind, str, int]:
        for table in self.tables:
            if name in table:
                entry = table[name]
                return getattr(entry, attr)
        raise ValueError("Symbol not found.")

    def kindOf(self, name: str) -> SymbolKind:
        return self._get_attribute(name=name, attr="kind")

    def typeOf(self, name: str) -> str:
        return self._get_attribute(name=name, attr="type")

    def indexOf(self, name: str) -> int:
        return self._get_attribute(name=name, attr="index")
