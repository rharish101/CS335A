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
import logging
import re
from math import ceil


class GoException(Exception):
    """Simply for catching errors in the source code."""

    pass


def go_traceback(tree):
    """Print traceback for the custom error message."""
    print("Traceback (for Go source code):")
    print(" " * 2 + 'File "{}", line {}'.format(lexer.filename, tree.lineno))
    print(" " * 4 + lexer.lines[tree.lineno - 1])


class SymbTable:
    """The class for all symbol tables."""

    def __init__(self, parent=None, use=None):
        """Initialize data dictionaries containing information.

        The kinds of information stored are:
            * Variables (dict of `GoVar`): Their types
            * Intermediates (dict of `GoVar`): Intermediate 3AC variables
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
            * Aliases (dict of `GoBaseType`): A dictionary of aliases (NOTE:
                Aliases have a reference to another type, while typedefs have a
                copy)
            * Basic Types (dict of dict): A dictionary of basic types
                (including typedefs) with their sizes and kind
                (integer/float/complex/other)
            * Used (set of str): Set of used variable/alias/const names
            * Constants (dict of GoConstants) : Their types
            * Imports (dict of `GoImportSpec`): The imports and their aliases
            * Parent (`SymbTable`): The reference to the parent scope (if it
                exists)
        """
        self.variables = {}
        self.intermediates = {}
        self.structures = {}
        self.interfaces = {}
        self.functions = {}
        self.methods = {}
        self.scopes = []
        self.aliases = {}
        self.used = set()
        self.constants = {}
        self.imports = {}
        self.parent = parent
        self.use = None

        if parent is not None:
            self.inline_count = parent.inline_count
        else:
            self.inline_count = 0

        self.basic_types = {}

        for type_str in [
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
        ]:
            self.basic_types[type_str] = {"kind": "int"}
        for type_str in ["float", "float32", "float64"]:
            self.basic_types[type_str] = {"kind": "float"}
        for type_str in ["complex", "complex64", "complex128"]:
            self.basic_types[type_str] = {"kind": "complex"}
        for type_str in ["byte", "string", "uintptr", "bool"]:
            self.basic_types[type_str] = {"kind": "other"}

        for name in self.basic_types:
            if name in ["uint8", "int8", "byte", "bool"]:
                self.basic_types[name]["size"] = 1
            elif name in ["uint16", "int16"]:
                self.basic_types[name]["size"] = 2
            elif name in [
                "uint32",
                "int32",
                "float32",
                "rune",
                "int",
                "uint",
                "uintptr",
            ]:
                self.basic_types[name]["size"] = 4
            elif name in [
                "uint64",
                "int64",
                "complex",
                "complex64",
                "float64",
                "float",
            ]:
                self.basic_types[name]["size"] = 8
            elif name == "complex128":
                self.basic_types[name]["size"] = 16
            elif name == "string":  # Only for string
                self.basic_types[name]["size"] = 4

        if use is None:
            if self.parent:
                self.offset = self.parent.offset
                self.activation_record = parent.activation_record
                self.use = parent.use
                self.activation_offset = parent.activation_offset
            else:
                self.offset = 0
                self.activation_record = []
                self.use = None
                # Using list as it is mutable.
                # This is because any increments by the child should reflect
                # in the parent
                self.activation_offset = [0]
        elif use == "function" or use == "method":
            self.offset = 0
            self.activation_record = []
            self.use = use
            # Using list as it is mutable.
            # This is because any increments by the child should reflect
            # in the parent
            self.activation_offset = [0]

        logging.info("offset assigned: {}".format(self.offset))

    def get_import(self, name):
        if name in self.imports:
            return self.imports[name]
        elif self.parent is not None:
            return self.parent.get_import(name)
        else:
            raise GoException(
                "Error : No module named {} imported".format(name)
            )

    def lookup_function(self, name):
        if name in self.functions:
            return True
        elif self.parent is not None:
            return self.parent.lookup_function(name)
        else:
            return False

    def lookup(self, name):
        if name in self.variables:
            return True
        elif self.parent is not None:
            return self.parent.lookup(name)
        else:
            return False

    def check_basic_type(self, name):
        if name in self.basic_types:
            return True
        elif self.parent is not None:
            return self.parent.check_basic_type(name)
        else:
            return False

    def get_basic_type(self, name):
        if name in self.basic_types:
            return self.basic_types[name]
        elif self.parent is not None:
            return self.parent.get_basic_type(name)
        else:
            raise GoException('Error: "{}" is unregistered dtype'.format(name))

    def get_actual(self, alias):
        if alias in self.aliases:
            actual = self.aliases[alias]
            while actual.name in self.aliases:
                actual = self.aliases[actual.name]
            if self.parent:
                parent_actual = self.parent.get_actual(actual.name)
            else:
                parent_actual = None
            return actual if parent_actual is None else parent_actual
        elif self.parent:
            return self.parent.get_actual(alias)
        else:
            return None

    # TODO: Need to handle dynamic entities like linked lists, strings etc
    def get_size(self, dtype, check=False):
        if isinstance(dtype, GoBasicLit):
            return self.get_size(dtype.dtype)
        elif isinstance(dtype, GoStruct):
            try:
                self.get_struct(dtype.name)
            except GoException:  # Inline struct
                return self.infer_struct_size(dtype)
            else:  # Pre-defined struct
                return self.struct_size(dtype.name)
        elif isinstance(dtype, GoPointType):
            return 4
        elif isinstance(dtype, GoArray):
            return dtype.length.item * self.get_size(dtype.dtype)
        elif isinstance(dtype, GoKeyedElement):
            element = dtype.element
            try:
                return self.get_type(element).size
            except GoException:
                return self.get_size(element)
        elif isinstance(dtype, GoCompositeLit):
            values = dtype.value
            size = 0
            for value in values:
                size += self.get_size(value)
            return size

        elif isinstance(dtype, GoType):
            name = dtype.name
            logging.info("SIZE: getting size of {}".format(name))
            value = dtype.value

            if self.check_basic_type(name):
                basic_type = self.get_basic_type(name)
                if basic_type["size"] is not None:
                    size = basic_type["size"]
                # else:  # string or its typedef
                #     if value is None:
                #         size = 0
                #     else:
                #         # -2 done to strip the quotes
                #         size = len(value) - 2
            else:
                actual_type = self.get_actual(name)
                if actual_type is None:
                    size = self.struct_size(name)
                    return size
                actual_type.value = value
                size = self.get_size(actual_type)
            return size
        else:
            print("Warning: Returning zero size")
            return 0

    def infer_struct_size(self, dtype):
        size = 0
        variables = dtype.vars
        for item in variables:
            size += self.get_size(item[1].dtype)
        return size

    def get_type(self, name, use="variable/array/struct", side=""):
        if side == "left":
            curr = self
            while curr.parent:
                if name in self.constants:
                    raise GoException(
                        "Error: Attempt to assign to constant {} ".format(name)
                    )
                curr = curr.parent

            if name in curr.constants:
                raise GoException(
                    "Error: Attempt to assign to constant {} ".format(name)
                )

        if name in self.variables:
            return self.variables[name]
        elif name in self.intermediates:
            return self.intermediates[name]
        elif self.parent:
            return self.parent.get_type(name)
        else:
            raise GoException(
                "Error: Attempt to use '{}': undeclared '{}' name ".format(
                    name, use
                )
            )

    def get_func(self, name, info):
        if name in self.functions:
            return self.functions[name][info], False
        elif self.parent:
            return self.parent.get_func(name, info)
        else:
            # Check for possible type-casting
            actual = self.get_actual(name)
            if actual is not None:
                name = actual.name
            if not self.check_basic_type(name):
                # Not type-casting
                raise GoException(
                    "Error: Attempt to use '{}': undeclared function".format(
                        name
                    )
                )
            else:
                # Type-casting
                result_type = GoType(name)
                result_type.size = self.get_size(result_type)
                func = {
                    "params": [GoParam(dtype=result_type)],
                    "result": [GoParam(dtype=result_type)],
                }
                return func[info], True

    def get_method(self, name, info):
        if name in self.methods:
            return self.methods[name][info]
        elif self.parent:
            return self.parent.get_method(name, info)
        else:
            raise GoException(
                "Error: Attempt to use undeclared method '{}' on struct '{}'".format(
                    name[0], name[1]
                )
            )

    def insert_var(self, name, dtype, use="variable"):
        if type(name) is not str:
            raise GoException(
                "Error: Variable name {} is not string".format(name)
            )
        dtype = deepcopy(dtype)
        if name not in self.used:
            # Get the underlying dtype
            if hasattr(dtype, "name"):
                actual = self.get_actual(dtype.name)
                if actual is not None:
                    dtype = actual
                # Check if dtype is of a struct or not
                if isinstance(dtype, GoType):
                    try:
                        struct_obj = self.get_struct_obj(dtype.name)
                        struct_obj.name = dtype.name
                        dtype = struct_obj
                    except GoException:
                        pass

            if isinstance(dtype, GoType):
                dtype.size = self.get_size(dtype)
                logging.info(
                    "previous offset {}, size {}".format(
                        self.offset, dtype.size
                    )
                )
                dtype.offset = self.offset + ceil(dtype.size / 4) * 4
                self.offset = dtype.offset

            # TODO: need to handle array os structures seperately
            elif isinstance(dtype, GoArray):
                logging.info("ARRAY DTYPE {}".format(dtype.dtype))
                dtype.size = self.get_size(dtype)

                dtype.offset = self.offset + ceil(dtype.size / 4) * 4
                self.offset = dtype.offset
                logging.info("ARRAY SIZE: {}".format(dtype.size))

            elif isinstance(dtype, GoStruct):
                dtype.size = self.get_size(dtype)
                dtype.offset = self.offset + ceil(dtype.size / 4) * 4
                self.offset = dtype.offset
                logging.info("STRUCT SIZE {}".format(dtype.size))

            elif isinstance(dtype, GoPointType):
                dtype.size = 4
                dtype.offset = self.offset + 4
                self.offset = dtype.offset

            if name not in ["dynamic_link", "return_address", "static_link"]:
                if use == "intermediate":
                    self.intermediates[name] = dtype
                else:
                    self.variables[name] = dtype

            if self.use == "function" or self.use == "method":
                self.activation_record.append((name, dtype))
                dtype_size = self.get_size(dtype)
                dtype.activation_offset = (
                    self.activation_offset[0] - ceil(dtype_size / 4) * 4
                )
                self.activation_offset[0] = dtype.activation_offset

            self.used.add(name)
        elif use == "intermediate":
            print('Warning: Already declared "{}" name "{}"'.format(use, name))
        else:
            raise GoException(
                'Error: Already declared "{}" name "{}"'.format(use, name)
            )

    def insert_alias(self, alias, actual, kind):
        if alias not in self.used:
            if kind == "alias":
                self.aliases[alias] = actual
            elif kind == "typedef":
                # Check structs
                try:
                    obj = self.get_struct_obj(actual.name)
                except GoException:
                    pass
                else:
                    self.insert_struct(alias, obj, embed=False)
                    return

                # Check interfaces
                try:
                    obj = self.get_interface(actual.name)
                except GoException:
                    pass
                else:
                    self.insert_interface(alias, obj)
                    return

                obj = self.get_actual(actual.name)
                if obj is not None:
                    if isinstance(obj, GoStruct):
                        self.insert_struct(alias, obj, embed=False)
                        return
                    elif isinstance(obj, GoInterfaceType):
                        self.insert_interface(alias, obj)
                        return
                    else:
                        actual = obj

                if self.check_basic_type(actual.name):
                    self.basic_types[alias] = self.get_basic_type(actual.name)
                else:
                    raise GoException(
                        'Typedef "{}" to undefined "{}"'.format(
                            alias, actual.name
                        )
                    )
            else:
                raise ValueError(
                    'Alias/typedef kind "{}" is invalid'.format(kind)
                )
            self.used.add(alias)
        else:
            raise GoException(
                "Error: Already used alias/typedef name '{}'".format(alias)
            )

    def helper_get_struct(self, struct_name, field):
        if struct_name in self.structures:
            if field is None:
                types = []
                for item in self.structures[struct_name].vars:
                    logging.info("item {}".format(item))
                    type_item = deepcopy(item[1])
                    dtype = type_item.dtype
                    # print(dtype.name)
                    if isinstance(dtype, GoType):
                        name = dtype.name
                        try:
                            type_item.dtype = self.get_struct_obj(name)
                        except GoException:
                            pass
                    types.append(type_item)
                return types

            for item in self.structures[struct_name].vars:
                # print(item,item[1].dtype)
                if field == item[0]:
                    type_item = deepcopy(item[1])
                    dtype = type_item.dtype
                    if isinstance(dtype, GoType):
                        name = dtype.name
                        try:
                            type_item.dtype = self.get_struct_obj(name)
                            # print(item[0],"found",self.get_struct_obj(name))
                        except GoException:
                            pass
                    # print("here",type_item,type_item.dtype)
                    return type_item
            else:
                raise GoException(
                    "Error: Attempt to access unexisting field '{}' on struct '{}'".format(
                        field, struct_name
                    )
                )
        elif self.parent:
            return self.parent.get_struct(struct_name, field)
        else:
            raise GoException(
                "Error: Attempt to access undeclared struct '{}'".format(
                    struct_name
                )
            )

    def get_struct(self, struct_name, field=None):
        actual_name = self.get_actual(struct_name)
        if actual_name is not None:
            if isinstance(actual_name, GoType):
                struct_name = actual_name.name
        return self.helper_get_struct(struct_name, field)

    def get_struct_obj(self, struct_name):
        actual_name = self.get_actual(struct_name)
        if actual_name is not None:
            if isinstance(actual_name, GoType):
                struct_name = actual_name.name
        if struct_name in self.structures:
            return self.structures[struct_name]
        elif self.parent:
            return self.parent.get_struct_obj(struct_name)
        else:
            raise GoException(
                "Error: Attempt to access undeclared struct '{}'".format(
                    struct_name
                )
            )

    def get_interface(self, interface_name):
        actual_name = self.get_actual(interface_name)
        if actual_name is not None:
            if isinstance(actual_name, GoType):
                interface_name = actual_name.name
        if interface_name in self.interfaces:
            return self.interfaces[interface_name]
        elif self.parent:
            return self.parent.get_interface(interface_name)
        else:
            raise GoException(
                "Error: Attempt to access undeclared interface '{}'".format(
                    interface_name
                )
            )

    def check_struct(self, struct_name, type_list):
        actual_types = self.get_struct(struct_name)
        if len(actual_types) is not len(type_list):
            raise GoException(
                "Error: Invalid number of values given for structure initialization"
            )
        size = 0
        for actual, given in zip(actual_types, type_list):
            logging.info(
                "actual type'{}', give types '{}'".format(
                    actual.dtype.name, given
                )
            )
            if isinstance(given, GoStruct):
                size += self.struct_size(given.name)
            else:
                self.type_check(
                    actual.dtype, given, "structure initialization"
                )
                size += self.get_size(given)
        return size

    def check_inline_struct(self, struct_obj, type_dict):
        variables = {}
        for item in struct_obj.vars:
            if item[0] not in variables:
                variables[item[0]] = item[1].dtype
            else:
                raise GoException(
                    "Error : field name {} already exists in inline struct".format(
                        item[0]
                    )
                )
                exit()
            if item[0] not in type_dict:
                raise GoException(
                    "Error: No value given for initialization of field '{}' in inline struct".format(
                        item[0]
                    )
                )
                exit()
        # print(variables)
        # print(type_dict)
        for key in type_dict:
            element = type_dict[key]
            if key in variables:
                if isinstance(element, GoType):
                    self.type_check(
                        variables[key],
                        element,
                        use="inline struct initialization",
                    )
                # already covered in the recursive call of symbol_table
                # elif isinstance(element,GoStruct):
                # pass
            else:
                raise GoException(
                    "Error : attempt to initialize un-existing field {} on inline struct"
                ).format(key)
                exit()

    def struct_size(self, struct_name):
        actual_types = self.get_struct(struct_name)
        size = 0
        for actual in actual_types:
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
            # self.
            dtype.size = self.get_size(dtype)
            dtype.offset = self.offset + ceil(dtype.size / 4) * 4
            self.offset = dtype.offset
            self.variables[const] = dtype
        else:
            raise GoException(
                "Error: Already used constant name '{}'".format(name)
            )

    def insert_struct(self, name, struct, embed=True):
        # print(struct.embeds)
        if name not in self.used:
            embeds = struct.embeds
            # handles struct embeddings
            if embed:
                for item in struct.embeds:
                    embed_obj = deepcopy(self.get_struct_obj(embeds[item]))
                    struct.vars.insert(0, (item, GoVar(GoType(embeds[item]))))
                    struct.tags.insert(0, (item, ""))
                    # struct.vars.insert(0,(item,GoVar(embed_obj)))
            # print(name,list([(var[0],var[1].dtype) for var in struct.vars]))
            self.structures[name] = struct
            self.used.add(name)
        else:
            raise GoException(
                "Error: Already used struct name '{}'".format(name)
            )

    def insert_interface(self, name, interface):
        if name not in self.used:
            self.interfaces[name] = interface
            self.used.add(name)
        else:
            raise GoException(
                "Error: Already used interface name '{}'".format(name)
            )

    def insert_func(self, name, params, result, prefix=""):
        name = "{}{}".format(prefix, name)
        if name not in self.functions:
            self.functions[name] = {}
            self.functions[name]["params"] = params
            self.functions[name]["result"] = result
        else:
            raise GoException("Error: already used function name")

    def insert_method(self, name, params, result, receiver, prefix=""):
        name = "{}{}".format(prefix, name)
        for rec in receiver:
            # Indexing by name and receiver
            key = (name, rec.dtype.name)
            if key not in self.methods:
                self.methods[key] = {}
                self.methods[key]["params"] = params
                self.methods[key]["result"] = result
            else:
                raise GoException("Error: already used method name")

    def nested_module(self, module):
        parent = module.parent
        child = module.child
        if isinstance(parent, GoFromModule):
            struct_name = (self.nested_module(parent)).dtype
            return self.get_struct(struct_name, child)
        elif type(parent) is str:
            struct_object = self.get_type(parent)
            struct_name = struct_object.name
            return self.get_struct(struct_name, child)

    def field2index(self, struct, field):
        index = 0
        # print(struct,field)
        # print(struct,struct.name,field)
        # if isinstance(struct, GoType):
        #     struct = self.get_struct_obj(struct.name)
        for struct_field in struct.vars:
            if struct_field[0] == field:
                break
            index += self.get_size(struct_field[1].dtype)
        return index

    def position2index(self, struct, index):
        count = 0
        for i, struct_field in enumerate(struct.vars):
            if index == i:
                return count
            count += self.get_size(struct_field[1].dtype)

    def type_check(
        self, dtype1, dtype2, use="", use_name=None, param_name=None
    ):

        # handles initialisation of arrays
        if (isinstance(dtype1, GoStruct) and isinstance(dtype2, GoType)) or (
            isinstance(dtype1, GoType) and isinstance(dtype2, GoStruct)
        ):
            name1 = dtype1.name
            name2 = dtype2.name
            actual1 = self.get_actual(name1)
            actual2 = self.get_actual(name2)
            if actual1:
                name1 = actual1.name
            if actual2:
                name2 = actual2.name

            if name1 != name2:
                raise GoException(
                    "Error: Operands in array initialization of different types {} and {}".format(
                        name1, name2
                    )
                )

        elif dtype1.__class__ is not dtype2.__class__:
            raise GoException(
                "Error: Operands in '{}' of different type classes '{}' and '{}'".format(
                    use, dtype1.__class__, dtype2.__class__
                )
            )
        elif isinstance(dtype1, GoStruct) and isinstance(dtype2, GoStruct):
            if dtype1.name != dtype2.name:
                raise GoException(
                    "Error : Structs {} and {} are of different types".format(
                        dtype1.name, dtype2.name
                    )
                )

        elif isinstance(dtype1, GoType) and isinstance(dtype1, GoType):
            name1 = dtype1.name
            name2 = dtype2.name
            logging.info("name1 '{}', name2 '{}'".format(name1, name2))

            # handles recursive typdef/aliases
            actual1 = self.get_actual(name1)
            actual2 = self.get_actual(name2)
            if actual1:
                name1 = actual1.name
            if actual2:
                name2 = actual2.name

            for name in [name1, name2]:
                if not self.get_basic_type(name):
                    raise GoException(
                        "Error: '{}' is unregistered dtype".format(name)
                    )

            type_error = False

            if dtype1.basic_lit or dtype2.basic_lit:
                if self.check_basic_type(name1):
                    new_name = self.get_basic_type(name1)["kind"]
                    if new_name != "other":
                        name1 = new_name
                if self.check_basic_type(name2):
                    new_name = self.get_basic_type(name2)["kind"]
                    if new_name != "other":
                        name2 = new_name

                # ensures that int can be assigned to float but not vice versa
                # need to ensure that only dtype2 is basic_lit in case of all non-expression type checking
                if use == "assignment":
                    if name1 == "int" and name1 != name2:
                        type_error = True
                    elif name1 == "float":
                        if name2 != "int" and name2 != "float":
                            type_error = True
                    elif name1 != name2:
                        type_error = True
                # in case of expression only one of the operands will have basic_lit = True as the case when both are basic lit is handled in the parser
                elif use == "expression":
                    if dtype1.basic_lit:
                        basic_lit = name1
                        other = name2
                    else:
                        basic_lit = name2
                        other = name1
                    if basic_lit == "int" and other in ["int", "float"]:
                        pass
                    elif name1 != name2:
                        type_error = True
            elif use != "type casting" and name1 != name2:
                type_error = True

            if type_error:
                if use == "function call":
                    raise GoException(
                        "Error: Mismatch type of param '{}' in function call of '{}'".format(
                            param_name, use_name
                        )
                    )
                elif use == "array conflicts":
                    raise GoException(
                        "Error: Value of '{}' type given to array '{}' instead of '{}' type".format(
                            dtype2.name, use_name, dtype1.name
                        )
                    )
                else:
                    raise GoException(
                        'Error: Operands in "{}" of different types "{}" and '
                        '"{}"'.format(use, name1, name2)
                    )

        elif isinstance(dtype1, GoPointType) and isinstance(
            dtype2, GoPointType
        ):
            self.type_check(dtype1.dtype, dtype2.dtype)


