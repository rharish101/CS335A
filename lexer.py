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
    "RUNE",
    "ID",
    "KEYWORD",
    "OP",
    "INT",
    "FLOAT",
    "IMAG",
    "NEWLINE",
]
t_COMMENT = r"(//.*|/\*[\s\S]*\*/)"
t_STRING = r"(\"[^\"\n]+\"|`[^`\n]+`)"

octal_byte_value = r"\\[0-7]{3}"
hex_byte_value = r"\\x[0-9a-fA-F]{2}"
byte_value = r"(" + octal_byte_value + r"|" + hex_byte_value + r")"
little_u_value = r"\\u[0-9a-fA-F]{4}"
big_u_value = r"\\U[0-9a-fA-F]{8}"
escaped_char = r"\\(a|b|f|n|r|t|v|\\|'|\")"
unicode_value = (
    r"(.|" + little_u_value + r"|" + big_u_value + r"|" + escaped_char + ")"
)
t_RUNE = r"'(" + unicode_value + r"|" + byte_value + r")'"

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
