#!/usr/bin/env python3
"""IR generation for Go."""
from lexer import lexer
from parser import parser
from go_classes import *
from argparse import ArgumentParser
from copy import deepcopy
import csv
import subprocess
import os


INT_TYPES = [
    "int",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "byte",
    "rune",
]


class SymbTable:
    """The class for all symbol tables."""

    def __init__(self, parent=None, use=None):
        """Initialize data dictionaries containing information.

        The kinds of information stored are:
            * Variables (dict of `GoVar`): Their types
            * Structures (dict of `GoStruct`): The variables, their types and
                their tags
            * Interfaces (dict of `GoInterfaceType`): The methods in the
                interfaces and their info
            * Functions (dict): Their params, return types, and their own
                symbol table as a dict
            * Methods (dict): Their params, return types, and their own symbol
                table as a dict for each struct on which they're used. Indexing
                is done by a tuple of (name, receiver).
            * Scopes (list of `SymbTable`): A list of the scope, using children
                symbol tables
            * Types (dict of `GoBaseType`): A dictionary of typedefs/aliases
                (NOTE: Aliases must have a reference to another type, while
                typedefs should have a copy)
            * Used (set of str): Set of used variable/alias/const names
            * Constants (dict of GoConstants) : Their types
            * Imports (dict of `GoImportSpec`): The imports and their aliases
            * Parent (`SymbTable`): The reference to the parent scope (if it
                exists)
        """
        self.variables = {}
        self.structures = {}
        self.interfaces = {}
        self.functions = {}
        self.methods = {}
        self.scopes = []
        self.types = {}
        self.used = set()
        self.constants = {}
        self.imports = {}
        self.parent = parent

        if use is None:
            if self.parent:
                self.offset = self.parent.offset
            else:
                self.offset = 0
        elif use == "function" or use == "method":
            self.offset = 0

        print("offset assigned: {}".format(self.offset))

    def lookup(self, name):
        if name in self.variables:
            return True
        elif self.parent is not None:
            return self.parent.lookup(name)
        else:
            return False

    def get_actual(self, alias):
        if alias in self.types:
            return self.types[alias]
        elif self.parent:
            return self.parent.get_actual(alias)
        else:
            return None

    # TODO Need to handle dynamic entities like linked lists, strings etc
    def get_size(self, dtype, check=False):
        # assert isinstance(dtype, GoType)
        # if isinstance(dtype,GoType):
        if isinstance(dtype, GoStruct):
            return self.struct_size(dtype.name)
        name = dtype.name
        print("SIZE: getting size of {}".format(name))
        value = dtype.value
        if name in ["uint8", "int8", "byte"]:
            size = 1
        elif name in ["uint16", "int16"]:
            size = 2
        elif name in [
            "uint32",
            "int32",
            "float32",
            "rune",
            "int",
            "uint",
            "uintptr",
        ]:
            size = 4
        elif name in ["unint64", "int64", "complex64", "float64", "float"]:
            size = 8
        elif name == "complex128":
            size = 16
        elif name == "string":
            # print("NAME XXXX{}".format(value))
            if value is None:
                size = 0
            else:
                size = len(value)
            # print("Warning: size of string is not defined")
        else:
            actual_type = self.get_actual(name)
            if actual_type is None:
                if check is False:
                    print("Error:'{}' is unregistered dtype".format(name))
                    exit()
                else:
                    return None
            temp = actual_type
            while temp is not None:
                if isinstance(temp, GoType):
                    actual_type = temp
                    temp = self.get_actual(actual_type.name)

            actual_type.value = value
            size = self.get_size(actual_type)
        return size

    def get_type(self, name, use="variable/array/struct"):
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get_type(name)
        else:
            print(
                "Error: Attempt to use '{}': undeclared '{}' name ".format(
                    name, use
                )
            )
            exit()

    def get_func(self, name, info):
        if name in self.functions:
            return self.functions[name][info]
        elif self.parent:
            return self.parent.get_func(name, info)
        else:
            print(
                "Error: Attempt to use '{}': undeclared function".format(name)
            )

    def get_method(self, name, info):
        if name in self.methods:
            return self.methods[name][info]
        elif self.parent:
            return self.parent.get_method(name, info)
        else:
            print(
                "Error: Attempt to use undeclared method '{}' on struct '{}'".format(
                    name[0], name[1]
                )
            )
            exit()

    def insert_var(self, name, dtype, use="variable"):
        if type(name) is not str:
            print("Error: Variable name {} is not string".format(name))
            exit()
        dtype = deepcopy(dtype)
        if name not in self.used:
            if isinstance(dtype, GoType):
                # type_name = dtype.name
                dtype.size = self.get_size(dtype)
                print(
                    "previous offset {}, size {}".format(
                        self.offset, dtype.size
                    )
                )
                dtype.offset = self.offset + dtype.size
                self.offset = dtype.offset

            # TODO need to handle array os structures seperately
            elif isinstance(dtype, GoArray):
                print("ARRAY DTYPE {}".format(dtype.dtype))
                assert isinstance(dtype.final_type, GoType)
                dtype.size = dtype.size * self.get_size(dtype.final_type)
                dtype.offset = self.offset + dtype.size
                self.offset = dtype.offset
                print("ARRAY SIZE: {}".format(dtype.size))

            elif isinstance(dtype, GoStruct):
                dtype.offset = self.offset + dtype.size
                self.offset = dtype.offset
                print("STRUCT SIZE {}".format(dtype.size))

            elif isinstance(dtype, GoPointType):
                dtype.size = 4
                dtype.offset = self.offset + 4
                self.offset = dtype.offset

            self.variables[name] = dtype
            self.used.add(name)
        else:
            print("Error: Already declared '{}' name '{}'".format(use, name))
            exit()

    def insert_alias(self, alias, actual):
        if alias not in self.used:
            self.types[alias] = actual
            self.used.add(alias)
        else:
            print("Error: Already used alias/typedef name '{}'".format(name))
            exit()

    def helper_get_struct(self, struct_name, field):
        if struct_name in self.structures:
            if field is None:
                types = []
                for item in self.structures[struct_name].vars:
                    print("item {}".format(item))
                    types.append(item[1])
                return types

            for item in self.structures[struct_name].vars:
                if field == item[0]:
                    return item[1]
            else:
                print(
                    "Error: Attempt to access unexisting field '{}' on struct '{}'".format(
                        field, struct_name
                    )
                )
                exit()
        elif self.parent:
            return self.parent.get_struct(struct_name, field)
        else:
            print(
                "Error: Attempt to access undeclared struct '{}'".format(
                    struct_name
                )
            )
            exit()

    def get_struct(self, struct_name, field=None):
        actual_name = self.get_actual(struct_name)
        if actual_name is not None:
            if isinstance(actual_name, GoType):
                struct_name = actual_name.name
        return self.helper_get_struct(struct_name, field)

    def check_struct(self, struct_name, type_list):
        actual_types = self.get_struct(struct_name)

        if len(actual_types) is not len(type_list):
            print(
                "Error: Invalid number of values given for structure initialization"
            )
            exit()
        size = 0
        for actual, given in zip(actual_types, type_list):
            print(
                "actual type'{}', give types '{}'".format(
                    actual.dtype.name, given
                )
            )
            if type(given) is list:
                size += self.check_struct(actual.dtype.name, given)
                # self.check_struct(actual.dtype.name, given)
            else:
                assert isinstance(actual, GoVar)
                assert isinstance(given, GoType)
                self.type_check(
                    actual.dtype, given, "structure initialization"
                )
                size += self.get_size(given)
        return size

    def struct_size(self, struct_name):
        actual_types = self.get_struct(struct_name)
        size = 0
        for actual in actual_types:
            # print("ACTUAL {}".format(actual.dtype.name))
            a = self.get_size(actual.dtype, True)
            if a is None:
                size += self.struct_size(actual.dtype.name)
            else:
                size += a
        return size

    def insert_const(self, const, dtype):
        if const not in self.used:
            self.constants[const] = dtype
            self.used.add(const)
        else:
            print("Error: Already used constant name '{}'".format(name))
            exit()

    def insert_struct(self, name, struct):
        if name not in self.used:
            self.structures[name] = struct
            self.used.add(name)
        else:
            print("Error: Already used struct name '{}'".format(name))
            exit()

    def insert_interface(self, name, interface):
        if name not in self.used:
            self.interfaces[name] = interface
            self.used.add(name)
        else:
            print("Error: Already used interface name '{}'".format(name))
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
        for rec in receiver:
            # Indexing by name and receiver
            assert isinstance(rec, GoParam)
            key = (name, rec.dtype.name)
            # print("struct key: '{}', '{}'".format(name,rec.name))
            if key not in table.methods:
                table.methods[key] = {}
                table.methods[key]["params"] = params
                table.methods[key]["result"] = result
            else:
                print("Error: already used method name")
                exit()

    def nested_module(self, module):
        parent = module.parent
        child = module.child
        assert type(child) is str
        # print("child '{}', parent '{}'".format(child, parent))
        if isinstance(parent, GoFromModule):
            assert isinstance(struct_name, GoVar)
            struct_name = (self.nested_module(parent)).dtype
            return self.get_struct(struct_name, child)
        elif type(parent) is str:
            struct_object = self.get_type(parent)
            struct_name = struct_object.name
            return self.get_struct(struct_name, child)

    def type_check(
        self, dtype1, dtype2, use="", use_name=None, param_name=None
    ):
        if dtype1.__class__ is not dtype2.__class__:
            print(
                "Error: Operands in '{}' of different type classes '{}' and '{}'".format(
                    use, dtype1.__class__, dtype2.__class__
                )
            )
            exit()

        if isinstance(dtype1, GoType) and isinstance(dtype1, GoType):
            name1 = dtype1.name
            name2 = dtype2.name
            print("name1 '{}', name2 '{}'".format(name1, name2))

            # handles recursive typdef/aliases
            actual1 = self.get_actual(name1)
            actual2 = self.get_actual(name2)

            while actual1 is not None:
                if isinstance(actual1, GoType):
                    name1 = actual1.name
                    actual1 = self.get_actual(actual1.name)

            while actual2 is not None:
                if isinstance(actual2, GoType):
                    name2 = actual2.name
                    actual2 = self.get_actual(actual2.name)

            for name in [name1, name2]:
                if name not in INT_TYPES and name not in [
                    "float",
                    "float32",
                    "float64",
                    "complex",
                    "byte",
                    "complex64",
                    "complex128",
                    "string",
                    "unintptr",
                ]:
                    print("Error:'{}' is unregistered dtype".format(name))
                    exit()
            if dtype1.basic_lit or dtype2.basic_lit:
                if name1 in INT_TYPES:
                    name1 = "int"
                elif name1 in ["float32", "float64", "float"]:
                    name1 = "float"
                elif name1 in ["complex64", "complex128", "complex"]:
                    name1 = "complex"

                if name2 in INT_TYPES:
                    name2 = "int"
                elif name2 in ["float32", "float64", "float"]:
                    name2 = "float"
                elif name2 in ["complex64", "complex128", "complex"]:
                    name2 = "complex"

            if name1 != name2:
                # print("'{}', '{}'".format(name1,name2))
                if use == "function call":
                    print(
                        "Error: Mismatch type of param '{}' in function call of '{}'".format(
                            param_name, use_name
                        )
                    )
                elif use == "array conflicts":
                    print(
                        "Error: Value of '{}' type given to array '{}' instead of '{}' type".format(
                            dtype2.name, use_name, dtype1.name
                        )
                    )
                else:
                    print(
                        'Error: Operands in "{}" of different types "{}" and '
                        '"{}"'.format(use, name1, name2)
                    )
                exit()

        if isinstance(dtype1, GoPointType) and isinstance(dtype2, GoPointType):
            self.type_check(dtype1.dtype, dtype2.dtype)


