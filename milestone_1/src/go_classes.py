"""Contains classes used by the parser (and possibly the semantic analyser)."""
# =============================================================================
# TYPES
# =============================================================================


class GoType:
    """The base class to inherit types from."""

    def __init__(self, kind):
        self.kind = kind


class GoInbuiltType(GoType):
    """For inbuilt types.

    Inbuilt types are:
        uint8, uint16, uint32, uint64
        int8, int16, int32, int64
        float32, float64
        complex64, complex128
        byte (alias for uint8), rune (alias for int32)
        uint, int, uintptr
        string
    """

    def __init__(self, name):
        super().__init__("inbuilt")
        self.name = name


class GoFromModule:
    """For module imports."""

    def __init__(self, parent, child):
        self.parent = parent
        self.child = child


class GoArray(GoType):
    """For array types."""

    def __init__(self, length, dtype):
        super().__init__("array")
        self.length = length
        self.dtype = dtype


class GoStruct(GoType):
    """For struct types."""

    def __init__(self, fields):
        super().__init__("struct")
        self.field = fields


class GoStructField:
    """For a single field in a struct."""

    def __init__(self, var_list, dtype, tag):
        self.vars = var_list
        self.dtype = dtype
        self.tag = tag


class GoDeref:
    """For derefencing a variable using "*"."""

    def __init__(self, var):
        self.var = var


class GoVar:
    """For variables."""

    def __init__(self, name):
        self.name = name


class GoPointType(GoType):
    """For pointer types."""

    def __init__(self, dtype):
        super().__init__("pointer")
        self.dtype = dtype


class GoFuncType(GoType):
    """For function types."""

    def __init__(self, params, result=None):
        super().__init__("function")
        self.params = params
        self.result = result


class GoParam:
    """For parameters to be passed to functions."""

    def __init__(self, name=None, dtype=None):
        self.name = name
        self.dtype = name


class GoInterfaceType(GoType):
    """For interfaces."""

    def __init__(self, methods):
        super().__init__("function")
        self.methods = methods


class GoMethodFunc:
    """For methods (not functions)."""

    def __init__(self, name, params, result=None):
        self.name = name
        self.params = params
        self.result = result


# =============================================================================
# BLOCKS
# =============================================================================


class GoBlock:
    """For blocks of statements."""

    def __init__(self, statements):
        self.statements = statements


# =============================================================================
# DECLARATIONS AND SCOPE
# =============================================================================


class GoDecl:
    """The base class to inherit declarations from."""

    def __init__(self, kind, declarations):
        self.kind = kind
        self.declarations = declarations


class GoConstSpec:
    """For a single spec of a constant in a const declaration."""

    def __init__(self, id_list, dtype=None, expr=None):
        self.id_list = id_list
        self.dtype = dtype
        self.expr = expr


class GoTypeDefAlias:
    """For typedefs and aliases."""

    def __init__(self, kind, alias, actual):
        self.kind = kind
        self.alias = alias
        self.actual = actual


class GoVarSpec:
    """For a single spec of a variable in a declaration of variables."""

    def __init__(self, lhs, dtype, rhs):
        self.lhs = lhs
        self.dtype = dtype
        self.rhs = rhs


class GoShortDecl(GoDecl):
    """For short declarations."""

    def __init__(self, id_list, expr_list):
        super().__init__("short", [])
        self.id_list = id_list
        self.expr_list = expr_list


class GoFuncDecl(GoDecl):
    """For function declarations."""

    def __init__(self, name, params, result, body):
        super().__init__("function", [])
        self.name = name
        self.params = params
        self.result = result
        self.body = body


class GoMethDecl(GoDecl):
    """For method (not function) declarations."""

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


class GoBaseLit:
    """The base class to inherit literals from."""

    def __init__(self, kind):
        self.kind = kind


class GoBasicLit(GoBaseLit):
    """For literals like integers, strings and so on."""

    def __init__(self, item):
        super().__init__("basic")
        self.item = item


class GoCompositeLit(GoBaseLit):
    """For composite literals."""

    def __init__(self, dtype, value):
        super().__init__("composite")
        self.dtype = dtype
        self.value = value


