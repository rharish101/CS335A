#!/usr/bin/env python3
"""IR generation for Go."""
from lexer import lexer, go_traceback
from parser import parser
from go_classes import *
from argparse import ArgumentParser

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

    def __init__(self, parent=None):
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
        self.types = []
        self.used = set()
        self.constants = {}
        self.imports = {}
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
        elif self.parent:
            return self.parent.get_type(name)
        else:
            print("Error: Attempt to use '{}': undeclared variable/array name ".format(name)) 
            exit()   
    def get_func(self,name,info):
        if name in self.functions:
            return self.functions[name][info]
        elif self.parent:
            return self.parent.get_func(name,info)
        else:
            print("Error: Attempt to use '{}': undeclared function".format(name))        


    def insert_var(self, name, dtype):
        if name not in self.used:
            self.variables[name] = dtype
            self.used.add(name)
        else:
            print("Error: Already declared variable name '{}'".format(name))
            exit()

    def insert_alias(self, alias, actual):
        if alias not in self.used:
            self.types[alias] = actual
            self.used.add(alias)
        else:
            print("Error: Already used alias/typedef name '{}'".format(name))
            exit()

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


    # XXX INCOMPLETE need to check for other type classes
    def type_check(self, dtype1, dtype2, use="",func_name = None, param_name=None):
        if dtype1.__class__ is not dtype2.__class__:
            print("Error: Operands in '{}' of different type classes '{}' and '{}'".format(use, dtype1.__class__,dtype2.__class__))
            exit()

        if isinstance(dtype1,GoType) and isinstance(dtype1,GoType):
            name1 = dtype1.name
            name2 = dtype2.name    
            for name in [name1,name2]:
                if name not in INT_TYPES and name not in ["float","float32","float64","complex","byte","complex64","complex128","string","unintptr"]:
                    print("Error:'{}' is unregistered dtype".format(name))
                    exit() 
            if dtype1.basic_lit or dtype2.basic_lit:
                if name1 in INT_TYPES:
                    name1 = "int"        
                elif name1 in ["float32","float64","float"]:
                    name1 = "float"  
                elif name1 in ["complex64","complex128","complex"]:
                    name1 = "complex"      

                if name2 in INT_TYPES:
                    name2 = "int"        
                elif name2 in ["float32","float64","float"]:
                    name2 = "float"   
                elif name2 in ["complex64","complex128","complex"]:
                    name2 = "complex"       

                       
            if name1 != name2:
                # print("'{}', '{}'".format(name1,name2))
                if use == 'function call':
                    print("Error: Mismatch type of param '{}' in function call of '{}'".format(param_name,func_name))
                else:    
                    print("Error: Operands in '{}' of different types'{}' and '{}'".format(use,name1,name2))
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
        # Indexing by name and 1st receiver
        key = (name, receiver[0])
        if key not in table.methods:
            # Only handling single receiver
            table.methods[key] = {}
            table.methods[key]["params"] = params
            table.methods[key]["result"] = result
        else:
            print("Error: already used method name")
            exit()

    def eval_type(self,expr):
        dtype = None
        if isinstance(expr, GoPrimaryExpr): 
            print("primary expr '{}'".format(expr))
            lhs = expr.lhs
            rhs = expr.rhs
            
            if isinstance(rhs,GoIndex):
                #handles multi dimensional ararys
                # symbol_table(expr,self)
                left = expr
                while isinstance(left.lhs,GoPrimaryExpr):
                    left = left.lhs  
                dtype = self.get_type(left.lhs).dtype 

            #XXX nested function calls with inner function having only one parameter are not working      
            elif isinstance(rhs,GoArguments): #fuction call
                print("FUNCTION CALL '{}', ARGUMENTS '{}'".format(lhs,rhs))
                func_name = lhs
                assert isinstance(rhs,GoArguments)
                #type checking of arguments passed to function
                argument_list = rhs.expr_list
                params_list = self.get_func(func_name,'params')
                print("ARGUMENT LIST: '{}'".format(argument_list))
                if len(argument_list) is not len(params_list):
                    print("Error: '{}' parameters passed to function '{}' instead of '{}'".format(len(argument_list),func_name,len(params_list)))
                    exit()
                for argument,param in zip(argument_list,params_list):
                    assert isinstance(param,GoParam)
                    # symbol_table(param,self)
                    symbol_table(argument,self)
                    actual_dtype = param.dtype
                    given_dtype = self.eval_type(argument)
                    self.type_check(actual_dtype,given_dtype,'function call',func_name, param.name)

                result = self.get_func(func_name,'result')
                assert isinstance(result,GoParam)
                result_type = result.dtype

                if type(result_type) is list:
                    print("Warning: Returning list of types")
                dtype  = result_type

            # handles selector operations on struct, returns the dtypes     
            elif isinstance(rhs,GoSelector):
                pass
                

        elif type(expr) is str:  # variable
            dtype = self.get_type(expr)
        elif isinstance(expr, GoExpression):
            symbol_table(expr, self)
            print(expr.dtype)
            dtype = expr.dtype
        elif isinstance(expr, GoBasicLit):
            dtype = expr.dtype
            assert isinstance(dtype,GoType)         

        
        elif isinstance(expr,GoUnaryExpr):
            if expr.op == "&":
                symbol_table(expr,self)
                dtype = expr.dtype

        if dtype is None:
            print("Warning: getting None dtype")      
        return dtype    




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
    error = False
    print(tree)
    # TODO: Store modules
    if isinstance(tree, GoSourceFile):
        # iterating over package imports
        for item in tree.imports:
            table.imports[item.import_as] = item
        # iteraing over TopLevelDeclList
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
        symbol_table(body, table, (name, receiver[0]), "method")

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
            # print("var dtype {}".format(dtype.name))
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
                    # if type(expr) is str:
                    #     eval_type = table.get_type(expr)
                    # elif isinstance(expr, GoBasicLit):
                    #     eval_type = expr.dtype
                    # elif isinstance(expr, GoExpression):
                    #     symbol_table(expr, table)
                    #     eval_type = expr.dtype

                    evaluated_types.append(table.eval_type(expr))
                if len(rhs) != 0:
                    if dtype is None:
                        for var, eval_type in zip(lhs, evaluated_types):
                            table.insert_var(var, eval_type)
                    else:
                        for var, eval_type in zip(lhs, evaluated_types):
                            # If defined type is not None then check if the
                            # evaluated type is same as the defined type
                            table.type_check(dtype, eval_type, "variable declaration")
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
                    # if type(expr) is str:
                    #     eval_type = table.get_type(expr)
                    # elif isinstance(expr, GoBasicLit):
                    #     eval_type = expr.dtype
                    # elif isinstance(expr, GoExpression):
                    #     symbol_table(expr, table)
                    #     eval_type = expr.dtype
                    evaluated_types.append(table.eval_type(expr))

                if dtype is None:
                    for const, eval_type in (expr_list, evaluated_types):
                        table.insert_const(const, eval_type)
                else:
                    for const, eval_type in zip(id_list, evaluated_types):
                        table.type_check(dtype, eval_type,"const declaration")
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
            elif isinstance(var, GoExpression):
                error = True
                print("Expression '{}' cannot be assigned value".format(var))
                exit()
            elif not table.lookup(var):
                error = True
                print('"{}" not declared before use'.format(var))
                exit()

        for var, expr in zip(lhs, rhs):
            print('assign: "{}" : "{}"'.format(var, expr))
            #can have only struct fields, variables, array on the LHS.
            if isinstance(var, GoPrimaryExpr):
                #print(table.get_type(var.lhs))
                #dtype1 = table.get_type(var.lhs).dtype
                left = var
                while isinstance(left.lhs,GoPrimaryExpr):
                    left = left.lhs
                dtype1 = table.get_type(left.lhs).dtype

            elif type(var) is str:
                dtype1 = table.get_type(var)


            # if type(expr) is str:
            #     dtype2 = table.get_type(expr)
            # elif isinstance(expr, GoBasicLit):
            #     dtype2 = expr.dtype
            # elif isinstance(expr, GoExpression):
            #     symbol_table(expr, table)
            #     dtype2 = expr.dtype

            dtype2 = table.eval_type(expr)

            table.type_check(dtype1, dtype2,"assignment")

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

            elif isinstance(expr, GoUnaryExpr):
                symbol_table(expr, table)
                if expr.op == "&":
                    table.insert_var(var,expr.dtype)
                    print("type = '{}' , {}'".format(var, expr.dtype))


    elif isinstance(tree, GoExpression):
        lhs = tree.lhs
        op = tree.op
        rhs = tree.rhs
        # symbol_table(lhs, table)
        # symbol_table(rhs, table)
        print('exp: lhs "{}", rhs "{}"'.format(lhs, rhs))

        # XXX INCOMPLETE : need to handle cases for array types, struct types,
        # interfaces, function, pointer
        # if type(lhs) is str:  # variable
        #     dtype1 = table.get_type(lhs)
        # elif isinstance(lhs, GoExpression):
        #     dtype1 = lhs.dtype
        # elif isinstance(lhs, GoBasicLit):
        #     dtype1 = lhs.dtype

        # if type(rhs) is str:  # variable
        #     dtype2 = table.get_type(rhs)
        # elif isinstance(rhs, GoExpression):
        #     dtype2 = rhs.dtype
        # elif isinstance(rhs, GoBasicLit):
        #     dtype2 = rhs.dtype

        dtype1 = table.eval_type(lhs)
        dtype2 = table.eval_type(rhs)

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
        
            table.type_check(dtype1,dtype2,"expression")
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
                print('basic_lit "{}", "{}", "{}"'.format(dtype1, dtype2, dtype1.basic_lit & dtype2.basic_lit))
                if op in [">", "<", ">=", "<=", "==", "!="]:
                    tree.dtype = GoType("bool",dtype1.basic_lit & dtype2.basic_lit)
                else:
                    tree.dtype = GoType(name,dtype1.basic_lit & dtype2.basic_lit)


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
        print("Entered GoFor")
        symbol_table(tree.clause, table)
        symbol_table(tree.infor, table)

    elif isinstance(tree, GoForClause):
        print("Entered GoForClause")
        
        if (tree.init is not None) and not isinstance(tree.init, GoShortDecl) and not isinstance(tree.init, GoAssign):
            error = True
            print("Error in for loop Initialization")
            exit()

        elif (tree.expr is not None) and not isinstance(tree.expr, GoBasicLit) and not isinstance(tree.expr, GoExpression):
            error = True
            print("Error in for loop Condition")
            exit()

        elif (tree.post is not None) and not isinstance(tree.post, GoAssign):
            error = True
            print("Error in for loop post expression")
            exit()

        symbol_table(tree.init, table)
        symbol_table(tree.expr, table)
        symbol_table(tree.post, table)

        
        if (tree.expr is not None) and tree.expr.dtype.name is not "bool":
            error = True
            print("loop Condition must be bool type")
            exit()

    elif isinstance(tree, GoRange):
        pass

    elif isinstance(tree, GoArray):
        symbol_table(tree.length, table)
        symbol_table(tree.dtype, table)
        if isinstance(tree.dtype,GoArray):
            tree.depth = tree.dtype.depth + 1
            tree.dtype = tree.dtype.dtype
        
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
        # if type(index) is str:  # variable
        #     dtype = table.get_type(index)
        # elif isinstance(index, GoExpression):
        #     dtype = index.dtype
        # elif isinstance(index, GoBasicLit):
        #     dtype = index.dtype

        # if dtype.name != "int":
        #     print("array index must be an integer")
        #     exit()
        dtype = table.eval_type(index)
        if isinstance(dtype,GoType):
            name = dtype.name
            if name not in INT_TYPES:
                print("Error: index of array is not integer")
                exit()

        

    elif isinstance(tree, GoPrimaryExpr):
        rhs = tree.rhs
        lhs = tree.lhs    
        if isinstance(rhs, GoIndex): #array indexing 
            print("array = '{}'".format(lhs))
            if isinstance(lhs,GoPrimaryExpr):
                lhs.depth = tree.depth + 1
            else:
                if not table.lookup(lhs):
                    error = True
                    print("'{}' array not declared".format(lhs))
                    exit()
                elif not isinstance(table.get_type(lhs), GoArray):
                    error = True
                    print("'{}' not array".format(table.get_type(lhs)))
                    exit()
                elif tree.depth != table.get_type(lhs).depth:
                    error = True
                    print("Incorect number of indexes in array '{}'".format(lhs));
                    exit()

                print("dtype: '{}'".format(table.get_type(lhs)))
                tree.dtype = (table.get_type(lhs)).dtype
                print("dtype: '{}'".format(table.get_type(lhs)))
        
        #XXX the symbol_table function should be called for all cases as lhs/ rhs may be of expression type    
            symbol_table(lhs, table)
            symbol_table(rhs, table)
        # symbol_table(lhs, table)
        # symbol_table(rhs, table)    
        
        elif isinstance(rhs,GoArguments): #fuction call
            print("FUNCTION CALL '{}'".format(lhs))
            func_name = lhs
            assert isinstance(rhs,GoArguments)
            #type checking of arguments passed to function
            argument_list = rhs.expr_list
            params_list = table.get_func(func_name,'params')
            if len(argument_list) is not len(params_list):
                print("Error: '{}' parameters passed to function '{}' instead of '{}'".format(len(argument_list),func_name,len(params_list)))
                exit()
            for argument,param in zip(argument_list,params_list):
                assert isinstance(param,GoParam)
                # symbol_table(param,table)
                symbol_table(argument,table)
                actual_dtype = param.dtype
                given_dtype = table.eval_type(argument)
                table.type_check(actual_dtype,given_dtype,'function call',func_name, param.name)

        # no requirement to check result dtype in case of isolated function call        
        #     result = table.get_func(func_name,'result')
        #     assert isinstance(result,GoParam)
        #     result_type = result.dtype

        #     if type(result_type) is list:
        #         print("Warning: Returning list of types")
        #     tree.dtype  = result_type    


    # XXX To be done later : check number of elements in array same as that
    # specified

    elif isinstance(tree, GoKeyedElement):
        print("Entered GoKeyedElement")
        #symbol_table(tree.element, table)
        if isinstance(tree.element,GoBasicLit) or isinstance(tree.element,GoExpression):
            symbol_table(tree.element, table)
            element_type = tree.element.dtype
            print(element_type)
        elif type(tree.element) is str:
            symbol_table(tree.element, table)
            element_type = table.get_type(tree.element)
        else:
            depth = 0
            for child in tree.element:
                if isinstance(child,GoKeyedElement):
                    symbol_table(child,table)
                    if depth == 0:
                        depth = child.depth
                    elif depth != child.depth:
                        error = True
                        print("Wrong array declaration")
                        exit(0)
                    print(child.dtype)
                    element_type = child.dtype
                
                if tree.dtype is None:
                    tree.dtype = element_type
                elif tree.dtype.name != element_type.name:
                    print(tree.dtype.name)
                    print(element_type.name)
                    error = True
                    print(
                            "Conflicting1 types in array, '{}', '{}'".format(
                                tree.dtype.name, element_type.name
                            )
                        )
                    exit()
            tree.depth = depth + 1
        tree.dtype = element_type
        print(tree.dtype.name)


    elif isinstance(tree, GoCompositeLit):
        print("Entered GoCompositeLit")
        symbol_table(tree.dtype, table)
        #symbol_table(tree.value, table)

        if isinstance(tree.dtype, GoArray):
            dtype = tree.dtype.dtype
            depth = 0
            print("dtype = '{}'".format(dtype.name))
            for child in tree.value:
                if isinstance(child,GoKeyedElement):
                    symbol_table(child,table)
                    if depth == 0:
                        depth = child.depth
                    elif depth != child.depth:
                        error = True
                        print("Error: Wrong array declaration")
                        exit()
                    element_type = child.dtype
                    print(element_type)
                
                # if dtype.name != element_type.name:
                #     print(
                #         "Conflicting types in array, '{}', '{}'".format(
                #             dtype.name, element_type.name
                #         )
                #     )
                #     exit()
                table.type_check(element_type,dtype,"array initialization")

            if depth != tree.dtype.depth:
                error = True
                print("Error: Wrong array declaration")
                exit()

    elif isinstance(tree,GoUnaryExpr):
        symbol_table(tree.expr,table)
        
        if type(tree.expr) is str:
            if tree.op == "&":
                tree.dtype = GoPointType(table.get_type(tree.expr))



table = SymbTable()
symbol_table(tree, table)
