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
            * Used : Set of used variable/alias/const names 
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
        self.types = {}
        self.used = set()
        self.constants  = {}
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

    def insert_var(self, name, dtype):
        if name not in self.used:
            self.variables[name]=dtype
            self.used.add(name)
        else:
            print("Error: already declared variable name")
            exit()  
    def insert_alias(self,alias,actual):
        if alias not in self.used:
            self.types[alias] = actual
            self.used.add(alias)
        else:
            print("Error: already used alias/typedef name")
            exit()   
    def insert_const(self,const,dtype):
        if const not in self.used:
            self.constants[const] = dtype
            self.used.add(const)
        else:
            print("Error: already used constant name")
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


def symbol_table(tree,table):

    #============================
         #VISHWAS
    #============================

    error = False
    print (tree)
    # UNIMPLEMENTED: package names and modules storing 
    if isinstance(tree,GoSourceFile):
        #iteraing over TopLevelDeclList`
        for item in tree.declarations:
            symbol_table(item,table)

    # method declarations  
    # UN-IMPLEMENTED: paramters and results
    elif isinstance(tree,GoMethDecl):
        reciever = tree.receiver 
        name = tree.name
        params = tree.params
        result = tree.result
        body = tree.body

        #moving into method body
        child_table = SymbTable(table)
        symbol_table(body,child_table)
        table.scopes.append(child_table)

        #iterating over paramter list
        for item in params:
            # Parameters contains tridot and Type 
            pass
        

         

    #function declarations   
    # UN-IMPLEMENTED: paramters and results 
    elif isinstance(tree,GoFuncDecl):
        name = tree.name
        params = tree.params #holds the parameter list (p_ParameterList)
        result = tree.result
        body = tree.body  #instance of GoBlock

        #moving into function body
        child_table = SymbTable(table)
        symbol_table(body,child_table)
        table.scopes.append(child_table)

        #iterating over paramter list
        for item in params:
            # contains tridot and Type 
            pass
        

    #UNINPLEMETNED:
    #               1. handle none types, in that case assign the type of the expression to the variable 
    #               2. type checking: if the defined type of the variable is not same as the expected type 
    elif isinstance(tree,GoDecl) and tree.kind is "var":
        var_list = tree.declarations
        for item in var_list:
            # assert isinstance(item,GoVarSpec)
            lhs = item.lhs
            dtype = item.dtype
            rhs = item.rhs
            if (len(lhs) is not len(rhs) and len(rhs) is not 0
                or len(rhs) is 0 and dtype is None):
                error = True
            else:
                #iterating over all expressions to evaluate their types
                evaluated_types = []
                for expr in rhs:
                    # print (expr)
                    assert isinstance(expr,GoExpression) or isinstance(expr,GoBasicLit)
                    symbol_table(expr,table)
                    evaluated_types.append(expr.dtype)
                # print('dtype : "{}"'.format(dtype.name))         
                if len(rhs) is not 0: 
                    if dtype is None:
                        for evel_type in evaluated_types:
                            table.insert_var(var,eval_type)
                    else:        
                        for var,eval_type in zip(lhs,evaluated_types):
                            #if defined type is not None then check if the evaluated type is same as the defined type
                            # if eval_type is not dtype:
                            #     error = True
                            #     break
                            print('var "{}":"{}"'.format(var,dtype))
                            table.insert_var(var,dtype)  
                else:
                    for var in lhs:
                        print('var "{}":"{}"'.format(var,dtype))
                        table.insert_var(var,dtype)             
                

    #typedef and aliases   
    #still need to incorporate typedef alias during type checking                
    elif isinstance(tree,GoDecl) and tree.kind is "type":
        type_list = tree.declarations
        #iterating over AliasDecl and Typedef
        for item in type_list:
            # assert isinstance(item,GoTypeDefAlias)
            alias = item.alias
            actual = item.actual
            table.insert_alias(alias,actual)
            print('typedef/alias "{}" : "{}"'.format(alias,actual))
           

    elif isinstance(tree,GoDecl) and tree.kind is "constant":
        const_list = tree.declarations
        for item in const_list:
            # assert isinstance(item,GoConstSpec)
            id_list = item.id_list
            dtype = item.dtype
            expr_list = item.expr
            if len(id_list) is not len(expr_list):
                error = True 
            else:
                evaluated_types = []
                for  expr in expr_list:
                    assert isinstance(expr,GoExpression) or isinstance(expr,GoBasicLit)
                    symbol_table(expr,table)
                    evaluated_types.append(expr.dtype)
                #if defined type is not None then check if the evaluated type is same as the defined type
                #currently each type is a string i.e. "INT", "STRING",...
                if dtype is None:
                    for eval_type in evaluated_types:
                        table.insert_const(const,eval_type)
                else:    
                    for const,eval_type in zip(id_list,evaluated_types):
                        # if eval_type is not dtype:
                        #     error = True
                        #     break
                        print('const "{}":"{}"'.format(const,dtype))

                        table.insert_const(const,dtype)
                        #adding to list of variables so that const can be used as variables except they can't be assigned to some other value. Need to implement this check 
                        #table.insert_var(const,dtype)

        
    elif isinstance(tree,GoBlock):
        statement_list = tree.statements
        child_table = SymbTable(table)
        table.scopes.append(child_table)
        for statement in statement_list:
            if statement is None or statement is "" or (type(statement) is list and len(statement) is 0):
                continue
            symbol_table(statement,child_table) 


    #Vishwas(above code) is storing the variable types as objects and Nohria is storing them as strings,
    # so the code below needs to be changed to resolve this discrepancy.        
    #====================================
            #NOHRIA
    #====================================
    
    elif isinstance(tree,GoAssign):
        if len(tree.lhs) != len(tree.rhs):
            error = True
            print ("error")
            exit()
        for child in tree.lhs:
            if table.lookup(child) == False:
                error = True
                print ("error")
                exit()
        for child in tree.rhs:
            symbol_table(child,table)
        for child1,child2 in zip(tree.lhs,tree.rhs):
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


    elif isinstance(tree,GoShortDecl):
        if len(tree.id_list) != len(tree.expr_list):
            error = True
            print ("error")
            exit()
        for child in tree.id_list:
            if type(child) is not str:
                error = True
                print ("error")
                exit()
        for child in tree.expr_list:
            symbol_table(child,table)
        
        for child1,child2 in zip(tree.id_list,tree.expr_list):
            if type(child2) is not str:
                if table.lookup(child1) == True and table.get_type(child1) != child2.dtype:
                    error = True
                    print ("error")
                    exit()
                else:
                    table.insert_var(child1,child2.dtype)
            else:
                if table.lookup(child1) == True and table.get_type(child1) != table.get_type(child2):
                    error = True
                    print ("error")
                    exit()
                else:
                    table.insert_var(child1,table.get_type(child2))

    elif isinstance(tree,GoExpression):
        symbol_table(tree.lhs,table)
        symbol_table(tree.rhs,table)
        print('exp: lhs "{}", rhs "{}"'.format(tree.lhs,tree.rhs))
        if type(tree.lhs) is not str:
            dtype1 = tree.lhs.dtype
        else:
            dtype1 = table.get_type(tree.lhs)

        if type(tree.rhs) is not str:
            dtype2 = tree.rhs.dtype
        else:
            dtype2 = table.get_type(tree.rhs)

        op = tree.op
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
                tree.dtype = "BOOL"
            else:
                tree.dtype = dtype1

    elif isinstance(tree,GoIf):
        newtable = SymbTable(table)      #  New symbol table needed as stmt is in the scope of both if and else
        symbol_table(tree.stmt,newtable)
        symbol_table(tree.cond,newtable)
        if tree.cond.dtype != "BOOL":
            error = True
            print ("error")
            exit()
        symbol_table(tree.inif,newtable)
        symbol_table(tree.inelse,newtable)

#XXX Issue with grammar when simple statement in switch case, incorrect parse tree bein generated    
    elif isinstance(tree,GoCaseClause):
        symbol_table(tree.kind,table)
        symbol_table(tree.expr_list,table)
        newtable = SymbTable(table)
        symbol_table(tree.stmt_list,newtable)

    elif isinstance(tree,GoBasicLit):
        tree.dtype = type(tree.item)

    elif type(tree) is list:
        for child in tree:
            symbol_table(child,table)

    elif type(tree) is not str and tree is not None:
        for attr in tree.__dict__:
            child = getattr(tree, attr)
            symbol_table(child,table)    


                
table = SymbTable()            
symbol_table(tree,table)     