# Global variable for labelling statements, ensuring unique variables, etc.
global_count = 0


def symbol_table(
    tree,
    table,
    name=None,
    block_type=None,
    store_var="",
    scope_label="",
    insert=False,
):
    """Do DFS to traverse the parse tree, construct symbol tables, 3AC.

    Args:
        tree: The object representing the current node
        table (`SymbTable`): The symbol table to be written to
        name (str): The name of the current function/method node
        block_type (str): To differentiate b/w regular blocks and functions or
            methods
        store_var (str): The variable in which the 3AC results (for
            expressions) will be stored
        insert (bool): Whether to insert the function/method or not
    """
    global global_count
    ir_code = ""
    DTYPE = None

    error = False
    print(tree)

    # XXX If code enters here then it looks only for variables, hence
    # we need to make sure that sybmol table is not called uneccessary strings
    # otherwise code will fail
    if type(tree) is str:  # variable
        print("STR: '{}'".format(tree))
        DTYPE = table.get_type(tree)
        if store_var == "":
            ir_code = tree
        else:
            ir_code = "{} = {}\n".format(store_var, tree)

    elif isinstance(tree, GoBasicLit):
        DTYPE = tree.dtype
        if store_var == "":
            ir_code = str(tree.item)
        else:
            ir_code = "{} = {}\n".format(store_var, tree.item)
        assert isinstance(DTYPE, GoType)

    elif isinstance(tree, GoFromModule):
        parent = tree.parent
        child = tree.child
        print("parent '{}', child '{}'".format(parent, child))

        # currently handles accessing a field of a struct
        if type(parent) is str:
            assert type(child) is str
            struct_name = table.get_type(parent).name
            DTYPE = table.get_struct(struct_name, child).dtype

        # handles nesting of structs
        elif isinstance(parent, GoFromModule):
            struct_name = (table.nested_module(parent)).dtype.name
            print("struct name '{}'".format(struct_name))
            DTYPE = table.get_struct(struct_name, child).dtype

        if store_var == "":
            ir_code = str(tree.name)
        else:
            ir_code = "{} = {}\n".format(store_var, tree.name)

    # TODO: Store modules
    elif isinstance(tree, GoSourceFile):
        # iterating over package imports
        for item in tree.imports:
            table.imports[item.import_as] = item
        # iteraing over TopLevelDeclList
        for item in tree.declarations:
            ir_code += symbol_table(
                item, table, name, block_type, scope_label=scope_label
            )[1]
        DTYPE = None

    # method declarations
    elif isinstance(tree, GoMethDecl):
        receiver = tree.receiver
        name = tree.name
        params = tree.params
        result = tree.result
        body = tree.body
        table.insert_method(name, params, result, receiver)
        # for rec in receiver:
        #     class_name = rec.dtype.name
        #     # print("XXX '{}' '{}'".format(rec.name,rec.dtype.name))
        #     symbol_table(body, table, (name, class_name), "method", scope_label = scope_label,insert = True)

        for rec in receiver:
            ir_code = "func begin {}_{}\n".format(name, rec.name)
            ir_code += symbol_table(
                body,
                table,
                (name, rec),
                "method",
                scope_label=scope_label,
                insert=True,
            )[1]
            ir_code += "func end\n"
        DTYPE = None

    # function declarations
    elif isinstance(tree, GoFuncDecl):
        name = tree.name
        params = tree.params
        result = tree.result
        body = tree.body  # instance of GoBlock
        table.insert_func(name, params, result)
        ir_code = "func begin {}\n".format(name)
        ir_code += symbol_table(
            body, table, name, "function", scope_label=scope_label, insert=True
        )[1]
        if result is None:
            ir_code += "return\n"
        ir_code += "func end\n"
        DTYPE = None

    elif isinstance(tree, GoDecl) and tree.kind == "var":
        depth_num = global_count
        global_count += 1

        var_list = tree.declarations
        for item in var_list:
            # assert isinstance(item,GoVarSpec)
            lhs = item.lhs
            dtype = item.dtype
            rhs = item.rhs
            # print("var dtype {}".format(dtype.name))
            if len(lhs) != len(rhs) and len(rhs) != 0:
                print(
                    "Error: different number of variables and values in var "
                    "declaration"
                )
                exit()
            elif len(rhs) == 0 and dtype is None:
                print(
                    "Error: neither data type nor values given in var "
                    "declaration"
                )
                exit()
            else:
                # iterating over all expressions to evaluate their types
                evaluated_types = []
                for i, expr in enumerate(rhs):
                    expr_dtype, expr_code = symbol_table(
                        expr,
                        table,
                        name,
                        block_type,
                        store_var="__decl{}_{}".format(i, depth_num),
                        scope_label=scope_label,
                    )
                    ir_code += expr_code
                    evaluated_types.append(expr_dtype)
                if len(rhs) != 0:
                    for i, (var, eval_type) in enumerate(
                        zip(lhs, evaluated_types)
                    ):
                        ir_code += "{} = __decl{}_{}\n".format(
                            var, i, depth_num
                        )
                        if dtype is not None:
                            # If defined type is not None then check if the
                            # evaluated type is same as the defined type
                            table.type_check(
                                dtype, eval_type, "variable declaration"
                            )
                            print('var "{}":"{}"'.format(var, dtype))
                            if isinstance(eval_type, GoType):
                                dtype.value = eval_type.value
                            table.insert_var(var, dtype)
                        else:
                            table.insert_var(var, eval_type)
                else:
                    for var in lhs:
                        print('var "{}":"{}"'.format(var, dtype))
                        ir_code += "{} = 0\n".format(var)
                        table.insert_var(var, dtype)
        DTYPE = None

    # typedef and aliases
    # XXX still need to incorporate typedef alias during type checking
    elif isinstance(tree, GoDecl) and tree.kind == "type":
        type_list = tree.declarations
        # iterating over AliasDecl and Typedef
        for item in type_list:
            assert isinstance(item, GoTypeDefAlias)
            alias = item.alias
            actual = item.actual
            if isinstance(actual, GoStruct):
                table.insert_struct(alias, actual)
            elif isinstance(actual, GoInterfaceType):
                table.insert_interface(alias, actual)
            else:
                table.insert_alias(alias, actual)

            print('typedef/alias "{}" : "{}"'.format(alias, actual))
        DTYPE = None

    elif isinstance(tree, GoDecl) and tree.kind == "constant":
        depth_num = global_count
        global_count += 1

        const_list = tree.declarations
        for item in const_list:
            # assert isinstance(item,GoConstSpec)
            id_list = item.id_list
            dtype = item.dtype
            expr_list = item.expr
            if len(id_list) != len(expr_list):
                print(
                    "Error: different number of variables and values in const "
                    "declaration"
                )
                exit()

            else:
                evaluated_types = []
                for i, expr in enumerate(expr_list):
                    expr_dtype, expr_code = symbol_table(
                        expr,
                        table,
                        name,
                        block_type,
                        store_var="__const{}_{}".format(i, depth_num),
                        scope_label=scope_label,
                    )
                    ir_code += expr_code
                    evaluated_types.append(expr_dtype)

                for i, (const, eval_type) in enumerate(
                    zip(id_list, evaluated_types)
                ):
                    if dtype is None:
                        table.insert_const(const, eval_type)
                    else:
                        table.type_check(dtype, eval_type, "const declaration")
                        # Treating constant declarations as variable assignment
                        ir_code += "{} = __const{}_{}\n".format(
                            const, i, depth_num
                        )
                        if isinstance(eval_type, GoType):
                            dtype.value = eval_type.value
                        print('const "{}":"{}"'.format(const, dtype))
                        table.insert_const(const, dtype)
        DTYPE = None

    elif isinstance(tree, GoBlock):
        statement_list = tree.statements
        if not name:
            child_table = SymbTable(table)
            table.scopes.append(child_table)

        elif block_type == "function" and insert:
            child_table = SymbTable(table, "function")
            for param in table.functions[name]["params"]:
                if param.name:
                    child_table.insert_var(param.name, param.dtype)
                # TODO need to handle parameters with None name
            table.functions[name]["body"] = child_table

        elif block_type == "method" and insert:
            child_table = SymbTable(table, "method")
            key = (name[0], name[1].dtype.name)
            # rec.dtype.name
            # print("NAME {}".format(name[1].name))
            for param in table.methods[key]["params"]:
                if param.name:
                    child_table.insert_var(param.name, dtype)

            struct_obj = GoStruct([])
            struct_obj.name = name[1].dtype.name
            struct_obj.size = table.struct_size(name[1].dtype.name)
            print("STRUCT METHOD SIZE {}".format(struct_obj.size))
            child_table.insert_var(name[1].name, struct_obj)
            table.methods[key]["body"] = child_table

        for statement in statement_list:
            if (
                statement is None
                or statement == ""
                or (type(statement) is list and len(statement) == 0)
            ):
                continue
            ir_code += symbol_table(
                statement,
                child_table,
                name,
                block_type,
                scope_label=scope_label,
            )[1]
        DTYPE = None

    elif isinstance(tree, GoAssign):
        depth_num = global_count
        global_count += 1

        lhs = tree.lhs
        rhs = tree.rhs
        if len(lhs) != len(rhs):
            print(
                "Different number of variables and values in assign operation"
            )
            exit()
        lhs_3ac = []

        for var in lhs:
            loc_lhs = ""
            loc_rhs = ""
            curr = var
            ind_cnt = 0  # For counting indices
            while True:
                should_break = True
                error = False
                if isinstance(curr, GoPrimaryExpr):
                    if isinstance(curr.rhs, GoSelector):
                        # No checking here; it is done ahead
                        loc_rhs = "." + curr.rhs.child + loc_rhs
                    elif isinstance(curr.rhs, GoIndex):
                        dtype, index_code = symbol_table(
                            curr.rhs.index,
                            table,
                            name,
                            block_type,
                            store_var="__index{}_{}".format(
                                ind_cnt, depth_num
                            ),
                            scope_label=scope_label,
                        )
                        table.type_check(dtype, GoType("int", True))
                        ir_code += index_code
                        loc_rhs = (
                            "[__index{}_{}]".format(ind_cnt, depth_num)
                            + loc_rhs
                        )
                        ind_cnt += 1
                    else:
                        error = True
                    curr = curr.lhs
                    should_break = False
                elif isinstance(curr, GoExpression):
                    error = True
                elif isinstance(curr, GoUnaryExpr):
                    if curr.op == "*":
                        if type(curr.expr) is str:
                            if not isinstance(
                                table.get_type(curr.expr), GoPointType
                            ):
                                print(
                                    "Error: {} not pointer type".format(
                                        curr.expr
                                    )
                                )
                                exit()
                            else:
                                loc_lhs += "*"
                            curr = curr.expr
                            should_break = False

                    else:
                        error = True
                elif isinstance(curr, GoFromModule):
                    # No checking here; it is done ahead
                    loc_rhs = "." + curr.child + loc_rhs
                    curr = curr.parent
                    should_break = False
                elif not table.lookup(curr):
                    print('Error: "{}" not declared before use'.format(curr))
                    exit()
                elif type(curr) is str:
                    loc_lhs += curr

                if error:
                    print(
                        'Error: Expression "{}" cannot be assigned '
                        "value".format(var)
                    )
                    exit()
                if should_break:
                    break
            lhs_3ac.append(loc_lhs + loc_rhs)

        for i, (var, expr) in enumerate(zip(lhs, rhs)):
            print('assign: "{}" : "{}"'.format(var, expr))
            # can have only struct fields, variables, array on the LHS.
            dtype1 = None
            if isinstance(var, GoPrimaryExpr):
                # print(table.get_type(var.lhs))
                # dtype1 = table.get_type(var.lhs).dtype
                left = var
                while isinstance(left.lhs, GoPrimaryExpr):
                    left = left.lhs
                # XXX
                dtype1 = table.get_type(left.lhs).dtype
                # dtype1 = table.get_type(left.lhs)

            elif type(var) is str:
                dtype1 = table.get_type(var)

            elif isinstance(var, GoUnaryExpr) and var.op == "*":
                symbol_table(
                    var.expr, table, name, block_type, scope_label=scope_label
                )
                if type(var.expr) is str:
                    if not isinstance(table.get_type(var.expr), GoPointType):
                        error = True
                        print("{} not pointer type".format(var.expr))
                        exit()
                    var.dtype = table.get_type(var.expr).dtype
                    dtype1 = var.dtype

                elif isinstance(var.expr, GoUnaryExpr) and var.expr.op == "*":
                    if not isinstance(var.expr.dtype, GoPointType):
                        error = True
                        print("{} not pointer type".format(var.expr))
                        exit()
                    var.dtype = var.expr.dtype.dtype
                    dtype1 = var.dtype

            # NEW START
            elif isinstance(var, GoFromModule):
                parent = var.parent
                child = var.child
                # currently handles accessing a field of a struct
                if type(parent) is str:
                    assert type(child) is str
                    struct_name = table.get_type(parent).name
                    dtype1 = table.get_struct(struct_name, child).dtype

                # handles nesting of structs
                elif isinstance(parent, GoFromModule):
                    print("parent '{}', child '{}'".format(parent, child))
                    struct_name = (table.nested_module(parent)).dtype.name
                    print("struct name '{}'".format(struct_name))
                    dtype1 = table.get_struct(struct_name, child).dtype

            if dtype1 is None:
                print("Warning : Getting None dtype in Assignment")
                exit()
            # NEW END

            dtype2, rhs_code = symbol_table(
                expr,
                table,
                name,
                block_type,
                store_var=lhs_3ac[i],
                scope_label=scope_label,
            )
            ir_code += rhs_code

            table.type_check(dtype1, dtype2, "assignment")

            DTYPE = None

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
            # elif isinstance(expr, GoCompositeLit):  # Arrays
            #     symbol_table(expr, table)
            #     table.insert_var(var, expr.dtype)
            #     print("type = '{}' , {}'".format(var, expr.dtype))

            # elif isinstance(expr, GoUnaryExpr):
            #     symbol_table(expr, table)
            #     if expr.op == "&":
            #         table.insert_var(var,expr.dtype)
            #         print("type = '{}' , {}'".format(var, expr.dtype))
            dtype, rhs_code = symbol_table(
                expr,
                table,
                name,
                block_type,
                store_var=var,
                scope_label=scope_label,
            )
            ir_code += rhs_code
            table.insert_var(var, dtype)

        DTYPE = None

    elif isinstance(tree, GoExpression):
        depth_num = global_count
        global_count += 1

        lhs = tree.lhs
        op = tree.op
        rhs = tree.rhs
        print('exp: lhs "{}", rhs "{}"'.format(lhs, rhs))

        # XXX INCOMPLETE : need to handle cases for array types, struct types,
        # interfaces, function, pointer

        dtype1, lhs_code = symbol_table(
            lhs,
            table,
            name,
            block_type,
            store_var="__lhs_{}".format(depth_num),
            scope_label=scope_label,
        )
        dtype2, rhs_code = symbol_table(
            rhs,
            table,
            name,
            block_type,
            store_var="__rhs_{}".format(depth_num),
            scope_label=scope_label,
        )
        ir_code += lhs_code + rhs_code
        ir_code += "{} = __lhs_{} {} __rhs_{}\n".format(
            store_var, depth_num, op, depth_num
        )

        print('exp lhs: "{}", rhs: "{}"'.format(dtype1, dtype2))

        if dtype1.__class__ is not dtype2.__class__:
            print(
                "Error: Operands in expression of different type classes '{}' "
                "and '{}'".format(dtype1.__class__, dtype2.__class__)
            )
            exit()

        # XXX INCOMPLETE need to check for other type classes
        if isinstance(dtype1, GoType) and isinstance(dtype2, GoType):
            name1 = dtype1.name
            name2 = dtype2.name

            table.type_check(dtype1, dtype2, "expression")
            if dtype1.basic_lit is False:
                name = dtype1.name
            else:
                name = dtype2.name

            if name == "bool" and op not in ["&&", "||"]:
                error = True
                print("invalid operator for bool operands")
                exit()
            elif op in ["&&", "||"] and name != "bool":
                error = True
                print(
                    "invalid operand types '{}' and '{}' for bool operator".format(
                        name1, name2
                    )
                )
                exit()
            elif (
                op in [">>", "<<", "&", "&^", "^", "|", "%"]
                and name not in INT_TYPES
            ):
                error = True
                print("error")
                exit()
            elif name == "string" and op not in [
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
                print(
                    'basic_lit "{}", "{}", "{}"'.format(
                        dtype1, dtype2, dtype1.basic_lit & dtype2.basic_lit
                    )
                )
                if op in [">", "<", ">=", "<=", "==", "!="]:
                    tree.dtype = GoType(
                        "bool", dtype1.basic_lit & dtype2.basic_lit
                    )
                else:
                    tree.dtype = GoType(
                        name, dtype1.basic_lit & dtype2.basic_lit
                    )
                DTYPE = tree.dtype

    elif isinstance(tree, GoIf):
        # New symbol table needed as stmt is in the scope of both if and else
        newtable = SymbTable(table)
        ir_code += symbol_table(
            tree.stmt, newtable, name, block_type, scope_label=scope_label
        )[1]
        ir_code += symbol_table(
            tree.cond,
            newtable,
            name,
            block_type,
            store_var="__cond",
            scope_label=scope_label,
        )[1]

        # Choosing the labels
        if_label = "If{}".format(global_count)
        endif_label = "EndIf{}".format(global_count)
        global_count += 1

        ir_code += "if __cond goto {}\n".format(if_label)
        if (
            not (
                isinstance(tree.cond, GoExpression)
                or isinstance(tree.cond, GoBasicLit)
            )
            or not isinstance(tree.cond.dtype, GoType)
            or tree.cond.dtype.name != "bool"
        ):
            error = True
            print("Error: If condition is not evaluating to bool")
            exit()
        ir_code += symbol_table(
            tree.inelse, newtable, name, block_type, scope_label=scope_label
        )[1]
        ir_code += "goto {}\n{}: ".format(endif_label, if_label)
        ir_code += symbol_table(
            tree.inif, newtable, name, block_type, scope_label=scope_label
        )[1]
        ir_code += "{}: ".format(endif_label)
        table.scopes.append(newtable)
        DTYPE = None

    elif isinstance(tree, GoFor):
        print("Entered GoFor")
        cond_label = "ForCond{}".format(global_count)
        for_label = "For{}".format(global_count)
        postfor_label = "ForPost{}".format(global_count)
        endfor_label = "EndFor{}".format(global_count)
        depth_num = global_count + 1
        global_count += 2

        DTYPE = None

        if isinstance(tree.clause, GoForClause):
            print("Entered GoForClause")
            if (
                (tree.clause.init is not None)
                and not isinstance(tree.clause.init, GoShortDecl)
                and not isinstance(tree.clause.init, GoAssign)
            ):
                print("Error in for loop Initialization")
                exit()
            elif (
                (tree.clause.expr is not None)
                and not isinstance(tree.clause.expr, GoBasicLit)
                and not isinstance(tree.clause.expr, GoExpression)
            ):
                print("Error in for loop Condition")
                exit()
            elif (tree.clause.post is not None) and not isinstance(
                tree.clause.post, GoAssign
            ):
                print("Error in for loop post expression")
                exit()

            ir_code += symbol_table(
                tree.clause.init,
                table,
                name,
                block_type,
                scope_label=scope_label,
            )[1]
            ir_code += "{}: ".format(cond_label)
            ir_code += symbol_table(
                tree.clause.expr,
                table,
                name,
                block_type,
                store_var="__fcond_{}".format(depth_num),
                scope_label=scope_label,
            )[1]
            ir_code += "if __fcond_{} goto {}\ngoto {}\n{}: ".format(
                depth_num, for_label, endfor_label, for_label
            )
            post_code = symbol_table(
                tree.clause.post,
                table,
                name,
                block_type,
                scope_label=scope_label,
            )[1]

            if (
                tree.clause.expr is not None
            ) and tree.clause.expr.dtype.name is not "bool":
                print("loop Condition must be bool type")
                exit()

        elif isinstance(tree.clause, GoRange):
            raise NotImplementedError("Range not implemented")

        ir_code += symbol_table(
            tree.infor, table, name, block_type, scope_label="For"
        )[1]
        ir_code += "{}: ".format(postfor_label) + post_code
        ir_code += "goto {}\n{}: ".format(cond_label, endfor_label)

    elif isinstance(tree, GoSwitch):
        newtable = SymbTable(table)
        for case_stmt in tree.case_list:
            for child in case_stmt.expr_list:
                symbol_table(
                    child, newtable, name, block_type, scope_label=scope_label
                )
            newnewtable = SymbTable(newtable)
            for child in case_stmt.stmt_list:
                symbol_table(
                    child, newnewtable, name, block_type, scope_label="Switch"
                )
            newtable.scopes.append(newnewtable)
        table.scopes.append(newtable)

        # Converting Switch to If-Else for 3AC
        prev_stmts = []
        for case_stmt in tree.case_list:
            if case_stmt.kind == "default":
                prev_stmts = case_stmt.stmt_list
                break

        for case_stmt in tree.case_list[::-1]:
            if case_stmt.kind == "default":
                continue
            for expr in case_stmt.expr_list:
                prev_stmts = [
                    GoIf(
                        None,
                        GoExpression(tree.cond, expr, "=="),
                        GoBlock(case_stmt.stmt_list),
                        GoBlock(prev_stmts),
                    )
                ]

        if_conv = prev_stmts[0]
        if_conv.stmt = tree.stmt
        copy_table = deepcopy(table)
        return symbol_table(
            if_conv, copy_table, name, block_type, scope_label="Switch"
        )

    # TODO: 3AC necessary ??
    # DTYPE needs to be verified
    # ==========================================================================
    elif isinstance(tree, GoArray):
        if tree.length != "variable":
            symbol_table(
                tree.length, table, name, block_type, scope_label=scope_label
            )
        symbol_table(
            tree.dtype, table, name, block_type, scope_label=scope_label
        )
        if isinstance(tree.dtype, GoArray):
            tree.depth = tree.dtype.depth + 1
            tree.final_type = tree.dtype.final_type
        else:
            tree.final_type = tree.dtype

        length = tree.length

        if length == "variable":
            return ir_code
        elif type(length) is str:  # variable
            dtype = table.get_type(length)
        elif isinstance(length, GoExpression):
            dtype = length.dtype
        elif isinstance(length, GoBasicLit):
            dtype = length.dtype

        # XXX Need to handle the case for typedef/alias of dtype.name
        if isinstance(dtype, GoType) and dtype.name not in INT_TYPES:
            tree.size = dtype.value * tree.dtype.size
            print("ARRAY SIZE: {}".format(tree.size))
            print("Error: Array length must be an integer")
            exit()

        # XXX
        DTYPE = None

    elif isinstance(tree, GoIndex):
        index = tree.index
        dtype, ir_code = symbol_table(
            index,
            table,
            name,
            block_type,
            store_var=store_var,
            scope_label=scope_label,
        )
        if isinstance(dtype, GoType):
            name = dtype.name
            if name not in INT_TYPES:
                print("Error: index of array is not integer")
                exit()
        DTYPE = dtype

    elif isinstance(tree, GoPrimaryExpr):
        depth_num = global_count
        global_count += 1

        rhs = tree.rhs
        lhs = tree.lhs

        if isinstance(rhs, GoIndex):  # array indexing
            print("array = '{}'".format(lhs))
            # TODO need to handle multiple return from function
            if isinstance(lhs, GoPrimaryExpr):
                lhs.depth = tree.depth + 1
            else:
                if not table.lookup(lhs):
                    print("'{}' array not declared".format(lhs))
                    exit()
                elif not isinstance(table.get_type(lhs), GoArray):
                    print("'{}' not array".format(lhs))
                    exit()
                elif tree.depth != table.get_type(lhs).depth:
                    print(
                        "Incorect number of indexes in array '{}'".format(lhs)
                    )
                    exit()

                # print("dtype: '{}'".format(table.get_type(lhs)))
                tree.dtype = (table.get_type(lhs)).dtype
                # print("dtype: '{}'".format(table.get_type(lhs)))

                # XXX
                DTYPE = tree.dtype

            ir_code += symbol_table(
                lhs,
                table,
                name,
                block_type,
                store_var="__indlhs_{}".format(depth_num),
                scope_label=scope_label,
            )[1]
            ir_code += symbol_table(
                rhs,
                table,
                name,
                block_type,
                store_var="__indrhs_{}".format(depth_num),
                scope_label=scope_label,
            )[1]
            ir_code += "{} = __indlhs_{}[__indrhs_{}]\n".format(
                store_var, depth_num, depth_num, scope_label=scope_label
            )

        elif isinstance(rhs, GoArguments):  # fuction call
            argument_list = rhs.expr_list

            if type(lhs) is str:
                print("FUNCTION CALL '{}'".format(lhs))
                func_name = lhs
                assert isinstance(rhs, GoArguments)
                # type checking of arguments passed to function
                argument_list = rhs.expr_list
                params_list = table.get_func(func_name, "params")

                result = table.get_func(func_name, "result")
                # print(result)
                # assert result is None or isinstance(result, GoParam) ## Functions with no return value

                # Get function name/location in memory
                func_loc = func_name

            elif isinstance(lhs, GoFromModule):
                parent = lhs.parent
                child = lhs.child
                # double imports
                print("METHOD parent: '{}',child: '{}'".format(parent, child))
                if isinstance(parent, GoFromModule):
                    raise NotImplementedError("Multiple imports not done yet")
                # single imports
                # ID DOT ID
                elif type(parent) is str:
                    # check if the child is actually a method defined for parent (struct)
                    # check is the type of arguments passed to child are same as that defined in method declaration
                    method_name = child
                    struct_name = (table.get_type(parent)).name
                    print(
                        "method call'{}' on struct '{}' with arguments '{}'".format(
                            method_name, struct_name, rhs
                        )
                    )
                    # func_name = lhs
                    key = (method_name, struct_name)
                    assert isinstance(rhs, GoArguments)
                    # type checking of arguments passed to function
                    params_list = table.get_method(key, "params")

                    result = table.get_method(key, "result")

                    # tree.dtype = result_type
                # Get function name/location in memory
                func_loc = lhs.name

            if len(argument_list) is not len(params_list):
                print(
                    'Error: "{}" parameters passed to function "{}" instead '
                    'of "{}"'.format(
                        len(argument_list), func_name, len(params_list)
                    )
                )
                exit()
            for i, (argument, param) in enumerate(
                zip(argument_list, params_list)
            ):
                assert isinstance(param, GoParam)
                # symbol_table(param,table)
                ir_code += symbol_table(
                    argument,
                    table,
                    name,
                    block_type,
                    store_var="__arg{}_{}".format(i, depth_num),
                    scope_label=scope_label,
                )[1]
                actual_dtype = param.dtype
                given_dtype, eval_code = symbol_table(
                    argument, table, name, block_type, scope_label=scope_label
                )
                table.type_check(
                    actual_dtype,
                    given_dtype,
                    "function call",
                    func_name,
                    param.name,
                )
            if len(result) > 0:
                result_type = []
                for item in result:
                    result_type.append(item.dtype)
                if len(result_type) == 1:
                    result_type = result_type[0]
                tree.dtype = result_type
            else:
                result_type = []
                tree.dtype = []

            DTYPE = result_type

            ir_code += "{} = {}(".format(store_var, func_loc)
            ir_code += ",".join(
                [
                    "__arg{}_{}".format(i, depth_num)
                    for i in range(len(argument_list))
                ]
            )
            ir_code += ")\n"

    # XXX To be done later : check number of elements in array same as that
    # specified

    elif isinstance(tree, GoKeyedElement):
        # symbol_table(tree.element, table)
        print("-" * 50)
        print(store_var, tree.use)
        print("-" * 50)
        if tree.use == "array":
            if isinstance(tree.element, GoBasicLit) or isinstance(
                tree.element, GoExpression
            ):
                if isinstance(tree.element, GoExpression):
                    ir_code += symbol_table(
                        tree.element,
                        table,
                        name,
                        block_type,
                        store_var=store_var,
                        scope_label=scope_label,
                    )[1]
                else:
                    ir_code += "{} = {}\n".format(store_var, tree.element.item)
                element_type = tree.element.dtype
                tree.size += 1
                # print(element_type)
            elif type(tree.element) is str:
                ir_code = "{} = {}".format(store_var, element)
                element_type = table.get_type(tree.element)
                tree.size += 1
            else:
                # LiteralValue is a list
                depth_num = global_count
                global_count += 1

                depth = 0
                child_count = 0
                cur_size = 0
                for child in tree.element:
                    if isinstance(child, GoKeyedElement):
                        child.use = "array"
                        ir_code += symbol_table(
                            child,
                            table,
                            name,
                            block_type,
                            store_var="__child{}_{}".format(
                                child_count, depth_num
                            ),
                            scope_label=scope_label,
                        )[1]
                        child_count += 1
                        if depth == 0:
                            depth = child.depth
                        elif depth != child.depth:
                            print("Error: Wrong array declaration")
                            exit(0)
                        print("child dtype {}".format(child.dtype))
                        element_type = child.dtype
                        tree.size += child.size

                        if cur_size == 0:
                            cur_size = child.size
                        elif cur_size != child.size:
                            print(
                                "Error: Incorrect number of elements in array"
                            )
                            exit()

                    if tree.dtype is None:
                        tree.dtype = element_type
                    else:
                        table.type_check(
                            tree.dtype, element_type, "array conflicts"
                        )

                tree.depth = depth + 1

                ir_code += (
                    "{} = {{".format(store_var)
                    + ",".join(
                        [
                            "__child{}_{}".format(i, depth_num)
                            for i in range(child_count)
                        ]
                    )
                    + "}\n"
                )
            tree.dtype = element_type
            print("tree.dtype '{}'".format(tree.dtype))

        # TODO 3AC
        elif tree.use == "struct":
            element = tree.element
            print("struct element '{}'".format(element))
            if isinstance(element, GoBasicLit):
                element_type = element.dtype
            elif isinstance(element, GoExpression):
                element_type, _ = symbol_table(
                    element, table, name, block_type, scope_label=scope_label
                )
                element_type = element_type
            elif type(element) is str:
                element_type = table.get_type(element)

            elif type(element) is list:
                element_type = []
                for item in element:
                    item.use = "struct"
                    item_type, _ = symbol_table(
                        item, table, name, block_type, scope_label=scope_label
                    )
                    element_type.append(item_type)
                print("LIST {}".format(list(element_type)))
            tree.dtype = element_type

        # XXX
        DTYPE = tree.dtype

    # XXX UN-IMPLEMENTED
    elif isinstance(tree, GoCompositeLit):
        print(
            "tree.dtype {}, tree.value {}".format(tree.dtype.name, tree.value)
        )
        symbol_table(
            tree.dtype, table, name, block_type, scope_label=scope_label
        )
        # symbol_table(tree.value, table)

        depth_num = global_count
        global_count += 1

        keys = []
        elem_num = 0
        # XXX How does this handle array of structs
        if isinstance(tree.dtype, GoArray):
            symbol_table(
                tree.dtype, table, name, block_type, scope_label=scope_label
            )
            # symbol_table(tree.value, table)
            dtype = tree.dtype.final_type
            depth = 0
            cur_size = 0

            # print("array_dtype = '{}'".format(dtype.name))
            for child in tree.value:
                if isinstance(child, GoKeyedElement):
                    child.use = "array"
                    ir_code += symbol_table(
                        child,
                        table,
                        name,
                        block_type,
                        store_var="__elem{}_{}".format(elem_num, depth_num),
                        scope_label=scope_label,
                    )[1]
                    elem_num += 1
                    keys.append(child.key)

                    if depth == 0:
                        depth = child.depth
                    elif depth != child.depth:
                        print("Error: Wrong array declaration")
                        exit()
                    element_type = child.dtype
                    tree.dtype.size += child.size
                    print("final array type {}".format(element_type))

                    if cur_size == 0:
                        cur_size = child.size
                    elif cur_size != child.size:
                        print("Error: Incorrect number of elements in array")
                        exit()

                table.type_check(element_type, dtype, "array initialization")
            # XXX
            DTYPE = tree.dtype
            if depth != tree.dtype.depth:
                print("Error: Wrong array declaration")
                exit()

            tree_value = tree.value
            tree_type = tree.dtype
            print("START")
            while isinstance(tree_type, GoArray):
                # print("type = {}, value = {}".format(tree_type.length.item,len(tree_value)))
                if (
                    tree_type.length != "variable"
                    and tree_type.length.item != len(tree_value)
                ):
                    print("Error: Array declaration of incorrect size")
                    exit()
                tree_type = tree_type.dtype
                tree_value = tree_value[0].element

        elif isinstance(tree.dtype, GoType):  # handles structs
            struct_name = tree.dtype.name
            print("Struct name {}".format(struct_name))
            field_list = tree.value
            type_list = []
            for i, field in enumerate(field_list):
                field.use = "struct"
                # field.name = struct_name
                assert isinstance(field, GoKeyedElement)
                field_type, elem_code = symbol_table(
                    field,
                    table,
                    name,
                    block_type,
                    store_var="__elem{}_{}".format(i, depth_num),
                    scope_label=scope_label,
                )
                keys.append(field.key)
                ir_code += elem_code
                type_list.append(field_type)
            print("FINAL LIST '{}'".format(type_list))
            struct_obj = GoStruct([])
            struct_obj.size = table.check_struct(struct_name, type_list)
            struct_obj.name = struct_name
            # struct_obj.size = table.struct_size(struct_name)
            # table.struct_size(struct_name)
            # table.variables(insert_var(struct_name, struct_obj, "struct"))

            DTYPE = struct_obj

        ir_code += "{} = {}{{".format(store_var, tree.dtype.name)
        ir_code += ",".join(
            [
                "{}:__elem{}_{}".format(key, i, depth_num)
                if key is not None
                else "__elem{}_{}".format(i, depth_num)
                for i, key in enumerate(keys)
            ]
        )
        ir_code += "}\n"

    elif isinstance(tree, GoUnaryExpr):
        ir_code += symbol_table(
            tree.expr,
            table,
            name,
            block_type,
            store_var="__opd",
            scope_label=scope_label,
        )[1]
        ir_code += "{} = {} __opd\n".format(store_var, tree.op)

        if tree.op == "&" or tree.op == "*":
            if type(tree.expr) is str:
                # print("XXX1")
                if tree.op == "&":
                    tree.dtype = GoPointType(table.get_type(tree.expr))
                elif tree.op == "*":
                    if not isinstance(table.get_type(tree.expr), GoPointType):
                        print("Error: {} not pointer type".format(tree.expr))
                        exit()
                    else:
                        tree.dtype = table.get_type(tree.expr).dtype

            elif isinstance(tree.expr, GoPrimaryExpr) or isinstance(
                tree.expr, GoFromModule
            ):
                # print("XXX2")
                eval_type, _ = symbol_table(
                    tree.expr, table, name, block_type, scope_label=scope_label
                )
                if tree.op == "&":
                    tree.dtype = GoPointType(eval_type)
                elif tree.op == "*":
                    if not isinstance(eval_type, GoPointType):
                        print("Error: {} not pointer type".format(eval_type))
                        exit()
                    else:
                        tree.dtype = eval_type.dtype

            elif isinstance(tree.expr, GoUnaryExpr):
                # print("XXX3")
                eval_type, _ = symbol_table(
                    tree.expr, table, name, block_type, scope_label=scope_label
                )

                if tree.op == "&":
                    if tree.expr.op == "&":
                        print("Error: Cannot take address of address")
                        exit()
                    elif tree.expr.op == "*":
                        tree.dtype = GoPointType(eval_type)
                        # tree.dtype = GoPointType(tree.expr.dtype)

                elif tree.op == "*":
                    if not isinstance(eval_type, GoPointType):
                        print("{} not pointer type".format(eval_type))
                        exit()
                    else:
                        tree.dtype = eval_type.dtype

            # elif isinstance(tree.expr,GoFromModule):
            #     eval_type,_  = symbol_table(tree.expr,table)

        # TODO need to add better type checking
        else:
            tree.dtype, _ = symbol_table(
                tree.expr, table, name, block_type, scope_label=scope_label
            )

        DTYPE = tree.dtype

    elif isinstance(tree, GoLabelCtrl):
        if scope_label == "":
            print("Error: {} not valid in this scope".format(tree.keyword))
            exit()
        elif tree.keyword == "continue" and "|" not in scope_label:
            print('Error: "continue" not valid in a "switch" scope')
            exit()

        if tree.keyword == "continue":
            ir_code = "goto {}\n".format(scope_label.split("|")[-1])
        else:
            ir_code = "goto {}\n".format(scope_label.split("|")[0])

    elif isinstance(tree, GoReturn):
        depth_num = global_count
        global_count += 1

        if block_type == "function":
            results = table.get_func(name, "result")
        elif block_type == "method":
            results = table.get_method(name, "result")
        else:
            print("Error: Return statement not inside any function or method")
            exit()

        if len(results) != len(tree.expr_list):
            print(
                'Error: No. of values returned is "{}"; should be "{}"'.format(
                    len(tree.expr_list), len(results)
                )
            )
            exit()
        for i, (res, expr) in enumerate(zip(results, tree.expr_list)):
            expr_dtype, expr_code = symbol_table(
                expr,
                table,
                name=name,
                block_type=block_type,
                store_var="__retval{}_{}".format(i, depth_num),
                scope_label=scope_label,
            )
            ir_code += expr_code
            table.type_check(res.dtype, expr_dtype, use="return")

        ir_code += "return "
        ir_code += ",".join(
            ["__retval{}_{}".format(i, depth_num) for i in range(len(results))]
        )
        ir_code += "\n"

    # ==================================================================

    return DTYPE, ir_code


# Used for numbering of nodes in the output ".dot" file
node_count = 0


def escape_string(string):
    """Escape a string for output into ".dot" file."""
    string = string.encode("unicode-escape").decode("utf8")
    string = string.replace('"', '\\"')
    return string


def get_dot(obj):
    """Get a list of node and edge declarations."""
    global node_count
    if type(obj) in [int, float, complex, bool]:
        obj = str(obj)
    if type(obj) is tuple:  # Struct variables
        obj = {"var": obj[0], "dtype": obj[1]}
    if type(obj) is str:
        output = [
            'N_{} [label="'.format(node_count) + escape_string(obj) + '"]'
        ]
    elif type(obj) is list:
        output = ['N_{} [label="list"]'.format(node_count)]
    else:
        output = [
            'N_{} [label="{}"]'.format(node_count, obj.__class__.__name__)
        ]
    own_count = node_count
    node_count += 1

    if type(obj) is list:
        for child in obj:
            # Avoid None child node, empty strings, and empty lists
            if (
                child is None
                or child == ""
                or (type(child) is list and len(child) == 0)
            ):
                continue
            output.append("N_{} -> N_{}".format(own_count, node_count))
            output += get_dot(child)
    elif type(obj) is not str and obj is not None:
        if type(obj) is dict:
            obj_dict = obj
        else:
            obj_dict = obj.__dict__
        for attr in obj_dict:
            if type(obj) is dict:
                child = obj[attr]
            else:
                child = getattr(obj, attr)
            # Avoid None child node, emtpy strings, empty lists, and "kind"
            # attributes
            if (
                child is None
                or child == ""
                or (type(child) is list and len(child) == 0)
                or attr == "kind"
            ):
                continue
            output.append(
                'N_{} -> N_{} [label="{}"]'.format(own_count, node_count, attr)
            )
            output += get_dot(child)

    return output


def resovle_pointer(dtype):
    s = ""
    while isinstance(dtype, GoPointType):
        dtype = dtype.dtype
        s = s + "*"
    if isinstance(dtype, GoType):
        s = s + dtype.name
    return s


# TODO Interfaces and return and parameter types for functions/methods
def csv_writer(table, name):
    # with open(name+'.txt') as file:
    # reader = csv.reader(file,delimiter = " ")
    file = open("{}.csv".format(name), "w")
    writer = csv.writer(
        file,
        delimiter=" ",
        quoting=csv.QUOTE_NONE,
        quotechar="",
        escapechar='"',
    )

    writer.writerow(
        ["VARIABLES", "=============================================="]
    )
    writer.writerow(["name", "type", "size", "offset"])
    writer.writerow([])
    var_rows = []
    for var in table.variables:
        dtype = table.variables[var]
        if isinstance(dtype, GoType):
            row = [var, dtype.name, dtype.size, dtype.offset]
        elif isinstance(dtype, GoStruct):
            row = [
                var,
                "struct {}".format(dtype.name),
                dtype.size,
                dtype.offset,
            ]
        elif isinstance(dtype, GoArray):
            row = [
                var,
                "array {}".format(dtype.dtype.name),
                dtype.size,
                dtype.offset,
            ]
        elif isinstance(dtype, GoPointType):
            row = [
                var,
                "{}".format(resovle_pointer(dtype)),
                dtype.size,
                dtype.offset,
            ]
        var_rows.append(row)

    var_rows = sorted(var_rows, key=lambda x: x[3])
    for row in var_rows:
        writer.writerow(row)

    writer.writerow([])
    writer.writerow(
        ["CONSTANTS", "=============================================="]
    )
    writer.writerow(["name", "type", "size", "offset"])
    writer.writerow([])
    var_rows = []
    for var in table.constants:
        dtype = table.constants[var]
        if isinstance(dtype, GoType):
            row = [var, dtype.name, dtype.size, dtype.offset]
        elif isinstance(dtype, GoStruct):
            row = [
                var,
                "struct {}".format(dtype.name),
                dtype.size,
                dtype.offset,
            ]
        elif isinstance(dtype, GoArray):
            row = [
                var,
                "array {}".format(dtype.dtype.name),
                dtype.size,
                dtype.offset,
            ]
        elif isinstance(dtype, GoPointType):
            row = [
                var,
                "{}".format(resovle_pointer(dtype)),
                dtype.size,
                dtype.offset,
            ]
        # writer.writerow(row)
        var_rows.append(row)

    var_rows = sorted(var_rows, key=lambda x: x[3])
    for row in var_rows:
        writer.writerow(row)

    if name == "global":
        writer.writerow([])
        writer.writerow(
            ["ALIASES", "=============================================="]
        )
        writer.writerow(["alias", "actual"])
        writer.writerow([])

        for alias in table.types:
            row = [alias, table.types[alias].name]
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(
            ["FUNCTIONS", "=============================================="]
        )
        writer.writerow(["func_name", "symbol_table"])
        writer.writerow([])

        for func in table.functions:
            row = [func, "{}.csv".format(func)]
            csv_writer(table.functions[func]["body"], func)
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(
            ["SCOPES", "=============================================="]
        )
        writer.writerow(["scope no.", "symbol_table"])
        writer.writerow([])
        count = 0
        writer.writerow([])
        for scope in table.scopes:
            row = ["scope_{}".format(count), "scope_{}".format(count).csv]
            csv_writer(scope, "scope_{}".format(count))
            writer.writerow(row)
            count += 1

        writer.writerow([])
        writer.writerow(
            ["METHODS", "=============================================="]
        )
        writer.writerow(["method_name", "reciever", "symbol_table"])
        writer.writerow([])
        for method in table.methods:
            name, rec = method
            row = [name, rec, "{}.csv".format(name + "_" + rec)]
            csv_writer(table.methods[method]["body"], name + "_" + rec)
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(
            ["STRUCTURES", "=============================================="]
        )

        for name in table.structures:
            writer.writerow([])
            struct = table.structures[name]
            writer.writerow([name, "{"])
            # writer.writerow([])
            vars = struct.vars
            tags = struct.tags
            for item1, item2 in zip(vars, tags):
                assert item1[0] == item2[0]
                row = ["  ", item1[0], item1[1].dtype.name, item2[1]]
                writer.writerow(row)
            # writer.writerow([])
            writer.writerow(["}"])

    file.close()


def get_csv(table):
    csv_writer(table, "global")
    subprocess.run(["rm", "-rf", "symbol_table"])
    os.mkdir("symbol_table")

    for file in os.listdir("."):
        if len(file.split(".")) == 2 and file.split(".")[1] == "csv":
            with open("./symbol_table/" + file, "w+") as outfile:
                subprocess.call(
                    ["awk", '{gsub(/"/,"")};1', file], stdout=outfile
                )
    for file in os.listdir("."):
        if len(file.split(".")) == 2 and file.split(".")[1] == "csv":
            subprocess.run(["rm", file])


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
    ir_code = symbol_table(tree, table)[1]
    get_csv(table)

    print("=" * 50)
    print(ir_code)
    print("=" * 50)
    with open("dot.dot", "w") as outf:
        core_info = ";\n  ".join(get_dot(tree))
        outf.write("digraph syntax_tree {\n  " + core_info + ";\n}")
