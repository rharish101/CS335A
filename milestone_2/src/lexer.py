"""Lexer for Go."""
from ply import lex
from ply.lex import TOKEN
from collections import OrderedDict

operators = [
    ("++", (r"\+\+", "INCR")),
    ("+", (r"\+", "PLUS")),
    ("--", (r"--", "DECR")),
    ("-", (r"-", "MINUS")),
    ("&^", (r"&\^", "BITCLR")),
    ("&&", (r"&&", "LOGAND")),
    ("&", (r"&", "BITAND")),
    ("<=", (r"<=", "LESSEQ")),
    ("<<", (r"<<", "LSHIFT")),
    ("<-", (r"<-", "REC")),
    ("<", (r"<", "LESS")),
    (">=", (r">=", "GREATEQ")),
    (">>", (r">>", "RSHIFT")),
    (">", (r">", "GREAT")),
    ("%", (r"%", "MODULO")),
    ("==", (r"==", "EQUALS")),
    ("!=", (r"!=", "NOTEQ")),
    ("(", (r"\(", "LBRACK")),
    (")", (r"\)", "RBRACK")),
    ("||", (r"\|\|", "LOGOR")),
    ("|", (r"\|", "BITOR")),
    ("[", (r"\[", "LSQBRACK")),
    ("]", (r"\]", "RSQBRACK")),
    ("*", (r"\*", "MULT")),
    ("^", (r"\^", "BITXOR")),
    ("{", (r"\{", "LCURLBR")),
    ("}", (r"\}", "RCURLBR")),
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
    # Update line no.
    t.lexer.lineno += len(t.value.split("\n")) - 1
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
    # Update line no.
    t.lexer.lineno += len(t.value.split("\n")) - 1

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
    # Update line no.
    t.lexer.lineno += len(t.value.split("\n")) - 1

    # Check last token for semicolon insertion
    if t.lexer.last:
        t.type = "SEMICOLON"
        t.lexer.last = False
        return t


def go_traceback(token_val):
    """Print traceback for the custom error message and return position."""
    print(
        '  File "{}", line {}\n    {}'.format(
            lexer.filename, lexer.lineno, lexer.lines[lexer.lineno - 1]
        )
    )
    return (
        lexer.lexpos
        - sum(map(lambda line: len(line) + 1, lexer.lines[: lexer.lineno - 1]))
        - len(token_val)
        + 1
    )


def t_error(t):
    position = go_traceback(t.value)
    print(
        'SyntaxError: Unexpected token "{}" at position {}'.format(
            t.value, position
        )
    )
    exit(1)


t_ignore = " \t"

# =============================================================================
# NOTE:
# lexer.filename should contain the source file's name
# lexer.lines should be a list containing the source file split by newlines
# =============================================================================
lexer = lex.lex()
lexer.last = False
