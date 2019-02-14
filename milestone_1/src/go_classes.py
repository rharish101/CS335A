"""Contains classes used by the parser (and possibly the semantic analyser)."""
# =============================================================================
# TYPES
# =============================================================================


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
        self.dtype = dtype


class GoStruct(GoType):
    def __init__(self, fields):
        super().__init__("struct")
        self.field = fields


class GoStructField:
    def __init__(self, var_list, dtype, tag):
        self.vars = var_list
        self.dtype = dtype
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


# =============================================================================
# BLOCKS
# =============================================================================


class GoBlock:
    def __init__(self, statements):
        self.statements = statements


# =============================================================================
# DECLARATIONS AND SCOPE
# =============================================================================


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


# =============================================================================
# EXPRESSIONS
# =============================================================================


class GoBaseExpr:
    def __init__(self, kind):
        self.kind = kind


class GoPrimaryExpr(GoBaseExpr):
    def __init__(self, lhs, rhs):
        super().__init__("primary")
        self.lhs = lhs
        self.rhs = rhs


class GoSelector:
    def __init__(self, child):
        self.child = child


class GoIndex:
    def __init__(self, index):
        self.index = index


class GoArguments:
    def __init__(self, expr_list, dtype=None):
        self.expr_list = expr_list
        self.dtype = dtype  # dtype can be None


class GoExpression(GoBaseExpr):
    def __init__(self, lhs, rhs, op):
        super().__init__("expression")
        self.lhs = lhs
        self.rhs = rhs
        self.op = op


class GoUnaryExpr(GoBaseExpr):
    def __init__(self, expr, op):
        super().__init__("unary")
        self.expr = expr
        self.op = op


# =============================================================================
# STATEMENTS
# =============================================================================


class GoAssign:
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op  # op can be None, indicating a simple assignment


class GoIf:
    def __init__(self, stmt, cond, inif, inelse):
        self.stmt = stmt  # stmt can be None, indicating no statement
        self.cond = cond
        self.inif = inif
        self.inelse = inelse


class GoSwitch:
    def __init__(self, stmt, cond, case_list):
        self.stmt = stmt  # stmt can be None, indicating no statement
        self.cond = cond
        self.case_list = case_list


class GoCaseClause:
    def __init__(self, kind, expr_list, stmt_list):
        self.kind = kind  # stmt can be None, indicating no statement
        self.expr_list = expr_list
        self.stmt_list = stmt_list


class GoFor:
    def __init__(self, clause, infor):
        self.clause = clause
        self.infor = infor


class GoBaseForCl:
    def __init__(self, kind):
        self.kind = kind


class GoForClause(GoBaseForCl):
    def __init__(self, init, expr, post):
        super().__init__("standard")
        self.init = init  # init can be None, indicating no statement
        self.expr = expr  # expr can be None, indicating no statement
        self.post = post  # post can be None, indicating no statement


class GoRange(GoBaseForCl):
    def __init__(self, lhs, rhs):
        super().__init__("range")
        self.lhs = lhs
        self.rhs = rhs


# Class for Return, Break, Continue and Goto statements
class GoControl:
    def __init__(self, kind):
        self.kind = kind


class GoReturn(GoControl):
    def __init__(self, expr_list):
        super().__init__("return")
        self.expr_list = expr_list


class GoLabelCtrl(GoControl):
    def __init__(self, keyword, label):
        super().__init__("label")
        self.keyword = keyword
        self.label = label


# =============================================================================
# PACKAGES
# =============================================================================


class GoSourceFile:
    def __init__(self, package, imports, declarations):
        self.package = package
        self.imports = imports
        self.declarations = declarations


class GoImportSpec:
    def __init__(self, package, import_as=None):
        self.package = package
        self.import_as = import_as
