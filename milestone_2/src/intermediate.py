#!/usr/bin/env python3
"""IR generation for Go."""
from lexer import lexer, go_traceback
from parser import parser
from go_classes import *
from argparse import ArgumentParser


class SymbTable:
    """The class for all symbol tables."""

    def __init__(self, parent=None):
        """Initialize data dictionaries containing information.

        The kinds of information stored are:
            * Variables (dict of `GoVar`): Their types
            * Structures (dict of `GoStruct`): The variables, their types and
                their tags
            * Interfaces: The methods in the interfaces and their info
            * Functions (dict of tuple (`GoFuncType`, `SymbTable`)): Their
                params, return types, and their own symbol table
            * Methods: Their params, return types, and their own symbol table
                for each struct on which they're used
            * Scopes (list of `SymbTable`): A list of the scope, using children
                symbol tables
            * Types (dict of `GoBaseType`): A dictionary of typedefs/aliases
                (NOTE: Aliases must have a reference to another type, while
                typedefs should have a copy)
            * Parent (`SymbTable`): The reference to the parent scope (if it
                exists)
        """
        self.variables = {}
        self.structures = {}
        self.interfaces = {}
        self.functions = {}
        self.methods = {}
        self.scopes = []
        self.types = []
        self.parent = parent

    def lookup(self, name):
        if name in self.variables:
            return True
        elif parent != None:
            return parent.lookup(name)
        else:
            return False

    def insert(self, name, dtype):
        if name not in self.variables:
            self.variables[name]=dtype

    def newScope(self, name):
        self.parent = name


if __name__ == "__main__":
    argparser = ArgumentParser(description="IR generator for Go")
    argparser.add_argument("input", type=str, help="input file")
    argparser.add_argument(
        "-s",
        "--symb",
        type=str,
        default=None,
        help="output symbol table file name",
    )
    argparser.add_argument(
        "-c", "--code", type=str, default=None, help="output 3AC file name"
    )
    argparser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug output"
    )
    args = argparser.parse_args()
    if args.symb is None:
        # Output filename is source filename (w/o extension) with the "csv"
        # extension
        args.symb = args.input.split("/")[-1][:-3] + ".csv"
    if args.code is None:
        # Output filename is source filename (w/o extension) with the "txt"
        # extension
        args.code = args.input.split("/")[-1][:-3] + ".txt"

    with open(args.input, "r") as go:
        input_text = go.read()
    if input_text[-1] != "\n":
        input_text += "\n"

    # Storing filename and input text for error reporting
    lexer.filename = args.input
    lexer.lines = input_text.split("\n")

    tree = parser.parse(input_text)
    if args.verbose:
        print(tree)
