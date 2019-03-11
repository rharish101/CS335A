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
            * Used (set of str): Set of used variable/alias/const names
            * Constants (dict of GoConstants) : Their types
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
        self.used = set()
        self.constants = {}
        self.parent = parent

    def lookup(self, name):
        if name in self.variables:
            return True
        elif self.parent is not None:
            return self.parent.lookup(name)
        else:
            return False

    def get_type(self, name):
        if name in self.variables:
            return self.variables[name]
        return self.parent.get_type(name)

    def insert_var(self, name, dtype):
        if name not in self.used:
            self.variables[name] = dtype
            self.used.add(name)
        else:
            print("Error: already declared variable name")
            exit()

    def insert_alias(self, alias, actual):
        if alias not in self.used:
            self.types[alias] = actual
            self.used.add(alias)
        else:
            print("Error: already used alias/typedef name")
            exit()

    def insert_const(self, const, dtype):
        if const not in self.used:
            self.constants[const] = dtype
            self.used.add(const)
        else:
            print("Error: already used constant name")
            exit()

    def insert_struct(self, name, struct):
        if name not in self.used:
            self.structures[name] = struct
            self.used.add(name)
        else:
            print("Error: already used Struct name")
            exit()

    # XXX INCOMPLETE need to check for other type classes
    def type_check(self, dtype1, dtype2):
        if dtype1.__class__ is not dtype2.__class__:
            print(
                'Error: Operands in expression of different type classes "{}" '
                'and "{}"'.format(dtype1.__class__, dtype2.__class__)
            )
            exit()
        if isinstance(dtype1, GoType) and isinstance(dtype1, GoType):
            name1 = dtype1.name
            name2 = dtype2.name
            if name1 != name2:
                print(
                    'Error: Operands in expression of different types "{}" and'
                    ' "{}"'.format(name1, name2)
                )
                exit()

    def insert_func(self, name, params, result):
        if name not in table.functions:
            table.functions[name] = {}
            table.functions[name]["params"] = params
            table.functions[name]["result"] = result
        else:
            print("Error: already used function name")
            exit()

    def insert_method(self, name, params, result, receiver):
        if name not in table.methods:
            table.methods[name] = {}
            table.methods[name]["params"] = params
            table.methods[name]["result"] = result
            table.methods[name]["receiver"] = receiver
        else:
            print("Error: already used method name")
            exit()


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


