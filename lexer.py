#!/usr/bin/env python3
"""Lexer for Go."""
from ply import lex
from ply.lex import TOKEN

tokens = [
    "COMMENT",
    "IMAG",
    "FLOAT",
    "INT",
    "KEYWORD",
    "ID",
    "RUNE",
    "STRING",
    "OP",
    "NEWLINES",
    "WHITESPACE",
]

octal_byte_value = r"\\[0-7]{3}"
hex_byte_value = r"\\x[0-9a-fA-F]{2}"
byte_value = r"(" + octal_byte_value + r"|" + hex_byte_value + r")"
little_u_value = r"\\u[0-9a-fA-F]{4}"
big_u_value = r"\\U[0-9a-fA-F]{8}"
escaped_char = r"\\(a|b|f|n|r|t|v|\\|'|\")"
unicode_value = (
    r"(.|" + little_u_value + r"|" + big_u_value + r"|" + escaped_char + ")"
)
rune_regex = r"'(" + unicode_value + r"|" + byte_value + r")'"

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
op_regex = r"(" + r"|".join(operators) + r")"

decimal_lit = r"[1-9][0-9]*"
octal_lit = r"0[0-7]*"
hex_lit = r"0[xX][0-9a-fA-F]+"
int_regex = r"(" + decimal_lit + "|" + octal_lit + "|" + hex_lit + ")"

decimals = r"[0-9]+"
exponent = r"(e|E)[\+-]?" + decimals
float_lit_1 = decimals + r"\." + r"(" + decimals + r")?(" + exponent + r")?"
float_lit_2 = decimals + exponent
float_lit_3 = r"\." + decimals + r"(" + exponent + r")?"
float_regex = (
    r"(" + float_lit_1 + r"|" + float_lit_2 + r"|" + float_lit_3 + r")"
)

imag_regex = r"(" + decimals + r"|" + float_regex + ")i"


def t_COMMENT(t):
    r"(//.*|/\*(\*(?!/)|[^*])*\*/)"
    return t


@TOKEN(imag_regex)
def t_IMAG(t):
    return t


@TOKEN(float_regex)
def t_FLOAT(t):
    return t


@TOKEN(int_regex)
def t_INT(t):
    return t


def t_ID(t):
    r"[a-zA-Z][a-zA-Z_0-9]*"
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
    if t.value in reserved:
        t.type = "KEYWORD"
    return t


@TOKEN(rune_regex)
def t_RUNE(t):
    return t


def t_STRING(t):
    r"(\"[^\"\n]+\"|`[^`\n]+`)"
    return t


@TOKEN(op_regex)
def t_OP(t):
    return t


t_NEWLINES = r"\n+"
t_WHITESPACE = r"[ \t]+"

lexer = lex.lex()
with open("/home/rharish/Programs/Go/hello.go", "r") as go:
    lexer.input(go.read())

output = ""
while True:
    token = lexer.token()
    if not token:
        break
    print(token)
    output += str(token.value)
print("=" * 10 + "OUTPUT" + "=" * 10)
print(output)
