from enum import Enum


class TokenType(str, Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"


class Keyword(str, Enum):
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    CONSTRUCTOR = "constructor"
    INT = "int"
    BOOLEAN = "boolean"
    CHAR = "char"
    VOID = "void"
    VAR = "var"
    STATIC = "static"
    FIELD = "field"
    LET = "let"
    DO = "do"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    THIS = "this"


class SymbolKind(str, Enum):
    STATIC = "static"
    FIELD = "field"
    ARG = "arg"
    VAR = "var"
    NONE = "none"


class Category(str, Enum):
    VAR = "var"
    ARGUMENT = "argument"
    STATIC = "static"
    FIELD = "field"
    CLASS = "class"
    SUBROUTINE = "subroutine"


class Verb(str, Enum):
    DEFINE = "define"
    USE = "use"