def symbol_table(tree, table, name=None, block_type=None):

    # ============================
    # VISHWAS
    # ============================

    error = False
    print(tree)
    # XXX UNIMPLEMENTED: storing package names and modules
    if isinstance(tree, GoSourceFile):
        # iteraing over TopLevelDeclList`
        for item in tree.declarations:
            symbol_table(item, table)

    # method declarations
    elif isinstance(tree, GoMethDecl):
        receiver = tree.receiver
        name = tree.name
        params = tree.params
        result = tree.result
        body = tree.body
        table.insert_method(name, params, result, receiver)
        symbol_table(body, table, name, "method")

    # function declarations
    elif isinstance(tree, GoFuncDecl):
        name = tree.name
        params = tree.params
        result = tree.result
        body = tree.body  # instance of GoBlock
        table.insert_func(name, params, result)
        symbol_table(body, table, name, "function")

    elif isinstance(tree, GoDecl) and tree.kind == "var":
        var_list = tree.declarations
        for item in var_list:
            # assert isinstance(item,GoVarSpec)
            lhs = item.lhs
            dtype = item.dtype
            rhs = item.rhs
            if len(lhs) != len(rhs) and len(rhs) != 0:
                error = True
                print(
                    "Error: different number of variables and values in var "
                    "declaration"
                )
                exit()
            elif len(rhs) == 0 and dtype is None:
                error = True
                print(
                    "Error: neither data type nor values given in var "
                    "declaration"
                )
                exit()
            else:
                # iterating over all expressions to evaluate their types
                evaluated_types = []
                for expr in rhs:
                    # assert isinstance(expr,GoExpression) or isinstance(expr,GoBasicLit) or type(expr) is str
                    if type(expr) is str:
                        eval_type = table.get_type(expr)
                    elif isinstance(expr, GoBasicLit):
                        eval_type = expr.dtype
                    elif isinstance(expr, GoExpression):
                        symbol_table(expr, table)
                        eval_type = expr.dtype

                    evaluated_types.append(eval_type)
                if len(rhs) != 0:
                    if dtype is None:
                        # XXX: What is the second "var"??
                        for var, eval_type in zip(var, evaluated_types):
                            table.insert_var(var, eval_type)
                    else:
                        for var, eval_type in zip(lhs, evaluated_types):
                            # If defined type is not None then check if the
                            # evaluated type is same as the defined type
                            table.type_check(dtype, eval_type)
                            print('var "{}":"{}"'.format(var, dtype))
                            table.insert_var(var, dtype)
                else:
                    for var in lhs:
                        print('var "{}":"{}"'.format(var, dtype))
                        table.insert_var(var, dtype)

    # typedef and aliases
    # XXX still need to incorporate typedef alias during type checking
    elif isinstance(tree, GoDecl) and tree.kind == "type":
        type_list = tree.declarations
        # iterating over AliasDecl and Typedef
        for item in type_list:
            # assert isinstance(item,GoTypeDefAlias)
            alias = item.alias
            actual = item.actual
            if isinstance(actual, GoStruct):
                table.insert_struct(alias, actual)
            else:
                table.insert_alias(alias, actual)

            print('typedef/alias "{}" : "{}"'.format(alias, actual))

    elif isinstance(tree, GoDecl) and tree.kind == "constant":
        const_list = tree.declarations
        for item in const_list:
            # assert isinstance(item,GoConstSpec)
            id_list = item.id_list
            dtype = item.dtype
            expr_list = item.expr
            if len(id_list) != len(expr_list):
                error = True
                print(
                    "Error: different number of variables and values in const "
                    "declaration"
                )
                exit()

            else:
                evaluated_types = []
                for expr in expr_list:
                    if type(expr) is str:
                        eval_type = table.get_type(expr)
                    elif isinstance(expr, GoBasicLit):
                        eval_type = expr.dtype
                    elif isinstance(expr, GoExpression):
                        symbol_table(expr, table)
                        eval_type = expr.dtype
                    evaluated_types.append(eval_type)

                if dtype is None:
                    for var, eval_type in (expr_list, evaluated_types):
                        # XXX: What is "const"??
                        table.insert_const(const, eval_type)
                else:
                    for const, eval_type in zip(id_list, evaluated_types):
                        table.type_check(dtype, eval_type)
                        print('const "{}":"{}"'.format(const, dtype))
                        table.insert_const(const, dtype)
                        # adding to list of variables so that const can be used as variables except they can't be assigned to some other value. Need to implement this check
                        # table.insert_var(const,dtype)

    elif isinstance(tree, GoBlock):
        statement_list = tree.statements
        child_table = SymbTable(table)
        if not name:
            table.scopes.append(child_table)
        elif block_type == "function":
            table.functions[name]["body"] = child_table
        elif block_type == "method":
            table.methods[name]["body"] = child_table
        for statement in statement_list:
            if (
                statement is None
                or statement == ""
                or (type(statement) is list and len(statement) == 0)
            ):
                continue
            symbol_table(statement, child_table)

    elif isinstance(tree, GoAssign):
        lhs = tree.lhs
        rhs = tree.rhs
        if len(lhs) != len(rhs):
            error = True
            print(
                "Different number of variables and values in assign operation"
            )
            exit()
        for var in lhs:
            if isinstance(var, GoPrimaryExpr):
                symbol_table(var, table)
            elif not table.lookup(var):
                error = True
                print('"{}" not declared before use'.format(var))
                exit()

        for var, expr in zip(lhs, rhs):
            print('assign: "{}" : "{}"'.format(var, expr))
            if isinstance(var, GoPrimaryExpr):
                dtype1 = table.get_type(var.lhs).dtype
            else:
                dtype1 = table.get_type(var)

            if type(expr) is str:
                dtype2 = table.get_type(expr)
            elif isinstance(expr, GoBasicLit):
                dtype2 = expr.dtype
            elif isinstance(expr, GoExpression):
                symbol_table(expr, table)
                dtype2 = expr.dtype

            table.type_check(dtype1, dtype2)

    elif isinstance(tree, GoShortDecl):
        id_list = tree.id_list
        expr_list = tree.expr_list
        if len(id_list) != len(expr_list):
            error = True
            print(
                "Different number of variables and values in short declaration"
            )
            exit()
        for var in id_list:
            if type(var) is not str:
                error = True
                print("Syntax error, '{}'".format(var))
                exit()

        for var, expr in zip(id_list, expr_list):
            print('short decl: "{}" : "{}"'.format(var, expr))
            if type(expr) is str:
                table.insert_var(var, table.get_type(expr))
            elif isinstance(expr, GoBasicLit):
                table.insert_var(var, expr.dtype)
            elif isinstance(expr, GoExpression):
                symbol_table(expr, table)
                # print(expr.dtype)
                table.insert_var(var, expr.dtype)
            elif isinstance(expr, GoCompositeLit):  # Arrays
                symbol_table(expr, table)
                table.insert_var(var, expr.dtype)
                print("type = '{}' , {}'".format(var, expr.dtype))

    elif isinstance(tree, GoExpression):
        lhs = tree.lhs
        op = tree.op
        rhs = tree.rhs
        symbol_table(lhs, table)
        symbol_table(rhs, table)
        print('exp: lhs "{}", rhs "{}"'.format(lhs, rhs))

        # XXX INCOMPLETE : need to handle cases for array types, struct types,
        # interfaces, function, pointer
        if type(lhs) is str:  # variable
            dtype1 = table.get_type(lhs)
        elif isinstance(lhs, GoExpression):
            dtype1 = lhs.dtype
        elif isinstance(lhs, GoBasicLit):
            dtype1 = lhs.dtype

        if type(rhs) is str:  # variable
            dtype2 = table.get_type(rhs)
        elif isinstance(rhs, GoExpression):
            dtype2 = rhs.dtype
        elif isinstance(rhs, GoBasicLit):
            dtype2 = rhs.dtype

        print('exp lhs: "{}", rhs: "{}"'.format(dtype1, dtype2))

        if dtype1.__class__ is not dtype2.__class__:
            error = True
            print(
                "Error: Operands in expression of different type classes '{}' "
                "and '{}'".format(dtype1.__class__, dtype2.__class__)
            )
            exit()

        # XXX INCOMPLETE need to check for other type classes
        if isinstance(dtype1, GoType) and isinstance(dtype2, GoType):
            name1 = dtype1.name
            name2 = dtype2.name
            if name1 != name2:
                print(
                    "Error: Operands in expression of different types '{}' and"
                    " '{}'".format(name1, name2)
                )
                exit()
            if name1 == "bool" and op not in ["&&", "||"]:
                error = True
                print("invalid operator for bool operands")
                exit()
            elif op in ["&&", "||"] and name1 != "bool":
                error = True
                print(
                    "invalid operand types '{}' and '{}' for bool operator".format(
                        name1, name2
                    )
                )
                exit()
            # XXX: What is INT_TYPES?
            elif (
                op in [">>", "<<", "&", "&^", "^", "|", "%"]
                and name1 not in INT_TYPES
            ):
                error = True
                print("error")
                exit()
            elif name1 == "string" and op not in [
                "+",
                "==",
                "!=",
                ">=",
                "<=",
                ">",
                "<",
            ]:
                error = True
                print("invalid operator for string type")
                exit()
            else:
                if op in [">", "<", ">=", "<=", "==", "!="]:
                    tree.dtype = GoType("bool")
                else:
                    tree.dtype = GoType(name1)

    elif isinstance(tree, GoIf):
        # New symbol table needed as stmt is in the scope of both if and else
        newtable = SymbTable(table)
        symbol_table(tree.stmt, newtable)
        symbol_table(tree.cond, newtable)

        if (
            not isinstance(tree.cond, GoExpression)
            or not isinstance(tree.cond.dtype, GoType)
            or tree.cond.dtype.name != "bool"
        ):
            error = True
            print("Error: If condition is not evaluating to bool")
            exit()
        symbol_table(tree.inif, newtable)
        symbol_table(tree.inelse, newtable)
        table.scopes.append(newtable)

    # XXX Issue with grammar when simple statement in switch case, incorrect
    # parse tree bein generated
    elif isinstance(tree, GoCaseClause):
        symbol_table(tree.kind, table)
        symbol_table(tree.expr_list, table)
        newtable = SymbTable(table)
        symbol_table(tree.stmt_list, newtable)
        table.scopes.append(newtable)

    # XXX UN-IMPLEMENTED
    elif isinstance(tree, GoFor):
        symbol_table(tree.clause)
        symbol_table(tree.infor)

    elif isinstance(tree, GoForClause):
        symbol_table(tree.init, table)
        symbol_table(tree.expr)
        symbol_table(tree.post)

        if not isinstance(tree.init, GoAssign) and not isinstance(
            tree.init, GoShortDecl
        ):
            error = True
            print("Error in for loop Initialization")
            exit()

    elif isinstance(tree, GoArray):
        symbol_table(tree.length, table)
        symbol_table(tree.dtype, table)

        length = tree.length

        if length == "variable":
            return
        elif type(length) is str:  # variable
            dtype = table.get_type(length)
        elif isinstance(length, GoExpression):
            dtype = length.dtype
        elif isinstance(length, GoBasicLit):
            dtype = length.dtype

        if isinstance(dtype, GoType) and dtype.name != "int":
            print("array length must be an integer")
            exit()

    elif isinstance(tree, GoIndex):
        symbol_table(tree.index, table)
        index = tree.index
        if type(index) is str:  # variable
            dtype = table.get_type(index)
        elif isinstance(index, GoExpression):
            dtype = index.dtype
        elif isinstance(index, GoBasicLit):
            dtype = index.dtype

        if dtype.name != "int":
            print("array index must be an integer")
            exit()

    elif isinstance(tree, GoPrimaryExpr):

        symbol_table(tree.lhs, table)
        symbol_table(tree.rhs, table)

        if isinstance(tree.rhs, GoIndex):
            print("a= '{}'".format(tree.lhs))
            if not table.lookup(tree.lhs):
                error = True
                print("'{}' array not declared".format(tree.lhs))
                exit()
            elif not isinstance(table.get_type(tree.lhs), GoArray):
                error = True
                print("'{}' not array".format(table.get_type(tree.lhs)))
                exit()
            print("dtype: '{}'".format(table.get_type(tree.lhs)))
            tree.dtype = (table.get_type(tree.lhs)).dtype
            print("dtype: '{}'".format(table.get_type(tree.lhs)))

    # XXX To be done later : check number of elements in array same as that
    # specified
    elif isinstance(tree, GoCompositeLit):
        symbol_table(tree.dtype, table)
        symbol_table(tree.value, table)

        if isinstance(tree.dtype, GoArray):
            dtype = tree.dtype.dtype
            for child in tree.value:
                if type(child.element) is str:  # variable
                    element_type = table.get_type(child.element)
                elif isinstance(child.element, GoExpression):
                    element_type = child.element.dtype
                elif isinstance(child.element, GoBasicLit):
                    element_type = child.element.dtype

                if dtype.name != element_type.name:
                    print(
                        "Conflicting types in array, '{}', '{}'".format(
                            dtype.name, element_type.name
                        )
                    )
                    exit()


table = SymbTable()
symbol_table(tree, table)
