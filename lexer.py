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
    "SEMICOLON",
    "NEWLINE",
]
t_COMMENT = r"(//.*|/\*[\s\S]*\*/)"
t_STRING = r"\"[^\"\n]+\""
# t_RUNE = r""
t_OP = r"(\+|&|\+=|&=|&&|==|!=|\(|\)|-|\||-=|\|=|\|\||<|<=|\[|\]|\*|\^|\*=|\^=|<-|>|>=|\{|\}|/|<<|/=|<<=|\+\+|=|:=|,|;|%|>>|%=|>>=|--|!|\.\.\.|\.|:|&\^|&\^=)"
t_INT = r"([1-9][0-9]*|0[0-7]*|0[xX][0-9a-fA-F]+)"
t_FLOAT = r"([0-9]+\.([0-9]+)?((e|E)(\+|-)?[0-9]+)?|[0-9]+(e|E)(\+|-)?[0-9]+|\.[0-9]+((e|E)(\+|-)?[0-9]+)?)"
t_IMAG = r"([0-9]+|([0-9]+\.([0-9]+)?((e|E)(\+|-)?[0-9]+)?|[0-9]+(e|E)(\+|-)?[0-9]+|\.[0-9]+((e|E)(\+|-)?[0-9]+)?))i"
t_SEMICOLON = r";"
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