inter_count = 0  # Global counter for intermediate variables


def symbol_table(
    tree,
    table,
    name=None,
    block_type=None,
    store_var="",
    scope_label="",
    insert=False,
    start=0,
    prefix="",
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
        scope_label (str): Denotes the target label(s) for possible
            break/continue (to be passed to every recursive call)
        insert (bool): Whether to insert the function/method or not
    """
    ir_code = ""
    DTYPE = None
    global inter_count
    inter_count += 1

    logging.info(tree)

    def string_handler(item, dtype, store_loc, start=0):
        """Handle storing of an "str" item of given dtype into store_loc."""
        global inter_count
        inter_count += 1
        local_ir = ""
        if store_loc == "":
            pass
        elif isinstance(dtype, GoArray):
            for arr_index in range(
                0, table.get_size(dtype), table.get_size(dtype.dtype)
            ):
                arr_elem = GoPrimaryExpr(
                    item,
                    GoIndex(GoBasicLit(arr_index, GoType("int", True, 1))),
                )
                local_ir += symbol_table(
                    arr_elem,
                    table,
                    name,
                    block_type,
                    store_var=store_loc + "[{}]".format(arr_index),
                    scope_label=scope_label,
                )[1]
        elif isinstance(dtype, GoStruct):
            field_index = 0
            for field, govar in dtype.vars:
                local_ir += string_handler(
                    item + "[{}]".format(field_index),
                    govar.dtype,
                    store_loc + "[{}]".format(field_index),
                )
                field_index += table.get_size(govar.dtype)
        elif hasattr(dtype, "name") and dtype.name == "string":
            left_index_name = "__str_ind_left_{}".format(inter_count)
            right_index_name = "__str_ind_right_{}".format(inter_count)
            cond_name = "__str_cond_{}".format(inter_count)
            table.insert_var(left_index_name, GoType("uint"), "intermediate")
            table.insert_var(right_index_name, GoType("uint"), "intermediate")
            table.insert_var(cond_name, GoType("bool"), "intermediate")

            while_label = "StrStart{}".format(inter_count)
            endwhile_label = "StrEnd{}".format(inter_count)

            local_ir += "{} = 0\n".format(right_index_name)
            local_ir += "{} = {}\n".format(left_index_name, start)
            local_ir += "{}: {} = {}[{}] == 0\n".format(
                while_label, cond_name, item, right_index_name
            )
            local_ir += "if {} goto {}\n".format(cond_name, endwhile_label)
            local_ir += "{}[{}] = {}[{}]\n".format(
                store_loc, left_index_name, item, right_index_name
            )
            local_ir += "{0:} = {0:} + 1\n".format(right_index_name)
            local_ir += "{0:} = {0:} + 1\n".format(left_index_name)
            local_ir += "goto {}\n".format(while_label)
            local_ir += "{}: {}[{}] = 0\n".format(
                endwhile_label, store_loc, left_index_name
            )
        else:
            local_ir += "{} = {}\n".format(store_loc, item)
        return local_ir

    # If code enters here then it looks only for variables, hence
    # we need to make sure that sybmol table is not called uneccessary strings
    # otherwise code will fail
    if type(tree) is str:  # variable
        logging.info("STR: '{}'".format(tree))
        DTYPE = table.get_type(tree)
        ir_code += string_handler(tree, DTYPE, store_var, start=start)

    # Trying to catch GoException raised by SymbTable's methods
    try:
        if isinstance(tree, GoBasicLit):
            DTYPE = tree.dtype
            if store_var == "":
                ir_code = str(tree.item)
            elif hasattr(tree.dtype, "name") and tree.dtype.name == "string":
                for i, char in enumerate(tree.item[1:-1]):
                    ir_code += "{}[{}] = {}\n".format(
                        store_var, i + start, ord(char)
                    )
                ir_code += "{}[{}] = 0\n".format(
                    store_var, len(tree.item) - 2 + start
                )
            else:
                ir_code = "{} = {}\n".format(store_var, tree.item)

        elif isinstance(tree, GoFromModule):
            parent = tree.parent
            child = tree.child
            this_name = tree.name
            # print("parent '{}', child '{}'".format(parent, child))

            if type(parent) is str:
                try:
                    import_table, import_3ac = table.get_import(parent)
                except GoException:
                    pass
                struct_obj = table.get_type(parent)
                struct_name = struct_obj.name
                # print(struct_name)
                # print(parent,struct_obj)
                parent_name = parent
            else:
                parent_name = "__parent_{}".format(inter_count)
                parent_dtype, parent_code = symbol_table(
                    parent,
                    table,
                    name,
                    block_type,
                    store_var=parent_name,
                    scope_label=scope_label,
                )
                ir_code += parent_code
                table.insert_var(parent_name, parent_dtype, "intermediate")
                struct_obj = parent_dtype
                struct_name = parent_dtype.name
            # print(struct_name,child)
            DTYPE = table.get_struct(struct_name, child).dtype
            this_name = "{}[{}]".format(
                parent_name, table.field2index(struct_obj, child)
            )
            ir_code += string_handler(this_name, DTYPE, store_var)

        # TODO: Store modules
        elif isinstance(tree, GoSourceFile):
            # iterating over package imports
            for item in tree.imports:
                # table.imports[item.import_as] = item
                package_name = item.package[:-1][1:]
                # print(package_name)
                package_path = os.path.join(
                    "./packages", "{}.go".format(package_name)
                )
                try:
                    # print(process_code(package_path))
                    table.imports[package_name] = process_code(package_path)
                except FileNotFoundError:
                    raise GoException(
                        "Error : Package name {} is not present in the packages folder".format(
                            package_name
                        )
                    )

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

            for rec in receiver:
                ir_code += "func begin {}.{}\n".format(rec.dtype.name, name)
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
            if result is None:
                result = []
            body = tree.body  # instance of GoBlock
            table.insert_func(name, params, result)
            ir_code += "func begin {}\n".format(name)
            ir_code += symbol_table(
                body,
                table,
                name,
                "function",
                scope_label=scope_label,
                insert=True,
            )[1]
            ir_code += "return 0\nfunc end\n"
            DTYPE = None

        elif isinstance(tree, GoDecl) and tree.kind == "var":
            var_list = tree.declarations
            for item in var_list:
                lhs = item.lhs
                dtype = item.dtype
                rhs = item.rhs
                if len(lhs) != len(rhs) and len(rhs) != 0:
                    raise GoException(
                        "Error: different number of variables and values in "
                        "var declaration"
                    )
                elif len(rhs) == 0 and dtype is None:
                    raise GoException(
                        "Error: neither data type nor values given in var "
                        "declaration"
                    )
                else:
                    # iterating over all expressions to evaluate their types
                    evaluated_types = []
                    inter_names = []
                    for i, expr in enumerate(rhs):
                        decl_name = "__decl{}_{}".format(i, inter_count)
                        expr_dtype, expr_code = symbol_table(
                            expr,
                            table,
                            name,
                            block_type,
                            store_var=decl_name,
                            scope_label=scope_label,
                        )
                        table.insert_var(
                            decl_name, expr_dtype, use="intermediate"
                        )
                        inter_names.append(decl_name)
                        ir_code += expr_code
                        evaluated_types.append(expr_dtype)
                    if len(rhs) != 0:
                        for i, (var, eval_type) in enumerate(
                            zip(lhs, evaluated_types)
                        ):
                            ir_code += "{} = {}\n".format(var, inter_names[i])
                            if dtype is not None:
                                # If defined type is not None then check if the
                                # evaluated type is same as the defined type
                                table.type_check(
                                    dtype, eval_type, "variable declaration"
                                )
                                logging.info(
                                    'var "{}":"{}"'.format(var, dtype)
                                )
                                if isinstance(eval_type, GoType):
                                    dtype.value = eval_type.value
                                table.insert_var(var, dtype)
                            else:
                                table.insert_var(var, eval_type)
                    else:
                        for var in lhs:
                            logging.info('var "{}":"{}"'.format(var, dtype))

                            def zero_initializer(dtype_loc, store_loc):
                                local_ir = ""
                                if isinstance(dtype_loc, GoArray):
                                    for arr_index in range(
                                        0,
                                        table.get_size(dtype_loc),
                                        table.get_size(dtype_loc.dtype),
                                    ):
                                        local_ir += zero_initializer(
                                            dtype_loc.dtype,
                                            store_loc=store_loc
                                            + "[{}]".format(arr_index),
                                        )
                                elif isinstance(dtype_loc, GoStruct):
                                    field_index = 0
                                    for field, govar in dtype_loc.vars:
                                        local_ir += zero_initializer(
                                            dtype_loc.dtype,
                                            store_loc=govar.dtype
                                            + "[{}]".format(field_index),
                                        )
                                        field_index += table.get_size(
                                            govar.dtype
                                        )
                                else:
                                    local_ir += "{} = 0\n".format(store_loc)
                                return local_ir

                            ir_code += zero_initializer(dtype, var)

                            if isinstance(dtype, GoArray):
                                depth = 1
                                curr = dtype
                                while isinstance(curr.dtype, GoArray):
                                    depth = depth + 1
                                    curr = curr.dtype
                                dtype.depth = depth
                            table.insert_var(var, dtype)
            DTYPE = None

        # typedef and aliases
        # still need to incorporate typedef alias during type checking
        elif isinstance(tree, GoDecl) and tree.kind == "type":
            type_list = tree.declarations
            # iterating over AliasDecl and Typedef
            for item in type_list:
                kind = item.kind
                alias = item.alias
                actual = item.actual
                if isinstance(actual, GoStruct):
                    table.insert_struct(alias, actual)
                elif isinstance(actual, GoInterfaceType):
                    table.insert_interface(alias, actual)
                else:
                    table.insert_alias(alias, actual, kind)

                logging.info('{} "{}" : "{}"'.format(kind, alias, actual))
            DTYPE = None

        elif isinstance(tree, GoDecl) and tree.kind == "constant":
            const_list = tree.declarations

            item_list = []

            for item in const_list:
                if isinstance(item.id_list, GoConstSpec):
                    item_list.append(item.id_list)
                else:
                    item_list.append(item)

            for item in item_list:
                id_list = item.id_list
                dtype = item.dtype
                expr_list = item.expr
                if len(id_list) != len(expr_list):
                    raise GoException(
                        "Error: different number of variables and values in "
                        "const declaration"
                    )

                else:
                    evaluated_types = []
                    inter_names = []
                    for i, expr in enumerate(expr_list):
                        const_name = "__const{}_{}".format(i, inter_count)
                        expr_dtype, expr_code = symbol_table(
                            expr,
                            table,
                            name,
                            block_type,
                            store_var=const_name,
                            scope_label=scope_label,
                        )
                        inter_names.append(const_name)
                        table.insert_var(
                            const_name, expr_dtype, use="intermediate"
                        )
                        ir_code += expr_code
                        evaluated_types.append(expr_dtype)

                    for i, (const, eval_type) in enumerate(
                        zip(id_list, evaluated_types)
                    ):
                        if dtype is None:
                            table.insert_const(const, eval_type)
                        else:
                            table.type_check(
                                dtype, eval_type, "const declaration"
                            )
                            # Treating constant declarations as variable assignment
                            ir_code += "{} = {}\n".format(
                                const, inter_names[i]
                            )
                            if isinstance(eval_type, GoType):
                                dtype.value = eval_type.value
                            logging.info(
                                'const "{}":"{}"'.format(const, dtype)
                            )
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
                    # TODO: need to handle parameters with None name
                if len(child_table.activation_record) > 0:
                    last_offset = child_table.activation_record[-1][
                        1
                    ].activation_offset
                for i in range(len(child_table.activation_record)):
                    child_table.activation_record[i][
                        1
                    ].activation_offset -= last_offset
                child_table.activation_offset = [0]
                for item in ["dynamic_link", "return_address", "static_link"]:
                    child_table.insert_var(item, GoPointType(None))
                table.functions[name]["body"] = child_table

            elif block_type == "method" and insert:
                child_table = SymbTable(table, "method")
                key = (name[0], name[1].dtype.name)
                for param in table.methods[key]["params"]:
                    if param.name:
                        child_table.insert_var(param.name, param.dtype)

                struct_obj = table.get_struct_obj(name[1].dtype.name)
                struct_obj.name = name[1].dtype.name
                struct_obj.size = table.struct_size(name[1].dtype.name)
                logging.info("STRUCT METHOD SIZE {}".format(struct_obj.size))
                child_table.insert_var(name[1].name, struct_obj)
                if len(child_table.activation_record) > 0:
                    last_offset = child_table.activation_record[-1][
                        1
                    ].activation_offset
                for i in range(len(child_table.activation_record)):
                    child_table.activation_record[i][
                        1
                    ].activation_offset -= last_offset
                child_table.activation_offset = [0]
                for item in ["dynamic_link", "return_address", "static_link"]:
                    child_table.insert_var(item, GoPointType(None))
                table.methods[key]["body"] = child_table

            else:
                child_table = SymbTable(table)
                table.scopes.append(child_table)

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

            if block_type == "function" and insert:
                if table.functions[name]["result"] is None:
                    ir_code += "return\n"
            elif block_type == "method" and insert:
                key = (name[0], name[1].dtype.name)
                if table.methods[key]["result"] is None:
                    ir_code += "return\n"
                ir_code += "return\n"

        elif isinstance(tree, GoAssign):
            lhs = tree.lhs
            rhs = tree.rhs
            if len(lhs) != len(rhs):
                # Check if RHS is function return
                # Will be checked later for multiple return
                if (
                    len(rhs) != 1
                    or not isinstance(rhs[0], GoPrimaryExpr)
                    or not isinstance(rhs[0].rhs, GoArguments)
                ):
                    raise GoException(
                        "Error: Different number of variables and values in "
                        "assign operation"
                    )
            lhs_3ac = []

            def _get_loc(curr, ind_cnt=0):
                nonlocal ir_code  # Use ir_code of `symbol_table`
                error = False

                if isinstance(curr, GoPrimaryExpr):
                    if isinstance(curr.rhs, GoSelector):
                        # No checking here; it is done ahead
                        return (
                            _get_loc(curr.lhs, ind_cnt) + "." + curr.rhs.child
                        )
                    elif isinstance(curr.rhs, GoIndex):
                        index_name = "__index{}_{}".format(
                            ind_cnt, inter_count
                        )
                        dtype, index_code = symbol_table(
                            curr.rhs.index,
                            table,
                            name,
                            block_type,
                            store_var=index_name,
                            scope_label=scope_label,
                        )
                        table.insert_var(index_name, dtype, use="intermediate")
                        table.type_check(dtype, GoType("int", True))
                        ir_code += index_code
                        lhs_dtype = symbol_table(curr.lhs, table)[0]
                        index_size = table.get_size(lhs_dtype.dtype)
                        if index_size != 1:
                            ir_code += "{} = {} * {}\n".format(
                                index_name, index_name, index_size
                            )

                        if isinstance(lhs_dtype.dtype, GoArray):
                            # Multi-dimensional array
                            lhs_name = "__index_lhs{}_{}".format(
                                ind_cnt, inter_count
                            )
                            table.insert_var(
                                lhs_name, lhs_dtype, "intermediate"
                            )
                            lhs_loc = _get_loc(curr.lhs, ind_cnt + 1)
                            ir_code += "{} = {} + {}\n".format(
                                lhs_name, lhs_loc, index_name
                            )
                            return lhs_name
                        else:
                            return _get_loc(
                                curr.lhs, ind_cnt + 1
                            ) + "[{}]".format(index_name)
                    else:
                        error = True
                elif isinstance(curr, GoExpression):
                    error = True
                elif isinstance(curr, GoUnaryExpr):
                    if curr.op == "*":
                        if type(curr.expr) is str:
                            if not isinstance(
                                table.get_type(curr.expr), GoPointType
                            ):
                                raise GoException(
                                    "Error: {} not pointer type".format(
                                        curr.expr
                                    )
                                )
                            else:
                                return "*" + _get_loc(curr.expr, ind_cnt)
                        elif isinstance(curr.expr, GoUnaryExpr):
                            return "*" + _get_loc(curr.expr, ind_cnt)
                            loc_lhs += "*"

                    else:
                        error = True
                elif isinstance(curr, GoFromModule):
                    # No checking here; it is done ahead
                    parent_dtype = symbol_table(
                        curr.parent,
                        table,
                        name,
                        block_type,
                        scope_label=scope_label,
                    )[0]
                    if not isinstance(parent_dtype, GoStruct):
                        raise GoException(
                            'Cannot access attribute "{}" as "{}" is not a struct'.format(
                                curr.child, parent_name
                            )
                        )
                    child_index = table.field2index(parent_dtype, curr.child)
                    return _get_loc(curr.parent, ind_cnt) + "[{}]".format(
                        child_index
                    )
                elif not table.lookup(curr):
                    raise GoException(
                        'Error: "{}" not declared before use'.format(curr)
                    )
                elif type(curr) is str:
                    return curr
                if error:
                    raise GoException(
                        'Error: Expression "{}" cannot be assigned '
                        "value".format(var)
                    )

            for var in lhs:
                lhs_3ac.append(_get_loc(var))

            if len(lhs) != len(rhs):
                # Check if function return RHS is valid
                return_name = "__func_ret_{}".format(inter_count)
                func_dtype, func_code = symbol_table(
                    rhs[0],
                    table,
                    name,
                    block_type,
                    store_var=return_name,
                    scope_label=scope_label,
                )
                if len(lhs) != len(func_dtype):
                    raise GoException(
                        "Error: Different number of variables and values in "
                        "function return; expected {}".format(len(func_dtype))
                    )
                else:
                    ir_code += func_code

                field_list = [
                    GoStructField(["__val{}".format(i)], func_dtype[i], "")
                    for i in range(len(func_dtype))
                ]
                return_struct = GoStruct(field_list)
                table.insert_var(return_name, return_struct, "intermediate")

                arg_index = 0
                for i in range(len(func_dtype)):
                    ir_code += "{} = {}[{}]\n".format(
                        lhs_3ac[i], return_name, arg_index
                    )
                    arg_index += table.get_size(func_dtype[i])

            else:
                for i, (var, expr) in enumerate(zip(lhs, rhs)):
                    logging.info('assign: "{}" : "{}"'.format(var, expr))
                    # can have only struct fields, variables, array on the LHS.
                    dtype1 = None
                    if isinstance(var, GoPrimaryExpr):
                        left = var
                        depth = 0
                        indexes = []
                        while isinstance(left.lhs, GoPrimaryExpr):
                            if isinstance(left.rhs.index, GoBasicLit):
                                indexes.append(left.rhs.index.item)
                            else:
                                indexes.append(0)
                            left = left.lhs
                            depth = depth + 1
                        if isinstance(left.rhs.index, GoBasicLit):
                            indexes.append(left.rhs.index.item)
                        else:
                            indexes.append(0)

                        dtype1 = table.get_type(left.lhs)
                        if (
                            dtype1.length.item <= indexes[len(indexes) - 1]
                            or indexes[len(indexes) - 1] < 0
                        ):
                            raise GoException("Error : Index Out of bound")
                        indexes.pop()
                        dtype1 = dtype1.dtype
                        while depth > 0:
                            if (
                                dtype1.length.item <= indexes[len(indexes) - 1]
                                or indexes[len(indexes) - 1] < 0
                            ):
                                raise GoException("Error : Index Out of bound")
                            indexes.pop()
                            dtype1 = dtype1.dtype
                            depth = depth - 1

                    elif type(var) is str:
                        dtype1 = table.get_type(var, side="left")

                    elif isinstance(var, GoUnaryExpr) and var.op == "*":
                        symbol_table(
                            var.expr,
                            table,
                            name,
                            block_type,
                            scope_label=scope_label,
                        )
                        if type(var.expr) is str:
                            if not isinstance(
                                table.get_type(var.expr), GoPointType
                            ):
                                raise GoException(
                                    "Error: {} not pointer type".format(
                                        var.expr
                                    )
                                )
                            var.dtype = table.get_type(var.expr).dtype
                            dtype1 = var.dtype

                        elif (
                            isinstance(var.expr, GoUnaryExpr)
                            and var.expr.op == "*"
                        ):
                            if not isinstance(var.expr.dtype, GoPointType):
                                raise GoException(
                                    "Error: {} not pointer type".format(
                                        var.expr
                                    )
                                )
                            var.dtype = var.expr.dtype.dtype
                            dtype1 = var.dtype

                    # NEW START
                    elif isinstance(var, GoFromModule):
                        parent = var.parent
                        child = var.child
                        # currently handles accessing a field of a struct
                        if type(parent) is str:
                            struct_name = table.get_type(parent).name
                            dtype1 = table.get_struct(struct_name, child).dtype

                        # handles nesting of structs
                        elif isinstance(parent, GoFromModule):
                            logging.info(
                                "parent '{}', child '{}'".format(parent, child)
                            )
                            struct_name = (
                                table.nested_module(parent)
                            ).dtype.name
                            logging.info(
                                "struct name '{}'".format(struct_name)
                            )
                            dtype1 = table.get_struct(struct_name, child).dtype

                    if dtype1 is None:
                        print("Warning: Getting None dtype in Assignment")
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
                    if type(dtype2) is list:
                        if len(dtype2) == 0:
                            raise GoException(
                                "Function with no return value cannot be used in assignement"
                            )
                        else:
                            raise GoException(
                                "Function with multiple returns not applicable in "
                                "single return context"
                            )
                    table.type_check(dtype1, dtype2, "assignment")

                    DTYPE = None

        elif isinstance(tree, GoShortDecl):
            id_list = tree.id_list
            expr_list = tree.expr_list
            check = True
            for expr in expr_list:
                if isinstance(expr, GoPrimaryExpr) and isinstance(
                    expr.rhs, GoArguments
                ):
                    if type(expr.lhs) is str:
                        length = len(table.get_func(expr.lhs, "result")[0])
                    else:
                        continue
                    if length > 1:
                        check = False
                    elif length == 0:
                        raise GoException(
                            "SyntaxError: Void function {} used as value".format(
                                expr.lhs
                            )
                        )

            if check is True:
                if len(id_list) != len(expr_list):
                    raise GoException(
                        "Error: Different number of variables and values in short declaration"
                    )

            else:
                if len(expr_list) > 1:
                    raise GoException(
                        "Error: multiple-value function {} used in single-value context".format(
                            expr.lhs
                        )
                    )
                elif len(id_list) != len(
                    table.get_func(expr.lhs, "result")[0]
                ):
                    raise GoException(
                        "Error: Different number of variables and values in short declaration"
                    )

                id_list = [id_list]

            for var in id_list:
                if type(var) is not str and type(var) is not list:
                    raise GoException(
                        "SyntaxError: LHS '{}' is not a variable".format(var)
                    )
                if type(var) is list:
                    for child in var:
                        if type(child) is not str:
                            raise GoException(
                                "SyntaxError: LHS '{}' is not a variable".format(
                                    var
                                )
                            )

            for var, expr in zip(id_list, expr_list):
                logging.info('short decl: "{}" : "{}"'.format(var, expr))
                dtype, rhs_code = symbol_table(
                    expr,
                    table,
                    name,
                    block_type,
                    store_var=var,
                    scope_label=scope_label,
                )
                ir_code += rhs_code
                # if isinstance(dtype,GoArray) and isinstance(dtype.dtype,GoArray):
                #     print(var,dtype.dtype.dtype)
                if type(var) is str:
                    table.insert_var(var, dtype)
                else:
                    for child1, child2 in zip(var, dtype):
                        table.insert_var(child1, child2)

            DTYPE = None

        elif isinstance(tree, GoExpression):
            start_label = "Start{}".format(inter_count)
            mid_label = "Mid{}".format(inter_count)
            end_label = "End{}".format(inter_count)

            lhs = tree.lhs
            op = tree.op
            rhs = tree.rhs
            logging.info('exp: lhs "{}", rhs "{}"'.format(lhs, rhs))

            # INCOMPLETE : need to handle cases for array types, struct types,
            # interfaces, function, pointer
            lhs_name = "__lhs_{}".format(inter_count)
            rhs_name = "__rhs_{}".format(inter_count)
            dtype1, lhs_code = symbol_table(
                lhs,
                table,
                name,
                block_type,
                store_var=lhs_name,
                scope_label=scope_label,
            )
            table.insert_var(lhs_name, dtype1, use="intermediate")
            dtype2, rhs_code = symbol_table(
                rhs,
                table,
                name,
                block_type,
                store_var=rhs_name,
                scope_label=scope_label,
            )
            table.insert_var(rhs_name, dtype1, use="intermediate")

            if dtype1.name == "string" and dtype2.name == "string":
                length = len(dtype1.value) - 2
                # print(length)
                dtype2, rhs_code = symbol_table(
                    rhs,
                    table,
                    name,
                    block_type,
                    store_var=lhs_name,
                    scope_label=scope_label,
                    start=length,
                )

            if dtype1.name == "bool" and dtype2.name == "bool":
                ir_code += "{}: ".format(start_label)
                ir_code += lhs_code
                if op == "||":
                    ir_code += "{} = True\n".format(rhs_name)
                    ir_code += "if {} goto {}\n".format(lhs_name, end_label)
                elif op == "&&":
                    ir_code += "if {} goto {}\n".format(lhs_name, mid_label)
                    ir_code += "{} = True\n".format(rhs_name)
                    ir_code += "goto {}\n".format(end_label)
                    ir_code += "{}: ".format(mid_label)

                ir_code += rhs_code
                ir_code += "{}: ".format(end_label)
                ir_code += "{} = {} {} {}\n".format(
                    store_var, lhs_name, op, rhs_name
                )

            elif dtype1.name == "string" and dtype2.name == "string":
                ir_code += lhs_code + rhs_code
                ir_code += "{} = {}\n".format(store_var, lhs_name)
            else:
                ir_code += lhs_code + rhs_code
                ir_code += "{} = {} {} {}\n".format(
                    store_var, lhs_name, op, rhs_name
                )

            logging.info('exp lhs: "{}", rhs: "{}"'.format(dtype1, dtype2))

            if dtype1.__class__ is not dtype2.__class__:
                raise GoException(
                    "Error: Operands in expression of different type classes '{}' "
                    "and '{}'".format(dtype1.__class__, dtype2.__class__)
                )

            # INCOMPLETE need to check for other type classes
            if isinstance(dtype1, GoType) and isinstance(dtype2, GoType):
                name1 = dtype1.name
                name2 = dtype2.name

                table.type_check(dtype1, dtype2, "expression")
                if dtype1.basic_lit is False:
                    name = dtype1.name
                else:
                    name = dtype2.name

                if name == "bool" and op not in ["&&", "||"]:
                    raise GoException(
                        "Error: Invalid operator for bool operands"
                    )
                elif op in ["&&", "||"] and name != "bool":
                    raise GoException(
                        "Error: Invalid operand types '{}' and '{}' for bool operator".format(
                            name1, name2
                        )
                    )
                elif op in [">>", "<<", "&", "&^", "^", "|", "%"] and (
                    not table.check_basic_type(name)
                    or table.get_basic_type(name)["kind"] != "int"
                ):
                    raise GoException(
                        "Error: Operator '{}' is not applicable for '{}'".format(
                            op, name
                        )
                    )
                elif name == "string" and op not in [
                    "+",
                    "==",
                    "!=",
                    ">=",
                    "<=",
                    ">",
                    "<",
                ]:
                    raise GoException(
                        "Error: Invalid operator for string type"
                    )
                else:
                    logging.info(
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
            cond_name = "__cond_{}".format(inter_count)
            cond_dtype, cond_code = symbol_table(
                tree.cond,
                newtable,
                name,
                block_type,
                store_var=cond_name,
                scope_label=scope_label,
            )
            ir_code += cond_code
            table.insert_var(cond_name, cond_dtype, use="intermediate")

            # Choosing the labels
            if_label = "If{}".format(inter_count)
            endif_label = "EndIf{}".format(inter_count)

            ir_code += "if {} goto {}\n".format(cond_name, if_label)
            if (
                not (
                    isinstance(tree.cond, GoExpression)
                    or isinstance(tree.cond, GoBasicLit)
                )
                or not isinstance(tree.cond.dtype, GoType)
                or tree.cond.dtype.name != "bool"
            ):
                raise GoException(
                    "Error: If condition is not evaluating to bool"
                )
            ir_code += symbol_table(
                tree.inelse,
                newtable,
                name,
                block_type,
                scope_label=scope_label,
            )[1]
            ir_code += "goto {}\n{}: ".format(endif_label, if_label)
            ir_code += symbol_table(
                tree.inif, newtable, name, block_type, scope_label=scope_label
            )[1]
            ir_code += "{}: ".format(endif_label)
            table.scopes.append(newtable)
            DTYPE = None

        elif isinstance(tree, GoFor):
            new_table = SymbTable(table)
            logging.info("Entered GoFor")
            cond_label = "ForCond{}".format(inter_count)
            for_label = "For{}".format(inter_count)
            postfor_label = "ForPost{}".format(inter_count)
            endfor_label = "EndFor{}".format(inter_count)

            DTYPE = None

            if isinstance(tree.clause, GoForClause):
                logging.info("Entered GoForClause")
                if (
                    (tree.clause.init is not None)
                    and not isinstance(tree.clause.init, GoShortDecl)
                    and not isinstance(tree.clause.init, GoAssign)
                ):
                    raise GoException(
                        "Error: Error in for loop Initialization"
                    )
                elif (
                    (tree.clause.expr is not None)
                    and not isinstance(tree.clause.expr, GoBasicLit)
                    and not isinstance(tree.clause.expr, GoExpression)
                ):
                    raise GoException("Error: Error in for loop Condition")
                elif (
                    (tree.clause.post is not None)
                    and not isinstance(tree.clause.post, GoAssign)
                    and not (
                        isinstance(tree.clause.post, GoUnaryExpr)
                        and tree.clause.post.op in ["++", "--"]
                    )
                ):
                    raise GoException(
                        "Error: Error in for loop post expression"
                    )

                ir_code += symbol_table(
                    tree.clause.init,
                    new_table,
                    name,
                    block_type,
                    scope_label=scope_label,
                )[1]
                ir_code += "{}: ".format(cond_label)
                fcond_name = "__fcond_{}".format(inter_count)
                fcond_dtype, fcond_code = symbol_table(
                    tree.clause.expr,
                    new_table,
                    name,
                    block_type,
                    store_var=fcond_name,
                    scope_label=scope_label,
                )
                ir_code += fcond_code
                if tree.clause.expr is not None:
                    new_table.insert_var(
                        fcond_name, fcond_dtype, use="intermediate"
                    )
                    ir_code += "if {} goto {}\ngoto {}\n{}: ".format(
                        fcond_name, for_label, endfor_label, for_label
                    )
                else:
                    ir_code += "goto {}\ngoto {}\n{}: ".format(
                        for_label, endfor_label, for_label
                    )
                post_code = symbol_table(
                    tree.clause.post,
                    new_table,
                    name,
                    block_type,
                    scope_label=scope_label,
                )[1]

                if (
                    tree.clause.expr is not None
                ) and tree.clause.expr.dtype.name is not "bool":
                    raise GoException(
                        "Error: Loop condition must be bool type"
                    )

            elif isinstance(tree.clause, GoRange):
                raise NotImplementedError("Range not implemented")

            ir_code += symbol_table(
                tree.infor,
                new_table,
                name,
                block_type,
                scope_label="{}|{}".format(endfor_label, postfor_label),
            )[1]
            ir_code += "{}: ".format(postfor_label) + post_code
            ir_code += "goto {}\n{}: ".format(cond_label, endfor_label)

            table.scopes.append(new_table)

        elif isinstance(tree, GoSwitch):
            new_table = SymbTable(table)
            symbol_table(
                tree.stmt, new_table, name, block_type, scope_label=scope_label
            )
            table.scopes.append(new_table)

            newtable = SymbTable(new_table)
            for case_stmt in tree.case_list:
                for child in case_stmt.expr_list:
                    symbol_table(
                        child,
                        newtable,
                        name,
                        block_type,
                        scope_label=scope_label,
                    )
                newnewtable = SymbTable(newtable)
                for child in case_stmt.stmt_list:
                    symbol_table(
                        child,
                        newnewtable,
                        name,
                        block_type,
                        scope_label="Switch",
                    )
                newtable.scopes.append(newnewtable)
            new_table.scopes.append(newtable)

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
            switch_label = "Switch{}".format(inter_count)
            DTYPE, ir_code = symbol_table(
                if_conv, copy_table, name, block_type, scope_label=switch_label
            )

            old_switch_label = re.search(
                r"\w+", ir_code.split("\n")[-1][::-1]
            ).group()[::-1]
            ir_code = ir_code.replace(old_switch_label, switch_label)

        # XXX: 3AC necessary ??
        # DTYPE needs to be verified
        # ==========================================================================
        elif isinstance(tree, GoArray):
            if tree.length != "variable":
                symbol_table(
                    tree.length,
                    table,
                    name,
                    block_type,
                    scope_label=scope_label,
                )
            symbol_table(
                tree.dtype, table, name, block_type, scope_label=scope_label
            )
            if isinstance(tree.dtype, GoArray):
                tree.depth = tree.dtype.depth + 1
                tree.final_type = tree.dtype.final_type
                if not isinstance(tree.dtype.dtype, GoArray):
                    tree.dtype.dtype = tree.dtype.final_type
            else:
                try:
                    dtype1 = table.get_struct_obj(tree.dtype.name)
                    tree.final_type = dtype1
                except GoException:
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

            # Need to handle the case for typedef/alias of dtype.name
            if isinstance(dtype, GoType) and (
                not table.check_basic_type(dtype.name)
                or table.get_basic_type(dtype.name)["kind"] != "int"
            ):
                tree.size = dtype.value * tree.dtype.size
                logging.info("ARRAY SIZE: {}".format(tree.size))
                raise GoException("Error: Array length must be an integer")

            DTYPE = tree.final_type

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
                if (
                    not table.check_basic_type(name)
                    or table.get_basic_type(name)["kind"] != "int"
                ):
                    raise GoException("Error: Index of array is not integer")
            else:
                raise GoException("Error: Index of array is not integer")
            DTYPE = dtype

        elif isinstance(tree, GoPrimaryExpr):
            rhs = tree.rhs
            lhs = tree.lhs
            # print(lhs,rhs)
            if isinstance(rhs, GoIndex):  # array indexing
                logging.info("array = '{}'".format(lhs))
                # TODO: need to handle multiple return from function
                if isinstance(lhs, GoPrimaryExpr):
                    lhs.depth = tree.depth + 1
                else:
                    if not table.lookup(lhs):
                        raise GoException(
                            "Error: '{}' array not declared".format(lhs)
                        )
                    elif not isinstance(table.get_type(lhs), GoArray):
                        raise GoException("Error: '{}' not array".format(lhs))
                    elif tree.depth > table.get_type(lhs).depth:
                        raise GoException(
                            "Error: Incorrect number of indexes in array '{}'".format(
                                lhs
                            )
                        )

                    tree.dtype = (table.get_type(lhs)).dtype
                    # if the array if one dimensional then simply return the final_type of that array
                    # if not isinstance(tree.dtype,GoArray):
                    #     tree.dtype = (table.get_type(lhs)).final_type
                    # print(lhs,tree.dtype)
                    DTYPE = tree.dtype

                left = tree
                depth = 0
                indexes = []
                while isinstance(left.lhs, GoPrimaryExpr):
                    if isinstance(left.rhs.index, GoBasicLit):
                        indexes.append(left.rhs.index.item)
                    else:
                        indexes.append(0)
                    left = left.lhs
                    depth = depth + 1
                if isinstance(left.rhs.index, GoBasicLit):
                    indexes.append(left.rhs.index.item)
                else:
                    indexes.append(0)

                dtype1 = table.get_type(left.lhs)
                if (
                    dtype1.length.item <= indexes[len(indexes) - 1]
                    or indexes[len(indexes) - 1] < 0
                ):
                    pass
                    # raise GoException("Error : Index Out of bound")
                indexes.pop()
                dtype1 = dtype1.dtype
                while depth > 0:
                    if (
                        dtype1.length.item <= indexes[len(indexes) - 1]
                        or indexes[len(indexes) - 1] < 0
                    ):
                        pass
                        # raise GoException("Error : Index Out of bound")
                    indexes.pop()
                    dtype1 = dtype1.dtype
                    depth = depth - 1

                lhs_name = "__indlhs_{}".format(inter_count)
                if type(lhs) is not str:
                    lhs_dtype, lhs_code = symbol_table(
                        lhs,
                        table,
                        name,
                        block_type,
                        store_var=lhs_name,
                        scope_label=scope_label,
                    )
                else:
                    lhs_dtype = table.get_type(lhs)
                    lhs_code = "{} = {}\n".format(lhs_name, lhs)

                if isinstance(lhs, GoPrimaryExpr):
                    #     if isinstance(lhs.dtype,GoArray) and isinstance(lhs.dtype.dtype,GoArray)
                    #         tree.dtype = lhs.dtype.dtype
                    tree.dtype = lhs.dtype.dtype
                    DTYPE = tree.dtype
                    # print(tree.dtype.name)
                    # print("HERE")

                ir_code += lhs_code
                table.insert_var(lhs_name, lhs_dtype, use="intermediate")

                rhs_name = "__indrhs_{}".format(inter_count)
                rhs_dtype, rhs_code = symbol_table(
                    rhs,
                    table,
                    name,
                    block_type,
                    store_var=rhs_name,
                    scope_label=scope_label,
                )
                ir_code += rhs_code
                ir_code += "{} = {} * {}\n".format(
                    rhs_name, rhs_name, table.get_size(lhs_dtype.dtype)
                )
                table.insert_var(rhs_name, rhs_dtype, use="intermediate")
                if isinstance(lhs_dtype, GoArray) and isinstance(
                    lhs_dtype.dtype, GoArray
                ):
                    ir_code += "{} = {} + {}\n".format(
                        store_var, lhs_name, rhs_name, scope_label=scope_label
                    )
                else:
                    ir_code += "{} = {}[{}]\n".format(
                        store_var, lhs_name, rhs_name, scope_label=scope_label
                    )

            elif isinstance(rhs, GoArguments):  # fuction call
                use = None
                argument_list = rhs.expr_list
                is_type_cast = False  # Type-casting has the same syntax

                if type(lhs) is str:
                    use = "function"
                    logging.info("FUNCTION CALL '{}'".format(lhs))
                    func_name = lhs
                    # type checking of arguments passed to function
                    argument_list = rhs.expr_list
                    params_list, is_type_cast = table.get_func(
                        func_name, "params"
                    )
                    if is_type_cast:
                        logging.info("type-casting '{}'".format(func_name))

                    result = table.get_func(func_name, "result")[0]
                    # assert result is None or isinstance(result, GoParam) ## Functions with no return value

                    # Get function name/location in memory
                    func_loc = func_name

                elif isinstance(lhs, GoFromModule):
                    parent = lhs.parent
                    child = lhs.child
                    # print(
                    #     "METHOD/IMPORT parent: '{}',child: '{}'".format(parent, child)
                    # )
                    if isinstance(parent, GoFromModule):
                        raise NotImplementedError(
                            "Multiple imports not done yet"
                        )
                    # single imports
                    # ID DOT ID
                    elif type(parent) is str:
                        try:
                            use = "method"
                            # check if the child is actually a method defined for parent (struct)
                            # check is the type of arguments passed to child are same as that defined in method declaration
                            method_name = child
                            struct_name = (table.get_type(parent)).name
                            logging.info(
                                "method call'{}' on struct '{}' with arguments '{}'".format(
                                    method_name, struct_name, rhs
                                )
                            )
                            key = (method_name, struct_name)
                            # type checking of arguments passed to function
                            params_list = table.get_method(key, "params")

                            result = table.get_method(key, "result")

                            # Get function name/location in memory
                            func_loc = lhs.name

                        # package imports
                        # TODO @Harish handle the 3AC
                        except GoException:
                            import_table, import_3ac = table.get_import(parent)
                            if import_table.lookup_function(child) is False:
                                raise GoException(
                                    "Error : function {} is not supported by the {} package".format(
                                        child, parent
                                    )
                                )
                            use = "import"

                if use != "import":
                    if len(argument_list) is not len(params_list):
                        raise GoException(
                            'Error: "{}" parameters passed to function "{}" '
                            'instead of "{}"'.format(
                                len(argument_list), func_name, len(params_list)
                            )
                        )

                    inter_names = []
                    depth_num = inter_count
                    for i, (argument, param) in enumerate(
                        zip(argument_list, params_list)
                    ):
                        arg_name = "__arg{}_{}".format(i, depth_num)
                        arg_dtype, arg_code = symbol_table(
                            argument,
                            table,
                            name,
                            block_type,
                            store_var=arg_name,
                            scope_label=scope_label,
                        )
                        ir_code += arg_code
                        table.insert_var(
                            arg_name, arg_dtype, use="intermediate"
                        )
                        inter_names.append(arg_name)
                        table.type_check(
                            param.dtype,
                            arg_dtype,
                            "type casting"
                            if is_type_cast
                            else "function call",
                            func_name,
                            param.name,
                        )

                    if len(result) > 1:
                        result_type = [item.dtype for item in result]
                    elif len(result) == 1:
                        result_type = result[0].dtype
                    else:
                        result_type = []
                    tree.dtype = []

                    DTYPE = result_type

                    if is_type_cast:
                        ir_code += "{} = {} {}\n".format(
                            store_var, result_type.name, inter_names[0]
                        )
                    else:
                        ir_code += "".join(
                            [
                                "param {}\n".format(inter_names[i])
                                for i in range(len(argument_list))
                            ]
                        )
                        if store_var == "":
                            temp_name = "__call_temp_{}".format(inter_count)
                            table.insert_var(temp_name, DTYPE, "intermediate")
                            ir_code += "{} = call {}, {}\n".format(
                                temp_name, func_loc, len(argument_list)
                            )
                        elif type(store_var) is not list:
                            ir_code += "{} = call {}, {}\n".format(
                                store_var, func_loc, len(argument_list)
                            )
                        else:
                            temp_name = "__call_temp_{}".format(inter_count)
                            table.insert_var(temp_name, DTYPE, "intermediate")
                            ir_code += "{} = call {},{}\n".format(
                                temp_name, func_loc, len(argument_list)
                            )
                            count = 0
                            for i, child in enumerate(store_var):
                                ir_code += "{} = {}[{}]\n".format(
                                    child, temp_name, count
                                )
                                count += table.get_size(
                                    table.get_func(tree.lhs, "result")[0][
                                        i
                                    ].dtype
                                )

            elif isinstance(rhs, GoSelector):
                child = rhs.child
                lhs_name = "__sellhs_{}".format(inter_count)
                lhs_dtype, lhs_code = symbol_table(
                    lhs,
                    table,
                    name,
                    block_type,
                    store_var=lhs_name,
                    scope_label=scope_label,
                )
                ir_code += lhs_code
                if isinstance(lhs_dtype, GoStruct):
                    struct_name = lhs_dtype.name
                    if type(child) is str:
                        DTYPE = table.get_struct(struct_name, child).dtype
                    struct_obj = table.get_struct_obj(struct_name)
                    ir_code += "{} = {}[{}]\n".format(
                        store_var,
                        lhs_name,
                        table.field2index(struct_obj, child),
                    )

        # TODO(later): check number of elements in array same as that
        # specified
        elif isinstance(tree, GoKeyedElement):
            logging.info("keyedelement: {} {}".format(store_var, tree.use))
            if tree.use == "array":

                def num2index(store_loc, element_type):
                    search = re.search(r"--\[([^\]]*)\]--", store_loc)
                    if search is not None:
                        store_index = table.get_size(element_type) * int(
                            search.groups()[0]
                        )
                        store_loc = re.sub(
                            r"--\[([^\]]*)\]--",
                            "[{}]".format(store_index),
                            store_loc,
                        )
                    return store_loc

                if isinstance(tree.element, GoBasicLit) or isinstance(
                    tree.element, GoExpression
                ):
                    element_type = tree.element.dtype
                    store_var = num2index(store_var, element_type)
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
                        ir_code += "{} = {}\n".format(
                            store_var, tree.element.item
                        )
                    tree.size += 1
                elif type(tree.element) is str:
                    element_type = table.get_type(tree.element)
                    store_var = num2index(store_var, element_type)
                    ir_code += symbol_table(
                        tree.element,
                        table,
                        name,
                        block_type,
                        store_var=store_var,
                        scope_label=scope_label,
                    )[1]
                    tree.size += 1
                else:  # LiteralValue is a list
                    # Convert multiple indexing ([][]) to single indexing ([])
                    len_arr = len(
                        [
                            True
                            for child in tree.element
                            if isinstance(child, GoKeyedElement)
                        ]
                    )
                    search = re.search(r"--\[([^\]]*)\]--", store_var)
                    if search is None:
                        parent_index = 0
                    else:
                        parent_index = len_arr * int(search.groups()[0])
                        store_var = store_var[: search.start()]

                    depth = 0
                    child_count = 0
                    cur_size = 0
                    for child in tree.element:
                        if isinstance(child, GoKeyedElement):
                            child.use = "array"
                            store_loc = "{}--[{}]--".format(
                                store_var, parent_index + child_count
                            )
                            child_dtype, child_code = symbol_table(
                                child,
                                table,
                                name,
                                block_type,
                                store_var=store_loc,
                                scope_label=scope_label,
                            )
                            ir_code += child_code
                            child.dtype = child_dtype
                            child_count += 1

                            count = 1
                            temp_child = child
                            while type(temp_child.element) is list:
                                count = count * len(temp_child.element)
                                temp_child = temp_child.element[0]
                            if depth == 0:
                                depth = child.depth
                            elif depth != child.depth:
                                raise GoException(
                                    "Error: Wrong array declaration"
                                )
                            logging.info("child dtype {}".format(child.dtype))
                            element_type = child.dtype
                            tree.size += child.size

                            if cur_size == 0:
                                cur_size = child.size
                            elif cur_size != child.size:
                                raise GoException(
                                    "Error: Incorrect number of elements in array"
                                )
                        if tree.dtype is None:
                            # print(element_type.name)
                            tree.dtype = element_type
                        else:
                            # print(tree.dtype.name,element_type.name)
                            table.type_check(
                                tree.dtype, element_type, "array conflicts"
                            )

                    tree.depth = depth + 1
                tree.dtype = element_type
                # print(tree.dtype)
                logging.info("tree.dtype '{}'".format(tree.dtype))

            elif tree.use == "struct":
                element = tree.element
                logging.info("struct element '{}'".format(element))
                if (
                    isinstance(element, GoBasicLit)
                    or isinstance(element, GoExpression)
                    or isinstance(element, GoCompositeLit)
                    or type(element) is str
                ):
                    element_type, ir_code = symbol_table(
                        element,
                        table,
                        name,
                        block_type,
                        scope_label=scope_label,
                        store_var=store_var,
                    )

                elif type(element) is list:
                    raise GoException(
                        "Error: Missing type in composite literal"
                    )
                tree.dtype = element_type

            DTYPE = tree.dtype
            # print(DTYPE.name)

        # UN-IMPLEMENTED
        # XXX long declaration of arrays not working
        # XXX no check implemented for valid indicies in arrays
        elif isinstance(tree, GoCompositeLit):
            logging.info(
                "tree.dtype {}, tree.value {}".format(tree.dtype, tree.value)
            )
            symbol_table(
                tree.dtype, table, name, block_type, scope_label=scope_label
            )

            elem_num = 0
            # How does this handle array of structs
            if isinstance(tree.dtype, GoArray):
                symbol_table(
                    tree.dtype,
                    table,
                    name,
                    block_type,
                    scope_label=scope_label,
                )
                dtype = tree.dtype.final_type
                # if type of the array is a struct_name change it's type to GoStruct
                try:
                    dtype = table.get_struct_obj(dtype.name)
                    tree.dtype.final_type = dtype
                except GoException:
                    pass

                depth = 0
                cur_size = 0

                for child in tree.value:
                    if isinstance(child, GoKeyedElement):
                        child.use = "array"
                        elem_dtype, elem_code = symbol_table(
                            child,
                            table,
                            name,
                            block_type,
                            store_var=store_var + "--[{}]--".format(elem_num),
                            scope_label=scope_label,
                        )
                        ir_code += elem_code
                        elem_num += 1

                        if depth == 0:
                            depth = child.depth
                        elif depth != child.depth:
                            raise GoException("Error: Wrong array declaration")
                        element_type = child.dtype
                        tree.dtype.size += child.size
                        logging.info(
                            "final array type {}".format(element_type)
                        )

                        if cur_size == 0:
                            cur_size = child.size
                        elif cur_size != child.size:
                            raise GoException(
                                "Error: Incorrect number of elements in array"
                            )

                    # print(dtype,element_type)
                    table.type_check(
                        dtype, element_type, "array initialization"
                    )

                if not isinstance(tree.dtype.dtype, GoArray):
                    tree.dtype.dtype = tree.dtype.final_type
                # if isinstance(tree.dtype.dtype,GoArray):
                #     print(tree.dtype.dtype.dtype.name)
                DTYPE = tree.dtype
                # print(DTYPE.final_type)
                # print(tree.dtype,tree.dtype.final_type)

                if depth != tree.dtype.depth:
                    raise GoException("Error: Wrong array declaration")

                tree_value = tree.value
                tree_type = tree.dtype
                logging.info("START")
                while isinstance(tree_type, GoArray):
                    if (
                        tree_type.length != "variable"
                        and tree_type.length.item != len(tree_value)
                    ):
                        raise GoException(
                            "Error: Array declaration of incorrect size"
                        )

                    elif tree_type.length == "variable":
                        tree_type.length = GoBasicLit(
                            len(tree_value), GoType("int", True)
                        )
                    tree_type = tree_type.dtype
                    tree_value = tree_value[0].element

            elif isinstance(tree.dtype, GoType) or isinstance(
                tree.dtype, GoStruct
            ):  # handles structs
                if isinstance(tree.dtype, GoType):
                    struct_name = tree.dtype.name
                    logging.info("Struct name {}".format(struct_name))
                    struct_obj = table.get_struct_obj(struct_name)
                else:
                    struct_name = "__inline_struct_{}".format(
                        table.inline_count
                    )
                    table.inline_count += 1
                    struct_obj = tree.dtype
                    # print(struct_obj.vars)

                field_list = tree.value
                type_list = []
                type_dict = {}
                unnamed_keys = True
                for i, field in enumerate(field_list):
                    field.use = "struct"
                    if field.key is not None:
                        unnamed_keys = False
                        field_name = store_var + "[{}]".format(
                            table.field2index(struct_obj, field.key)
                        )
                    elif not unnamed_keys:
                        raise GoException(
                            "Error: Cannot mix named and unnamed keys"
                        )
                    else:
                        field_name = store_var + "[{}]".format(
                            table.position2index(struct_obj, i)
                        )

                    field_type, elem_code = symbol_table(
                        field,
                        table,
                        name,
                        block_type,
                        store_var=field_name,
                        scope_label=scope_label,
                    )
                    type_list.append(field_type)
                    if field.key is not None:
                        type_dict[field.key] = field_type
                    ir_code += elem_code

                logging.info("FINAL LIST '{}'".format(type_list))
                # struct_obj = GoStruct([])
                if isinstance(tree.dtype, GoType):
                    if unnamed_keys:
                        table.check_struct(struct_name, type_list)
                    else:
                        table.check_inline_struct(struct_obj, type_dict)
                else:
                    table.check_inline_struct(struct_obj, type_dict)

                struct_obj.size = table.get_size(tree)
                struct_obj.name = struct_name
                if struct_name.startswith("__inline_struct"):
                    table.insert_struct(struct_name, struct_obj)

                DTYPE = struct_obj

        elif isinstance(tree, GoUnaryExpr):
            opd_name = "__opd_{}".format(inter_count)
            opd_dtype, opd_code = symbol_table(
                tree.expr,
                table,
                name,
                block_type,
                store_var=opd_name,
                scope_label=scope_label,
            )
            ir_code += opd_code
            table.insert_var(opd_name, opd_dtype, use="intermediate")
            ir_code += "{} = {}{}\n".format(store_var, tree.op, opd_name)

            if tree.op == "&" or tree.op == "*":
                if tree.op == "&":
                    tree.dtype = GoPointType(opd_dtype)
                elif hasattr(opd_dtype, "dtype"):  # tree.op == "*"
                    tree.dtype = opd_dtype.dtype
                else:  # Not a pointer/array type
                    raise GoException(
                        'Error: "{}" not pointer type'.format(opd_dtype)
                    )

                if (
                    isinstance(tree.expr, GoUnaryExpr)
                    and tree.op == "&"
                    and tree.expr.op == "&"
                ):
                    raise GoException("Error: Cannot take address of address")

                elif isinstance(tree.expr, GoCompositeLit) and tree.op == "*":
                    raise GoException("Cannot dereference composite literals")

            # TODO: need to add better type checking
            else:
                tree.dtype = opd_dtype

            DTYPE = tree.dtype

        elif isinstance(tree, GoLabelCtrl):
            if scope_label == "":
                raise GoException(
                    "Error: {} not valid in this scope".format(tree.keyword)
                )
            elif tree.keyword == "continue" and scope_label == "Switch":
                raise GoException(
                    'Error: "continue" not valid in a "switch" scope'
                )

            if tree.keyword == "continue":
                ir_code = "goto {}\n".format(scope_label.split("|")[-1])
            else:
                ir_code = "goto {}\n".format(scope_label.split("|")[0])

        elif isinstance(tree, GoReturn):
            if block_type == "function":
                results = table.get_func(name, "result")[0]
            elif block_type == "method":
                key = (name[0], name[1].dtype.name)
                results = table.get_method(key, "result")
            else:
                raise GoException(
                    "Error: Return statement not inside any function or method"
                )

            if len(results) != len(tree.expr_list):
                raise GoException(
                    'Error: No. of values returned is "{}"; should be "{}"'.format(
                        len(tree.expr_list), len(results)
                    )
                )

            return_name = "__retval_{}".format(inter_count)
            if len(results) > 1:
                field_list = [
                    GoStructField(["__val{}".format(i)], results[i].dtype, "")
                    for i in range(len(results))
                ]
                return_struct = GoStruct(field_list)
                table.insert_var(
                    return_name, return_struct, use="intermediate"
                )
            elif len(results) == 1:
                table.insert_var(
                    return_name, results[0].dtype, use="intermediate"
                )

            return_index = 0
            for i, (res, expr) in enumerate(zip(results, tree.expr_list)):
                if len(results) > 1:
                    return_name_i = return_name + "[{}]".format(return_index)
                else:
                    return_name_i = return_name
                expr_dtype, expr_code = symbol_table(
                    expr,
                    table,
                    name=name,
                    block_type=block_type,
                    store_var=return_name_i,
                    scope_label=scope_label,
                )
                ir_code += expr_code
                return_index += table.get_size(expr_dtype)
                table.type_check(res.dtype, expr_dtype, use="return")

            if len(results) == 0:
                ir_code += "return \n"
            else:
                ir_code += "return {}\n".format(return_name)

    except GoException as go_exp:
        if not hasattr(tree, "lineno"):
            raise GoException(go_exp)  # Will be handled by the caller
        go_traceback(tree)
        print(go_exp)
        exit(1)

    return DTYPE, ir_code


def process_code(input_path):
    """Generate the symbol table and the 3AC for the input file path.

    Args:
        input_path (str): The path to the input file

    Returns:
        SymbTable, str: The symbol table and the 3AC code for the input

    """
    with open(input_path, "r") as go:
        input_text = go.read()
    if input_text[-1] != "\n":
        input_text += "\n"

    # Reset the lexer to line no. 1
    lexer.lineno = 1
    # Storing filename and input text for error reporting
    lexer.filename = input_path
    lexer.lines = input_text.split("\n")

    if hasattr(parser, "statestack"):
        # Parser was used earlier
        parser.restart()
    tree = parser.parse(input_text)

    table = SymbTable()
    ir_code = symbol_table(tree, table, prefix=input_text.split(".")[0])[1]
    return table, ir_code


def resolve_dtype(dtype):
    s = ""
    if isinstance(dtype, GoType):
        s = dtype.name
    elif isinstance(dtype, GoStruct):
        s = "struct_{}".format(dtype.name)
    elif isinstance(dtype, GoArray):
        s = "array_{}".format(resolve_dtype(dtype.dtype))
    elif isinstance(dtype, GoPointType):
        while isinstance(dtype, GoPointType):
            dtype = dtype.dtype
            s = s + "*"
        s = s + resolve_dtype(dtype)
    return s


#  Interfaces
def csv_writer(table, name, dir_name, activation=False):
    if dir_name[-1] != "/":
        dir_name += "/"

    file = open(dir_name + "{}.csv".format(name), "w")
    writer = csv.writer(
        file,
        delimiter=",",
        quoting=csv.QUOTE_NONE,
        quotechar="",
        escapechar='"',
    )

    for kind in ["variables", "intermediates", "constants"]:
        if kind != "variables":
            writer.writerow([])
        writer.writerow(["#" + kind.upper()])
        writer.writerow(["name", "type", "size", "offset"])
        var_rows = []
        for var in getattr(table, kind):
            dtype = getattr(table, kind)[var]
            row = None
            if isinstance(dtype, GoType):
                row = [var, resolve_dtype(dtype), dtype.size, dtype.offset]
            elif isinstance(dtype, GoStruct):
                row = [var, resolve_dtype(dtype), dtype.size, dtype.offset]
            elif isinstance(dtype, GoArray):
                row = [var, resolve_dtype(dtype), dtype.size, dtype.offset]
            elif isinstance(dtype, GoPointType):
                row = [var, resolve_dtype(dtype), dtype.size, dtype.offset]
            if row is not None:
                var_rows.append(row)

        var_rows = sorted(var_rows, key=lambda x: x[3])
        for row in var_rows:
            writer.writerow(row)

    writer.writerow([])
    writer.writerow(["#SCOPES"])
    writer.writerow(["scope_no", "symbol_table"])
    count = 0
    for scope in table.scopes:
        row = ["scope_{}".format(count), "{}_scope_{}.csv".format(name, count)]
        csv_writer(scope, "{}_scope_{}".format(name, count), dir_name)
        writer.writerow(row)
        count += 1

    if activation:
        writer.writerow([])
        writer.writerow(["#ACTIVATION RECORD"])
        for item in table.activation_record:
            writer.writerow([item[0], item[1].activation_offset])

    if name == "global":
        writer.writerow([])
        writer.writerow(["#PACKAGES"])
        for package in table.imports:
            writer.writerow([package])

        writer.writerow([])
        writer.writerow(["#ALIASES"])
        writer.writerow(["alias", "actual"])

        for alias in table.aliases:
            row = [alias, table.aliases[alias].name]
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(["#BUILTINS"])
        writer.writerow(["name", "size"])

        for builtin in table.basic_types:
            row = [builtin, table.basic_types[builtin]["size"]]
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(["#FUNCTIONS"])
        writer.writerow(
            ["name", "[ParamName_type]", "symbol_table", "[ReturnType]"]
        )

        for func in table.functions:
            row = [func]
            params = table.functions[func]["params"]
            param_string = ""
            for param in params[:-1]:
                param_string += "{}_{};".format(
                    param.name, resolve_dtype(param.dtype)
                )
            if len(params) > 0:
                last = params[len(params) - 1]
                param_string += "{}_{}".format(
                    last.name, resolve_dtype(last.dtype)
                )

            row.append(param_string)
            row.append("{}.csv".format(func))
            csv_writer(
                table.functions[func]["body"], func, dir_name, activation=True
            )
            results = table.functions[func]["result"]
            result_string = ""
            if results is not None:
                for result in results[:-1]:
                    result_string += "{};".format(resolve_dtype(result.dtype))
                if len(results) > 0:
                    result_string += "{}".format(
                        resolve_dtype(results[len(results) - 1].dtype)
                    )
            row.append(result_string)
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(["#METHODS"])
        writer.writerow(
            [
                "name",
                "reciever",
                "[ParamName_type]",
                "symbol_table",
                "[ReturnType]",
            ]
        )
        for method in table.methods:
            row = ["{}_{}".format(method[0], method[1])]
            params = table.methods[method]["params"]
            param_string = ";".join(
                [
                    "{}_{}".format(param.name, resolve_dtype(param.dtype))
                    for param in params
                ]
            )

            row.append(param_string)
            row.append("{}_{}.csv".format(method[0], method[1]))
            csv_writer(
                table.methods[method]["body"],
                "{}_{}".format(method[0], method[1]),
                dir_name,
                activation=True,
            )
            results = table.methods[method]["result"]
            result_string = ""
            if results is not None:
                for result in results[:-1]:
                    result_string += "{};".format(resolve_dtype(result.dtype))
                if len(results) > 0:
                    result_string += "{}".format(
                        resolve_dtype(results[len(results) - 1].dtype)
                    )
            row.append(result_string)
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(["#STRUCTURES"])
        writer.writerow(["struct name", "[VarName_dtype_tag]"])
        for struct_name in table.structures:
            struct = table.structures[struct_name]
            row = [struct_name]
            var = struct.vars
            tags = struct.tags
            string = ""
            for item1, item2 in zip(var[:-1], tags[:-1]):
                string += "{}_{}_{};".format(
                    item1[0], resolve_dtype(item1[1].dtype), item2[1]
                )
            if len(var) > 0:
                item1 = var[len(var) - 1]
                item2 = tags[len(tags) - 1]
                string += "{}_{}_{}".format(
                    item1[0], resolve_dtype(item1[1].dtype), item2[1]
                )
            row.append(string)
            writer.writerow(row)

    file.close()


def get_csv(table, dir_name):
    """Generate required CSV and TXT files."""
    if dir_name[-1] != "/":
        dir_name += "/"

    subprocess.run(["rm", "-rf", dir_name])
    os.mkdir(dir_name)
    csv_writer(table, "global", dir_name)

    for csv_file in os.listdir("."):
        if len(csv_file.split(".")) == 2 and csv_file.split(".")[1] == "csv":
            with open(dir_name + csv_file + ".temp", "w+") as out_file:
                subprocess.call(
                    ["awk", '{gsub(/"/,"")};1', csv_file], stdout=out_file
                )
            subprocess.run(["mv", out_file, csv_file])


if __name__ == "__main__":
    argparser = ArgumentParser(description="IR generator for Go")
    argparser.add_argument("input", type=str, help="input file")
    argparser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="output directory name for csv and txt files",
    )
    argparser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug output"
    )
    args = argparser.parse_args()
    if args.output is None:
        # Output directory name is source filename (w/o extension)
        args.output = ".".join(args.input.split("/")[-1].split(".")[:-1])
    if args.output[-1] != "/":
        args.output += "/"

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    table, ir_code = process_code(args.input)
    get_csv(table, args.output)
    with open(args.output + "3ac.txt", "w") as ir_file:
        ir_file.write(ir_code)
