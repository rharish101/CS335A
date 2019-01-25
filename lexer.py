"""Lexer for Go."""
from ply import lex

tokens = (
    "COMMENTS",
    "STRING",
    # "RUNE",
    "ID",
    "OP",
    "INT",
    "FLOAT",
    "IMAG",
    "SEMICOLONS",
)
t_COMMENTS = r"(//.*|/\*[\s\S]*\*/)"
t_STRING = r"\"[^\"\n]+\""
t_RUNE = r""
t_OP = r""
t_INT = r""
t_FLOAT = r""
t_IMAG = r""
t_SEMICOLONS = r""

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


def t_ID(t):
    r"[a-zA-Z][a-zA-Z_0-9]"
    if t.value in reserved:
        t.type = t.value.upper()
    return t


lexer = lex.lex()
lexer.input()
while True:
    token = lexer.token()
    if not token:
        break
    print(token)
