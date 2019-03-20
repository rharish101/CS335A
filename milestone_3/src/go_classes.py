"""Contains classes used by the parser (and possibly the semantic analyser)."""
# =============================================================================
# TYPES
# =============================================================================


class GoBaseType:
    """The base class to inherit types from."""

    def __init__(self, kind):
        self.kind = kind


class GoType(GoBaseType):
    """For inbuilt types and typedef/aliases being used after declaration.

    Inbuilt types are:
        uint8, uint16, uint32, uint64
        int8, int16, int32, int64
        float32, float64
        complex64, complex128
        byte (alias for uint8), rune (alias for int32)
        uint, int, uintptr
        string

    WARNING:
        Sometimes standard variables may be cast as this type. The most common
        scenario is when multiple parameters of the same type are being passed
        into functions with the common type being specified only once.
    """

    def __init__(self, name, basic_lit=False, value=None, size=0, offset=0):
        super().__init__("inbuilt")
        self.name = name  # For storing name of this type
        self.basic_lit = basic_lit
        self.size = size
        self.offset = offset
        self.value = value


class GoFromModule:
    """For module imports."""

    def __init__(self, parent, child):
        self.parent = parent
        self.child = child
        # For storing name of this type
        if type(parent) is str:
            self.name = parent + "." + child
        elif hasattr(parent, "name"):
            self.name = parent.name + "." + child
        else:
            self.name = str(parent) + "." + child


class GoArray(GoBaseType):
    """For array types."""

    def __init__(
        self, length, dtype, depth=1, size=0, offset=0, final_type=None
    ):
        super().__init__("array")
        self.length = length
        self.dtype = dtype
        self.depth = depth
        # self.name = "*" + dtype.name  # For storing name of this type
        self.size = size
        self.offset = offset
        self.final_type = dtype


class GoStruct(GoBaseType):
    """For struct types."""

    def __init__(self, fields):
        super().__init__("struct")
        # vars and tags should be lists so as to enforce order on the inputs given to the struct
        self.vars = []
        self.tags = []
        # XXX don't know about this
        self.embeds = {}
        self.size = 0
        self.offset = 0
        self.name = "struct"  # For storing name of this type
        used = set()
        for field in fields:
            if field.dtype.kind == "embedded":
                name = field.vars[0]
                if isinstance(name, GoDeref):
                    name = name.var
                if isinstance(name, GoFromModule):
                    name = name.child
                if name not in used:
                    self.embeds[name] = field.vars[0]
                    used.add(name)
                else:
                    raise ValueError(
                        'Error: Already used embedded field "{}" in struct '
                        "declaration"
                    )
            else:
                for var in field.vars:
                    if var not in used:
                        self.vars.append((var, GoVar(field.dtype)))
                        self.tags.append((var, field.tag))
                        used.add(var)
                    else:
                        raise ValueError(
                            'Error: Already used variable name "{}" in struct '
                            "declaration"
                        )


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

    def __init__(self, dtype):
        self.dtype = dtype


class GoPointType(GoBaseType):
    """For pointer types."""

    def __init__(self, dtype, size=0, offset=0):
        super().__init__("pointer")
        self.dtype = dtype
        self.size = size
        self.offset = offset
        # self.name = "*" + dtype.name  # For storing name of this type


# dtype can be of class GoPrimarayExpr, which has no name attribute


class GoFuncType(GoBaseType):
    """For function types."""

    def __init__(self, params, result=None):
        super().__init__("function")
        self.params = params
        self.result = result
        self.name = "function"  # For storing name of this type


class GoParam:
    """For parameters to be passed to functions."""

    def __init__(self, name=None, dtype=None):
        self.name = name  # name can be None
        self.dtype = dtype


class GoInterfaceType(GoBaseType):
    """For interfaces."""

    def __init__(self, methods):
        super().__init__("function")
        self.name = "interface"  # For storing name of this type
        self.methods = {}
        used = set()
        for method in methods:
            if method.name not in used:
                self.methods[method.name] = method
                used.add(method.name)
            else:
                raise ValueError(
                    'Error: Already used method name "{}" in interface '
                    "declaration"
                )


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

    def __init__(self, item, dtype):
        super().__init__("basic")
        self.item = item
        self.dtype = dtype


class GoCompositeLit(GoBaseLit):
    """For composite literals."""

    def __init__(self, dtype, value, size=0):
        super().__init__("composite")
        self.dtype = dtype
        self.value = value
        self.size = size


class GoKeyedElement:
    """For keyed elements in composite literals."""

    def __init__(self, key, element, dtype=None, depth=1, use=None, size=0):
        self.key = key
        self.element = element
        self.dtype = dtype
        self.depth = depth
        self.use = use
        self.size = size


class GoBaseExpr:
    """The base class to inherit expressions from."""

    def __init__(self, kind):
        self.kind = kind


class GoPrimaryExpr(GoBaseExpr):
    """For primary expressions (operands for unary/binary expressions)."""

    def __init__(self, lhs, rhs, dtype=None, depth=1):
        super().__init__("primary")
        self.lhs = lhs
        self.rhs = rhs
        self.dtype = dtype
        self.depth = depth


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

    def __init__(self, expr_list,lineno=0):
        self.expr_list = expr_list
        self.lineno = lineno


class GoExpression(GoBaseExpr):
    """For expressions made using binary operators."""

    def __init__(self, lhs, rhs, op, dtype=None):
        super().__init__("expression")
        self.lhs = lhs
        self.rhs = rhs
        self.op = op
        self.dtype = dtype


class GoUnaryExpr(GoBaseExpr):
    """For expressions made using unary operators."""

    def __init__(self, expr, op, dtype=None):
        super().__init__("unary")
        self.expr = expr
        self.op = op
        self.dtype = dtype


# =============================================================================
# STATEMENTS
# =============================================================================


class GoBaseStmt:
    """The base class to inherit statements from."""

    def __init__(self):
        pass


class GoAssign(GoBaseStmt):
    """For assignment statements."""

    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op  # op can be None, indicating a simple assignment


class GoIf(GoBaseStmt):
    """For if/else statements."""

    def __init__(self, stmt, cond, inif, inelse):
        self.stmt = stmt  # stmt can be None, indicating no statement
        self.cond = cond
        self.inif = inif
        self.inelse = inelse


class GoSwitch(GoBaseStmt):
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


class GoFor(GoBaseStmt):
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


class GoControl(GoBaseStmt):
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
        self.declarations = declarations

        self.imports = []
        for import_decl in imports:
            for import_spec in import_decl.declarations:
                self.imports.append(import_spec)


class GoImportSpec:
    """For an import specification."""

    def __init__(self, package, import_as=None):
        self.package = package
        self.import_as = import_as