class GoKeyedElement:
    """For keyed elements in composite literals."""

    def __init__(self, key, element):
        self.key = key
        self.element = element


class GoBaseExpr:
    """The base class to inherit expressions from."""

    def __init__(self, kind):
        self.kind = kind


class GoPrimaryExpr(GoBaseExpr):
    """For primary expressions (operands for unary/binary expressions)."""

    def __init__(self, lhs, rhs):
        super().__init__("primary")
        self.lhs = lhs
        self.rhs = rhs  # rhs may be none


class GoSelector:
    """For selection of an attribute from package/struct in a primary expr."""

    def __init__(self, child):
        self.child = child


class GoIndex:
    """For indexing an array in a primary expr."""

    def __init__(self, index):
        self.index = index


class GoArguments:
    """For arguments to a function."""

    def __init__(self, expr_list, dtype=None):
        self.expr_list = expr_list
        self.dtype = dtype  # dtype can be None


class GoExpression(GoBaseExpr):
    """For expressions made using binary operators."""

    def __init__(self, lhs, rhs, op):
        super().__init__("expression")
        self.lhs = lhs
        self.rhs = rhs
        self.op = op


class GoUnaryExpr(GoBaseExpr):
    """For expressions made using unary operators."""

    def __init__(self, expr, op):
        super().__init__("unary")
        self.expr = expr
        self.op = op


# =============================================================================
# STATEMENTS
# =============================================================================


class GoAssign:
    """For assignment statements."""

    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op  # op can be None, indicating a simple assignment


class GoIf:
    """For if/else statements."""

    def __init__(self, stmt, cond, inif, inelse):
        self.stmt = stmt  # stmt can be None, indicating no statement
        self.cond = cond
        self.inif = inif
        self.inelse = inelse


class GoSwitch:
    """For switch/case statements."""

    def __init__(self, stmt, cond, case_list):
        self.stmt = stmt  # stmt can be None, indicating no statement
        self.cond = cond
        self.case_list = case_list


class GoCaseClause:
    """For a single case clause in a switch/case statement."""

    def __init__(self, kind, expr_list, stmt_list):
        self.kind = kind  # stmt can be None, indicating no statement
        self.expr_list = expr_list
        self.stmt_list = stmt_list


class GoFor:
    """For loops (for/while/range)."""

    def __init__(self, clause, infor):
        self.clause = clause
        self.infor = infor


class GoBaseForCl:
    """The base class to inherit for loop clauses from.

    For loop clauses include C-style for loop and clauses using "range".
    """

    def __init__(self, kind):
        self.kind = kind


class GoForClause(GoBaseForCl):
    """For C-style for loop clauses."""

    def __init__(self, init, expr, post):
        super().__init__("standard")
        self.init = init  # init can be None, indicating no statement
        self.expr = expr  # expr can be None, indicating no statement
        self.post = post  # post can be None, indicating no statement


class GoRange(GoBaseForCl):
    """For loop clauses using "range"."""

    def __init__(self, lhs, rhs):
        super().__init__("range")
        self.lhs = lhs
        self.rhs = rhs


class GoControl:
    """The base class to inherit control statements from.

    Control statements include return, break, continue, goto and fallthrough.
    """

    def __init__(self, kind):
        self.kind = kind


class GoReturn(GoControl):
    """For "return" statements."""

    def __init__(self, expr_list):
        super().__init__("return")
        self.expr_list = expr_list


class GoLabelCtrl(GoControl):
    """For control statements that use labels.

    Statements include: "break", "continue", and "goto".
    """

    def __init__(self, keyword, label):
        super().__init__("label")
        self.keyword = keyword
        self.label = label  # label can be None


# =============================================================================
# PACKAGES
# =============================================================================


class GoSourceFile:
    """For the source file."""

    def __init__(self, package, imports, declarations):
        self.package = package
        self.imports = imports
        self.declarations = declarations


class GoImportSpec:
    """For an import specification."""

    def __init__(self, package, import_as=None):
        self.package = package
        self.import_as = import_as
