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
        elif self.parent != None:
            return self.parent.lookup(name)
        else:
            return False

    def get_type(self, name):
        if name in self.variables:
            return self.variables[name]
        return self.parent.get_type(name)

    def insert(self, name, dtype):
        if name not in self.variables:
            self.variables[name]=dtype

def type_check(obj, table):
    print (obj)
    if isinstance(obj,GoBlock):
        newtable = SymbTable(table)
        for child in obj.statements:
            if ( child is None or child == "" or (type(child) is list and len(child) == 0) ):
                continue
            type_check(child,newtable)
    
    elif isinstance(obj,GoAssign):
        if len(obj.lhs) != len(obj.rhs):
            error = True
            print ("error")
            exit()
        for child in obj.lhs:
            if table.lookup(child) == False:
                error = True
                print ("error")
                exit()
        for child in obj.rhs:
            type_check(child,table)
        for child1,child2 in zip(obj.lhs,obj.rhs):
            if type(child2) is not str:
                if table.get_type(child1) != child2.dtype:
                    error = True
                    print ("error")
                    exit()
            else:
                if table.get_type(child1) != table.get_type(child2):
                    error = True
                    print ("error")
                    exit()


    elif isinstance(obj,GoShortDecl):
        if len(obj.id_list) != len(obj.expr_list):
            error = True
            print ("error")
            exit()
        for child in obj.id_list:
            if type(child) is not str:
                error = True
                print ("error")
                exit()
        for child in obj.expr_list:
            type_check(child,table)
        
        for child1,child2 in zip(obj.id_list,obj.expr_list):
            if type(child2) is not str:
                if table.lookup(child1) == True and table.get_type(child1) != child2.dtype:
                    error = True
                    print ("error")
                    exit()
                else:
                    table.insert(child1,child2.dtype)
            else:
                if table.lookup(child1) == True and table.get_type(child1) != table.get_type(child2):
                    error = True
                    print ("error")
                    exit()
                else:
                    table.insert(child1,table.get_type(child2))

    elif isinstance(obj,GoExpression):
        type_check(obj.lhs,table)
        type_check(obj.rhs,table)
        
        if type(obj.lhs) is not str:
            dtype1 = obj.lhs.dtype
        else:
            dtype1 = table.get_type(obj.lhs)

        if type(obj.rhs) is not str:
            dtype2 = obj.rhs.dtype
        else:
            dtype2 = table.get_type(obj.rhs)

        op = obj.op
        if dtype1 != dtype2:
            error = True
            print ("error")
            exit()
        elif dtype1 == "BOOL" and op not in ["&&","||"]:
            error = True
            print ("error")
            exit()
        elif op in ["&&","||"] and dtype1 != "BOOL":
            error = True
            print ("error")
            exit()
        elif op in [">>", "<<", "&", "&^", "^", "|", "%"] and dtype1 not in INT_TYPES:
            error = True
            print ("error")
            exit()
        elif dtype1 == "STRING" and op not in ["+", "==", "!=", ">=", "<=", ">", "<"]:
            error = True
            print ("error")
            exit()
        else:
            if op in [">","<",">=","<=","==","!="]:
                obj.dtype = "BOOL"
            else:
                obj.dtype = dtype1


    elif isinstance(obj,GoBasicLit):
        obj.dtype = type(obj.item)

    elif type(obj) is list:
        for child in obj:
            type_check(child,table)

    elif type(obj) is not str and obj is not None:
        for attr in obj.__dict__:
            child = getattr(obj, attr)
            type_check(child,table)    



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

    table = SymbTable()
    type_check(tree,table)
