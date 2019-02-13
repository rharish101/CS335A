class GoType:
    def __init__(self, kind):
        self.kind = kind


class GoInbuiltType(GoType):
    def __init__(self, name):
        super().__init__("inbuilt")
        self.name = name


class GoFromModule:
    def __init__(self, parent, child):
        self.parent = parent
        self.child = child


class GoArray(GoType):
    def __init__(self, length, dtype):
        super().__init__("array")
        self.length = length
        self.type = dtype


class GoStruct(GoType):
    def __init__(self, fields):
        super().__init__("struct")
        self.field = fields


class GoStructField:
    def __init__(self, var_list, dtype, tag):
        self.vars = var_list
        self.type = dtype
        self.tag = tag


class GoDeref:
    def __init__(self, var):
        self.var = var


class GoVar:
    def __init__(self, name):
        self.name = name


class GoPointType(GoType):
    def __init__(self, dtype):
        super().__init__("pointer")
        self.dtype = dtype


class GoFuncType(GoType):
    def __init__(self, params, result=None):
        super().__init__("function")
        self.params = params
        self.result = result


class GoInterfaceType(GoType):
    def __init__(self, methods):
        super().__init__("function")
        self.methods = methods


class GoParam:
    def __init__(self, name=None, dtype=None):
        self.name = name
        self.dtype = name


class GoMethodFunc:
    def __init__(self, name, params, result=None):
        self.name = name
        self.params = params
        self.result = result


class GoBlock:
    def __init__(self, statements):
        self.statements = statements


class GoDecl:
    def __init__(self, kind, declarations):
        self.kind = kind
        self.declarations = declarations


class GoConstSpec:
    def __init__(self, id_list, dtype=None, expr=None):
        self.id_list = id_list
        self.dtype = dtype
        self.expr = expr


class GoTypeDefAlias:
    def __init__(self, kind, alias, actual):
        self.kind = kind
        self.alias = alias
        self.actual = actual


class GoVarSpec:
    def __init__(self, lhs, dtype, rhs):
        self.lhs = lhs
        self.dtype = dtype
        self.rhs = rhs


class GoShortDecl(GoDecl):
    def __init__(self, id_list, expr_list):
        super().__init__("short", [])
        self.id_list = id_list
        self.expr_list = expr_list


class GoFuncDecl(GoDecl):
    def __init__(self, name, params, result, body):
        super().__init__("function", [])
        self.name = name
        self.params = params
        self.result = result
        self.body = body


class GoMethDecl(GoDecl):
    def __init__(self, receiver, name, params, result, body):
        super().__init__("function", [])
        self.receiver = receiver
        self.name = name
        self.params = params
        self.result = result
        self.body = body


class GoSourceFile:
    def __init__(self, package, imports, declarations):
        self.package = package
        self.imports = imports
        self.declarations = declarations


class GoImportSpec:
    def __init__(self, package, import_as=None):
        self.package = package
        self.import_as = import_as

class GoFunc:
    def __init__(self, key, func):
        self.key = key
        self.func = func

class GoPrimaryExpr:
    def __init__(self, primary_exp, index):
        self.primary_exp = primary_exp
        self.index = index

class GoExpression:
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op

class GoIncDec:
    def __init__(self, expr, op):
        self.expr = expr
        self.op = op

class GoAssign:
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op

class GoAddMul:
    def __init__(self, add_op, assign_op):
        self.add_op = add_op
        self.assign_op = assign_op

class GoIf:
    def __init__(self, stmt_cond, inif, inelse):
        self.stmt_cond = stmt_cond
        self.inif = inif
        self.inelse = inelse

# Class for Return, Break, Continue and GoTo statements 
class GoControl:
    def __init__(self, keyword, identifier):
        self.keyword = keyword
        self.identifier = identifier