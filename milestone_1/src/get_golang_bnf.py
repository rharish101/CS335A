#!/usr/bin/env python3
"""Get Go's grammar in BNF form."""
import requests
from bs4 import BeautifulSoup
import re
import lexer

url = "https://golang.org/ref/spec"
req = requests.get(url)
soup = BeautifulSoup(req.text, features="html.parser")

text = ""
# The [8:] is for skipping lexing rules
for tag in soup.find_all("pre", {"class": "ebnf"})[8:]:
    # Remove spurious newlines so that a rule takes up one line only
    text += re.sub(r"([\|=])\s+", r"\1 ", tag.text.strip()) + "\n"


def parse_ebnf(string):
    """Parse a rule upto one level to highlight EBNF's extended features.

    If the input rule is in BNF, the rule is returned as it is. Otherwise, the rule
    is split into a list, which is returned. In this list, the part of the rule in
    BNF is kept as a string, whereas use of (), [] or {} results in a tuple of 2
    elements, where the first element is one of "(", "[" or "[", and the second
    element is the part of the rule inside the brackets as a string.
    """
    # Check for "(", "[" or "["
    match = re.search(r"[\(\[\{]", string)
    if match is None:
        return string.strip()
    left = match.span()[0]

    right = left + 1
    count = 1
    # Get the matching parenthesis
    while count > 0:
        if string[right] in ["(", "[", "{"]:
            count += 1
        elif string[right] in [")", "]", "}"]:
            count -= 1
        right += 1

    def expand(item):
        "Help avoid expanding a string with *"
        if type(item) is str:
            return [item]
        else:
            return item

    # Output is the left part, bracketed part and whatever lies to the right
    output = [
        string[:left].strip(),
        (string[left], string[left + 1 : right - 1].strip()),
        *expand(parse_ebnf(string[right:])),
    ]
    return [
        item for item in output if type(item) is not str or item.strip() != ""
    ]


def ebnf2bnf_l1(string):
    """Convert EBNF to BNF upto one level of nesting of EBNF's extended features.

    It returns a list of rules, each of which is a string. This function opens up
    an EBNF rule only upto one level of (), [] or {}.
    """
    parsed = parse_ebnf(string)
    if type(parsed) is str:
        return [string.strip()]

    # The LHS of the production
    name = string.split(":")[0].strip()
    rules = []

    # Used in naming of new non-terminals
    counts = {"(": 1, "[": 1, "{": 1}
    suffix = {"(": "Group", "[": "Opt", "{": "Rep"}
    num2str = {
        1: "One",
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
    }

    for i, item in enumerate(parsed):
        # Ignore non-extended features of EBNF
        if type(item) is tuple:
            # The name for the new non-terminal
            parsed[i] = name + suffix[item[0]] + num2str[counts[item[0]]]
            counts[item[0]] += 1
            if item[0] == "(":  # Grouping
                rules.append(
                    "{} : {}".format(parsed[i], item[1].strip()).strip()
                )
            elif item[0] == "[":  # Option ()
                rules.append("{} : {} |".format(parsed[i], item[1].strip()))
            elif item[0] == "{":  # Repetition (0 to n)
                rules.append(
                    "{} : {} {} |".format(
                        parsed[i], parsed[i], item[1].strip()
                    )
                )

    # Prepend modified form of original rule to new rules list
    return [" ".join(parsed).strip()] + rules


def ebnf2bnf(string):
    """Convert an EBNF rule to a list of BNF rules."""
    l1_results = ebnf2bnf_l1(string)
    final_rules = []
    for rule in l1_results:
        l2_results = ebnf2bnf_l1(rule)
        if len(l2_results) == 1:  # Already in BNF
            final_rules += l2_results
        else:
            final_rules += ebnf2bnf(rule)
    return final_rules


def tokenizer(string):
    """Replace terminals with their tokens."""
    token_map = {
        "identifier": "ID",
        "int_lit": "INT",
        "float_lit": "FLOAT",
        "imaginary_lit": "IMAG",
        "rune_lit": "RUNE",
        "string_lit": "STRING",
    }
    for literal in token_map.keys():
        string = string.replace(literal, token_map[literal])

    def op_keyw_rpl(reg):
        """Replace operators and keywords with their tokens."""
        string = reg.group()[1:-1]
        if string in lexer.reserved:
            return string.upper()
        elif string in lexer.operators.keys():
            return lexer.operators[string][1]

    string = re.sub(r'"[^"]*"', op_keyw_rpl, string)
    return string


# Start with "SourceFile" as start symbol
grammar = [["Start: SourceFile"]]
for item in text.split("\n"):
    if item == "":
        continue
    # item = item.lower()
    item = item.replace(" = ", " : ")
    item = re.sub(r".$", "", item)
    item = re.sub(r"\s+", r" ", item)
    item = tokenizer(item)
    item = re.sub(r"([a-z])_([a-z])", r"\1\2", item)  # Remove underscores

    rules = ebnf2bnf(item)
    total_rules = []
    # Split alternatives for each rule as per indentation
    for rule in rules:
        lhs_len = len(rule.split(":")[0])
        total_rules.append(re.sub(r" *\|", "\n" + " " * lhs_len + "|", rule))

    grammar.append(total_rules)

output_file = "bnf.txt"
with open(output_file, "w") as outf:
    outf.write("\n\n".join(["\n".join(rules) for rules in grammar]))
print("Output written to " + output_file)
