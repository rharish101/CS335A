#!/usr/bin/env python3
"""Lexer for Go."""
from __future__ import print_function
from ply import lex
from ply.lex import TOKEN
from collections import OrderedDict

operators = [
    ("+=", (r"\+=", "PLUSEQ")),
    ("++", (r"\+\+", "INCR")),
    ("+", (r"\+", "PLUS")),
    ("-=", (r"-=", "MINUSEQ")),
    ("--", (r"--", "DECR")),
    ("-", (r"-", "MINUS")),
    ("&^=", (r"&\^=", "BITCLREQ")),
    ("&^", (r"&\^", "BITCLR")),
    ("&=", (r"&=", "BITANDEQ")),
    ("&&", (r"&&", "LOGAND")),
    ("&", (r"&", "BITAND")),
    ("<<=", (r"<<=", "LSHIFTEQ")),
    ("<=", (r"<=", "LESSEQ")),
    ("<<", (r"<<", "LSHIFT")),
    ("<-", (r"<-", "REC")),
    ("<", (r"<", "LESS")),
    (">>=", (r">>=", "RSHIFTEQ")),
    (">=", (r">=", "GREATEQ")),
    (">>", (r">>", "RSHIFT")),
    (">", (r">", "GREAT")),
    ("%=", (r"%=", "MODEQ")),
    ("%", (r"%", "MODULO")),
    ("==", (r"==", "EQUALS")),
    ("!=", (r"!=", "NOTEQ")),
    ("(", (r"\(", "LBRACK")),
    (")", (r"\)", "RBRACK")),
    ("|=", (r"\|=", "BITOREQ")),
    ("||", (r"\|\|", "LOGOR")),
    ("|", (r"\|", "BITOR")),
    ("[", (r"\[", "LSQBRACK")),
    ("]", (r"\]", "RSQBRACK")),
    ("*=", (r"\*=", "MULTEQ")),
    ("^=", (r"\^=", "BITXOREQ")),
    ("*", (r"\*", "MULT")),
    ("^", (r"\^", "BITXOR")),
    ("{", (r"\{", "LCURLBR")),
    ("}", (r"\}", "RCURLBR")),
    ("/=", (r"/=", "DIVEQ")),
    ("/", (r"/", "DIV")),
    ("=", (r"=", "ASSIGN")),
    (":=", (r":=", "SHDECL")),
    (",", (r",", "COMMA")),
    (";", (r";", "SEMICOLON")),
    ("!", (r"!", "LOGNOT")),
    ("...", (r"\.\.\.", "TRIDOT")),
    (".", (r"\.", "DOT")),
    (":", (r":", "COLON")),
]
operators = OrderedDict(operators)

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

tokens = (
    [
        "COMMENT",
        "IMAG",
        "FLOAT",
        "INT",
        "ID",
        "KEYWORD",
        "RUNE",
        "STRING",
        "OP",
        "NEWLINES",
    ]
    + [keyword.upper() for keyword in reserved]
    + [value[1] for value in operators.values()]
)

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

op_regex = r"(" + r"|".join([value[0] for value in operators.values()]) + r")"

decimal_lit = r"[1-9][0-9]*"
octal_lit = r"0[0-7]*"
hex_lit = r"0[xX][0-9a-fA-F]+"
int_regex = r"(" + hex_lit + "|" + octal_lit + "|" + decimal_lit + ")"

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
    pass


@TOKEN(imag_regex)
def t_IMAG(t):
    # Keep track of last token for semicolon insertion on newlines
    t.lexer.last = True
    return t


@TOKEN(float_regex)
def t_FLOAT(t):
    # Keep track of last token for semicolon insertion on newlines
    t.lexer.last = True
    return t


@TOKEN(int_regex)
def t_INT(t):
    # Keep track of last token for semicolon insertion on newlines
    t.lexer.last = True
    return t


def t_ID(t):
    r"[a-zA-Z_][a-zA-Z_0-9]*"
    if t.value in reserved:
        t.type = t.value.upper()
        # Keep track of last token for semicolon insertion on newlines
        if t.value in ["break", "continue", "fallthrough", "return"]:
            t.lexer.last = True
        else:
            t.lexer.last = False
    else:  # Keep track of last token for semicolon insertion on newlines
        t.lexer.last = True
    return t


@TOKEN(rune_regex)
def t_RUNE(t):
    # Keep track of last token for semicolon insertion on newlines
    t.lexer.last = True
    return t


def t_STRING(t):
    r"(\"(\\[^\n]|[^\"\\\n])*\"|`[^`]*`)"
    # Keep track of last token for semicolon insertion on newlines
    t.lexer.last = True
    return t


@TOKEN(op_regex)
def t_OP(t):
    # Keep track of last token for semicolon insertion on newlines
    if t.value in ["++", "--", ")", "]", "}"]:
        t.lexer.last = True
    else:
        t.lexer.last = False
    t.type = operators[t.value][1]
    return t


def t_NEWLINES(t):
    r"\n+"
    # Check last token for semicolon insertion
    t.lexer.last = False
    if t.lexer.last:
        t.type = "SEMICOLON"
        return t


t_ignore = " \t"

lexer = lex.lex()
