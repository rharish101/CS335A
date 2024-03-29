#!/usr/bin/env python3
"""Lexer for Go."""
from __future__ import print_function
from ply import lex
from ply.lex import TOKEN
from argparse import ArgumentParser
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
        "WHITESPACE",
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
    r"[a-zA-Z_][a-zA-Z_0-9]*"
    if t.value in reserved:
        t.type = t.value.upper()
    return t


@TOKEN(rune_regex)
def t_RUNE(t):
    return t


def t_STRING(t):
    r"(\"(\\[^\n]|[^\"\\\n])*\"|`[^`]*`)"
    return t


@TOKEN(op_regex)
def t_OP(t):
    t.type = operators[t.value][1]
    return t


t_NEWLINES = r"\n+"
t_WHITESPACE = r"[ \t]+"

lexer = lex.lex()


def colorify(token, config):
    """Make coloured HTML content from token."""
    content = (
        str(token.value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
        .replace(" ", "&nbsp;")
        .replace("\t", "&nbsp;" * 4)
    )
    try:
        try:
            color = config[token.type]
        except KeyError:
            if token.type.lower() in reserved:
                color = config["KEYWORD"]
            elif token.type in [value[1] for value in operators.values()]:
                color = config["OP"]
            else:
                raise KeyError
        content = '<span style="color:' + color + ';">' + content + "</span>"
    except KeyError:
        pass
    return content


def complete_html(html, file_name, light_mode=False):
    """Add html to complete the webpage."""
    fg_color = "#cccccc"
    bg_color = "#2b2b2b"
    if light_mode:
        fg_color, bg_color = bg_color, fg_color
    before = (
        """<html>
        <head>
            <title>"""
        + file_name.split("/")[-1]
        + """</title>
            <style>
                body
                {
                    color: """
        + fg_color
        + """;
                    background-color: """
        + bg_color
        + """;
                    padding: 2em;
                    font-family: monospace;
                    font-size: 1.1em;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    line-height: 1.5em;
                }
            </style>
        </head>
        <body>
    """
    )
    after = """</body>
    </html>
    """
    return before + html + after


if __name__ == "__main__":
    parser = ArgumentParser(description="Lexer for Go")
    parser.add_argument("input", type=str, help="input file")
    parser.add_argument(
        "-c",
        "--cfg",
        type=str,
        default="../tests/cfg1/colors1.cfg",
        help="config file",
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None, help="output file name"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug output"
    )
    parser.add_argument(
        "-l",
        "--light-mode",
        action="store_true",
        help="use light mode for the HTML instead of dark mode",
    )
    args = parser.parse_args()
    if args.output is None:
        args.output = args.input.split("/")[-1] + ".html"

    with open(args.input, "r") as go:
        lexer.input(go.read())

    with open(args.cfg, "r") as config_file:
        cfg_txt = config_file.read()
    if cfg_txt[-1] == "\n":
        cfg_txt = cfg_txt[:-1]
    config = {
        line.split(",")[0].strip(): line.split(",")[1].strip()
        for line in cfg_txt.split("\n")
    }

    output = ""
    while True:
        token = lexer.token()
        if not token:
            break
        if args.verbose:
            print(token)
        output += colorify(token, config)

    with open(args.output, "w") as outf:
        outf.write(complete_html(output, args.input, args.light_mode))
    print('Output file "{}" generated'.format(args.output))
