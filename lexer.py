#!/usr/bin/env python3
"""Lexer for Go."""
from ply import lex

reserved = [
    "break",
    "default",
    "func",
    "interface",
    "select",
    "case",
    "defer",
    "go",
    "map",
    "struct",
    "chan",
    "else",
    "goto",
    "package",
    "switch",
    "const",
    "fallthrough",
    "if",
    "range",
    "type",
    "continue",
    "for",
    "import",
    "return",
    "var",
]

tokens = [
    "COMMENT",
    "STRING",
    # "RUNE",
    "ID",
    "KEYWORD",
    "OP",
    "INT",
    "FLOAT",
    "IMAG",
    "NEWLINE",
]
t_COMMENT = r"(//.*|/\*[\s\S]*\*/)"
t_STRING = r"\"[^\"\n]+\""
# t_RUNE = r""

operators = [
    r"\+",
    r"&",
    r"\+=",
    r"&=",
    r"&&",
    r"==",
    r"!=",
    r"\(",
    r"\)",
    r"-",
    r"\|",
    r"-=",
    r"\|=",
    r"\|\|",
    r"<",
    r"<=",
    r"\[",
    r"\]",
    r"\*",
    r"\^",
    r"\*=",
    r"\^=",
    r"<-",
    r">",
    r">=",
    r"\{",
    r"\}",
    r"/",
    r"<<",
    r"/=",
    r"<<=",
    r"\+\+",
    r"=",
    r":=",
    r",",
    r";",
    r"%",
    r">>",
    r"%=",
    r">>=",
    r"--",
    r"!",
    r"\.\.\.",
    r"\.",
    r":",
    r"&\^",
    r"&\^=",
]
t_OP = r"(" + r"|".join(operators) + r")"

decimal_lit = r"[1-9][0-9]*"
octal_lit = r"0[0-7]*"
hex_lit = r"0[xX][0-9a-fA-F]+"
t_INT = r"(" + decimal_lit + "|" + octal_lit + "|" + hex_lit + ")"

decimals = r"[0-9]+"
exponent = r"(e|E)[\+-]?" + decimals
float_lit_1 = decimals + r"\." + r"(" + decimals + r")?(" + exponent + r")?"
float_lit_2 = decimals + exponent
float_lit_3 = r"\." + decimals + r"(" + exponent + r")?"
t_FLOAT = r"(" + float_lit_1 + r"|" + float_lit_2 + r"|" + float_lit_3 + r")"

t_IMAG = r"(" + decimals + r"|" + t_FLOAT + ")i"
t_NEWLINE = r"\n"
t_ignore = " \t"


def t_ID(t):
    r"[a-zA-Z][a-zA-Z_0-9]*"
    if t.value in reserved:
        t.type = "KEYWORD"
    return t


lexer = lex.lex()
with open("/home/rharish/Programs/Go/hello.go", "r") as go:
    lexer.input(go.read())
while True:
    token = lexer.token()
    if not token:
        break
    print(token)
