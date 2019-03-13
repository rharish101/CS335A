"""Parser for Go."""
from ply import yacc
from lexer import tokens, lexer, t_error, go_traceback
from go_classes import *

precedence = (
    ("left", "LSQBRACK"),
    ("left", "RSQBRACK"),
    ("left", "LCURLBR"),
    ("left", "RCURLBR"),
    ("left", "LBRACK"),
    ("left", "RBRACK"),
    ("left", "ID"),
    ("left", "SHDECL"),
    ("left", "COMMA"),
    ("left", "TRIDOT"),
    ("left", "DOT"),
    ("left", "SEMICOLON"),
    ("left", "COLON"),
    ("left", "NEWLINES"),
    ("left", "BREAK"),
    ("left", "CONTINUE"),
    ("left", "RETURN"),
    ("left", "INT"),
    ("left", "FLOAT"),
    ("left", "STRING"),
    ("left", "LOGAND"),
    ("left", "LOGOR"),
    ("left", "EQUALS", "NOTEQ"),
    ("left", "BITOR"),
    ("left", "BITXOR"),
    ("left", "BITAND", "BITCLR"),
    ("left", "LESS", "LESSEQ", "GREAT", "GREATEQ"),
    ("left", "LSHIFT", "RSHIFT"),
    ("left", "PLUS", "MINUS"),
    ("left", "MULT", "DIV", "MODULO"),
)

# =============================================================================
# BASIC
# =============================================================================


def p_start(p):
    "start : SourceFile"
    p[0] = p[1]


def p_empty(p):
    "empty :"


def p_error(p):
    t_error(p)


# =============================================================================
# TYPES
# =============================================================================


def p_Type(p):
    """Type : TypeLit
            | LBRACK ID RBRACK
            | LBRACK Type RBRACK
            | LBRACK ID DOT ID RBRACK
    """
    if len(p) == 2:  # TypeLit
        p[0] = p[1]
    elif len(p) == 4:  # Type or ID
        if isinstance(p[2], GoBaseType):  # Type
            p[0] = p[2]
        else:  # ID
            p[0] = GoType(p[2])
    else:  # ID DOT ID
        p[0] = GoFromModule(p[2], p[4])


def p_TypeLit(p):
    """TypeLit : LiteralType
               | InterfaceType
               | PointerType
               | FunctionType
    """
    p[0] = p[1]


def p_ArrayType(p):
    """ArrayType : LSQBRACK ArrayLength RSQBRACK Type
                 | LSQBRACK ArrayLength RSQBRACK ID DOT ID
                 | LSQBRACK ArrayLength RSQBRACK ID
                 | LSQBRACK RSQBRACK Type
                 | LSQBRACK RSQBRACK ID DOT ID
                 | LSQBRACK RSQBRACK ID
    """
    if len(p) == 5:  # Type or ID
        if isinstance(p[4], GoBaseType):  # Type
            arr_type = p[4]
        else:  # ID
            arr_type = GoType(p[4])
        length = p[2]
    elif len(p) == 7:  # ID DOT ID
        arr_type = GoFromModule(p[4], p[6])
        length = p[2]
    elif len(p) == 4:
        if isinstance(p[3], GoBaseType):  # Type
            arr_type = p[3]
        else:  # ID
            arr_type = GoType(p[3])
        length = "variable"
    else:
        arr_type = GoFromModule(p[3], p[5])
        length = "variable"

    p[0] = GoArray(length, arr_type)


def p_ArrayLength(p):
    """ArrayLength : Expression
    """
    p[0] = p[1]


def p_StructType(p):
    """StructType : STRUCT LCURLBR FieldDeclList RCURLBR
    """
    try:
        p[0] = GoStruct(p[3])
    except ValueError as msg:
        position = go_traceback(p.slice[1])
        print("{} at position {}".format(msg, position))
        exit()


def p_FieldDecl(p):
    """FieldDecl : IdentifierList Type TagTop
                 | IdentifierList ID DOT ID TagTop
                 | IdentifierList ID TagTop
                 | ID Type TagTop
                 | ID ID DOT ID TagTop
                 | ID ID TagTop
                 | MULT ID DOT ID TagTop
                 | ID DOT ID TagTop
                 | MULT ID TagTop
                 | ID TagTop
    """
    tag = p[len(p) - 1]

    # Explicit field
    if len(p) in (4, 6):
        if len(p) == 4:
            if isinstance(p[2], GoBaseType):  # Type
                field_type = p[2]
            else:  # ID
                field_type = GoType(p[2])
        else:  # ID DOT ID
            field_type = GoFromModule(p[2], p[4])
        if type(p[1]) is list:
            var_list = p[1]
        else:
            var_list = [p[1]]

    # Embedded field
    else:
        field_type = GoBaseType("embedded")
        if len(p) == 6:
            var_list = [GoDeref(GoFromModule(p[2], p[4]))]
        elif len(p) == 5:
            var_list = [GoFromModule(p[1], p[3])]
        elif len(p) == 4:
            var_list = [GoDeref(p[2])]
        else:
            var_list = [p[1]]

    p[0] = GoStructField(var_list, field_type, tag)


def p_FieldDeclList(p):
    """FieldDeclList : empty
                     | FieldDeclList FieldDecl SEMICOLON
    """
    if p[1] is None:  # empty
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_TagTop(p):
    """TagTop : empty
              | STRING
    """
    if p[1] is None:  # empty
        p[0] = ""
    else:
        p[0] = p[1]


def p_PointerType(p):
    """PointerType : MULT Type
                   | MULT ID DOT ID
                   | MULT ID
    """
    if isinstance(p[2], GoBaseType):  # Type
        point_to = p[2]
    elif len(p) == 5:  # ID DOT ID
        point_to = GoFromModule(p[2], p[4])
    else:  # ID
        point_to = GoType(p[2])
    p[0] = GoPointType(point_to)


def p_FunctionType(p):
    """FunctionType : FUNC Signature
    """
    p[0] = GoFuncType(*p[2])


def p_Signature(p):
    """Signature : Parameters
                 | Parameters Result
    """
    # First element is Parameters, second is Result
    if len(p) == 2:  # No result given
        p[0] = (p[1], None)
    else:
        p[0] = (p[1], p[2])


# XXX Parameters, TypeLit unimplemented during type checking
def p_Result(p):
    """Result : Parameters
              | TypeLit
              | ID DOT ID
              | ID
    """
    if type(p[1]) is list:  # Parameters
        p[0] = p[1]
    else:
        if isinstance(p[1], GoBaseType) or isinstance(
            p[1], GoFromModule
        ):  # Type
            dtype = p[1]
        elif len(p) == 4:  # ID DOT ID
            dtype = GoFromModule(p[1], p[3])
        else:  # ID
            dtype = GoType(p[1])
        p[0] = GoParam(dtype=dtype)
        # p[0] = [GoParam(dtype=dtype)]


def p_Parameters(p):
    """Parameters : LBRACK RBRACK
                  | LBRACK ParameterList RBRACK
                  | LBRACK ParameterList COMMA RBRACK
    """
    if len(p) == 3:  # Nothing in there
        p[0] = []
    else:  # COMMA doesn't matter
        p[0] = p[2]


def p_ParameterList(p):
    """ParameterList : ParameterDecl
                     | ParameterList COMMA ParameterDecl
    """
    if len(p) == 2:  # Single ParameterDecl
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_ParameterDecl(p):
    """ParameterDecl : TRIDOT Type
                     | TRIDOT ID DOT ID
                     | TRIDOT ID
                     | ID TRIDOT Type
                     | ID TRIDOT ID DOT ID
                     | ID TRIDOT ID
                     | Type
                     | ID DOT ID
                     | ID
                     | ID Type
                     | ID ID DOT ID
                     | ID ID
    """
    # Remove support for variadic params
    new_p = []
    for item in p:
        if type(item) is not str or item != "...":
            new_p.append(item)

    if len(new_p) == 2 or len(new_p) == 4:  # only types given
        name = None
    else:  # ID given as name
        name = new_p[1]

    if isinstance(new_p[-1], GoBaseType):  # GoBaseType
        dtype = new_p[-1]
    elif len(new_p) > 3:  # ID DOT ID
        dtype = GoFromModule(new_p[-3], new_p[-1])
    else:  # ID
        dtype = GoType(new_p[-1])

    p[0] = GoParam(name=name, dtype=dtype)


def p_InterfaceType(p):
    """InterfaceType : INTERFACE LCURLBR MethodSpecList RCURLBR
    """
    try:
        p[0] = GoInterfaceType(p[3])
    except ValueError as msg:
        position = go_traceback(p.slice[1])
        print("{} at position {}".format(msg, position))
        exit()


def p_MethodSpecList(p):
    """MethodSpecList : empty
                      | MethodSpecList MethodSpec SEMICOLON
    """
    if len(p) == 2:  # empty
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_MethodSpec(p):
    """MethodSpec : ID Signature
                  | ID DOT ID
                  | ID
    """
    if len(p) == 3:  # Function signature given
        p[0] = GoMethodFunc(p[1], *p[2])
    elif len(p) == 4:  # ID DOT ID element
        p[0] = GoFromModule(p[1], p[3])
    else:  # ID element
        p[0] = GoType(p[1])


# =============================================================================
# BLOCKS
# =============================================================================


def p_Block(p):
    """Block : LCURLBR StatementList RCURLBR
    """
    p[0] = GoBlock(p[2])


def p_StatementList(p):
    """StatementList : Statement SEMICOLON StatementList
                     | empty
    """
    if len(p) == 2:  # emtpy
        p[0] = []
    else:
        p[0] = [p[1]] + p[3]


# =============================================================================
# DECLARATIONS AND SCOPE
# =============================================================================


def p_Declaration(p):
    """Declaration : ConstDecl
                   | TypeDecl
                   | VarDecl
    """
    p[0] = p[1]


def p_TopLevelDecl(p):
    """TopLevelDecl : Declaration
                    | FunctionDecl
                    | MethodDecl
    """
    p[0] = p[1]


def p_TopLevelDeclList(p):
    """TopLevelDeclList : TopLevelDecl SEMICOLON TopLevelDeclList
                        | empty
    """
    if len(p) == 2:  # empty
        p[0] = []
    else:
        p[0] = [p[1]] + p[3]


def p_ConstDecl(p):
    """ConstDecl  : CONST LBRACK ConstSpecList RBRACK
                  | CONST ConstSpec
                  | CONST ID
    """
    if len(p) == 3:  # Single constant spec
        if isinstance(p[2], GoConstSpec):  # ConstSpec
            declarations = [p[2]]
        else:  # ID
            declarations = [GoConstSpec(p[2])]
    else:  # List of constant specs
        declarations = p[3]
    p[0] = GoDecl("constant", declarations)


def p_ConstSpec(p):
    """ConstSpec : IdentifierList
                 | IdentifierList Type ASSIGN ExpressionList
                 | IdentifierList ID DOT ID ASSIGN ExpressionList
                 | IdentifierList ID ASSIGN ExpressionList
                 | IdentifierList ASSIGN ExpressionList
                 | IdentifierList Type ASSIGN Expression
                 | IdentifierList ID DOT ID ASSIGN Expression
                 | IdentifierList ID ASSIGN Expression
                 | IdentifierList ASSIGN Expression
                 | ID Type ASSIGN ExpressionList
                 | ID ID DOT ID ASSIGN ExpressionList
                 | ID ID ASSIGN ExpressionList
                 | ID ASSIGN ExpressionList
                 | ID Type ASSIGN Expression
                 | ID ID DOT ID ASSIGN Expression
                 | ID ID ASSIGN Expression
                 | ID ASSIGN Expression
    """
    if len(p) == 2:  # Simply declaring constants
        p[0] = GoConstSpec(p[1])
        return

    if type(p[1]) is list:  # IdentifierList
        id_list = p[1]
    else:  # ID
        id_list = [p[1]]

    if isinstance(p[2], GoBaseType):  # Type
        dtype = p[2]
    elif len(p) == 7:  # ID DOT ID
        dtype = GoFromModule(p[2], p[4])
    elif len(p) == 5:  # ID
        dtype = GoType(p[2])
    else:  # Type-less
        dtype = None

    if type(p[len(p) - 1]) is list:  # ExpressionList
        expressions = p[len(p) - 1]
    else:  # Expression
        expressions = [p[len(p) - 1]]

    p[0] = GoConstSpec(id_list, dtype, expressions)


def p_ConstSpecList(p):
    """ConstSpecList : empty
                     | ConstSpecList ConstSpec SEMICOLON
                     | ConstSpecList ID SEMICOLON
    """
    if len(p) == 2:
        p[0] = []
    else:
        if len(p) == 5:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = p[1] + [GoConstSpec(p[2])]


def p_IdentifierList(p):
    """IdentifierList : ID IdentifierBotList
    """
    p[0] = [p[1]] + p[2]


def p_IdentifierBotList(p):
    """IdentifierBotList : COMMA ID
                         | IdentifierBotList COMMA ID
    """
    if len(p) == 3:  # Just COMMA ID
        p[0] = [p[2]]
    else:
        p[0] = p[1] + [p[3]]


def p_ExpressionList(p):
    """ExpressionList : Expression ExpressionBotList
    """
    p[0] = [p[1]] + p[2]


def p_TypeDecl(p):
    """TypeDecl : TYPE TypeSpecTopList
    """
    p[0] = GoDecl("type", p[2])


def p_TypeSpec(p):
    """TypeSpec : AliasDecl
                | TypeDef
    """
    p[0] = p[1]


def p_TypeSpecList(p):
    """TypeSpecList : empty
                    | TypeSpecList TypeSpec SEMICOLON
    """
    if len(p) == 2:  # empty
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_TypeSpecTopList(p):
    """TypeSpecTopList : TypeSpec
                       | LBRACK TypeSpecList  RBRACK
    """
    if len(p) == 2:  # single TypeSpec
        p[0] = [p[1]]
    else:
        p[0] = p[2]


def p_AliasDecl(p):
    """AliasDecl : ID ASSIGN Type
                 | ID ASSIGN ID DOT ID
                 | ID ASSIGN ID
    """
    if isinstance(p[3], GoBaseType):  # Type
        dtype = p[3]
    elif len(p) == 6:  # ID DOT ID
        dtype = GoFromModule(p[3], p[5])
    else:  # ID
        dtype = GoType(p[3])
    p[0] = GoTypeDefAlias("alias", p[1], dtype)


def p_TypeDef(p):
    """TypeDef : ID Type
               | ID ID DOT ID
               | ID ID
    """
    if isinstance(p[2], GoBaseType):  # Type
        dtype = p[2]
    elif len(p) == 5:  # ID DOT ID
        dtype = GoFromModule(p[2], p[4])
    else:  # ID
        dtype = GoType(p[2])
    p[0] = GoTypeDefAlias("typedef", p[1], dtype)


def p_VarDecl(p):
    """VarDecl : VAR VarSpecTopList
    """
    p[0] = GoDecl("var", p[2])


def p_VarSpec(p):
    """VarSpec : IdentifierList Type VarSpecMid
               | IdentifierList ID DOT ID VarSpecMid
               | IdentifierList ID VarSpecMid
               | IdentifierList ASSIGN ExpressionList
               | IdentifierList ASSIGN Expression
               | ID Type VarSpecMid
               | ID ID DOT ID VarSpecMid
               | ID ID VarSpecMid
               | ID ASSIGN ExpressionList
               | ID ASSIGN Expression
    """
    if type(p[1]) is list:  # IdentifierList
        lhs = p[1]
    else:  # ID
        lhs = [p[1]]

    if type(p[len(p) - 1]) is list:  # VarSpecMid or ExpressionList
        rhs = p[len(p) - 1]
    else:  # Expression
        rhs = []

    if isinstance(p[2], GoBaseType):  # Type
        dtype = p[2]
    elif len(p) == 6:  # ID DOT ID
        dtype = GoFromModule(p[2], p[4])
    elif type(p[2]) is str:  # ID
        dtype = GoType(p[2])
    else:  # No type given
        dtype = None

    p[0] = GoVarSpec(lhs, dtype, rhs)


def p_VarSpecMid(p):
    """VarSpecMid : empty
                  | ASSIGN ExpressionList
                  | ASSIGN Expression
    """
    if len(p) == 2:  # empty
        p[0] = []
    elif type(p[2]) is list:  # ExpressionList
        p[0] = p[2]
    else:  # Expression
        p[0] = [p[2]]


def p_VarSpecList(p):
    """VarSpecList : empty
                   | VarSpecList VarSpec SEMICOLON
    """
    if len(p) == 2:  # empty
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_VarSpecTopList(p):
    """VarSpecTopList : VarSpec
                      | LBRACK VarSpecList RBRACK
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[2]


def p_ShortVarDecl(p):
    """ShortVarDecl : ExpressionList SHDECL ExpressionList
                    | ExpressionList SHDECL Expression
                    | Expression SHDECL ExpressionList
                    | Expression SHDECL Expression
    """
    if type(p[1]) is list:  # IdentifierList
        id_list = p[1]
    else:
        id_list = [p[1]]

    if type(p[3]) is list:
        expressions = p[3]
    else:
        expressions = [p[3]]

    p[0] = GoShortDecl(id_list, expressions)


def p_FunctionDecl(p):
    """FunctionDecl : FUNC FunctionName FunctionDeclTail
    """
    p[0] = GoFuncDecl(p[2], *p[3])


def p_FunctionDeclTail(p):
    """FunctionDeclTail : Function
                        | Signature
    """
    if len(p[1]) == 3:  # Function is a tuple of (Parameters, Results, Body)
        p[0] = p[1]
    else:  # Signature is a tuple of (Parameters, Results)
        p[0] = (*p[1], GoBlock([]))


def p_FunctionName(p):
    """FunctionName : ID
    """
    p[0] = p[1]


def p_Function(p):
    """Function : Signature FunctionBody
    """
    # Signature is a tuple of (Parameters, Results)
    p[0] = (*p[1], p[2])


def p_FunctionBody(p):
    """FunctionBody : Block
    """
    p[0] = p[1]


def p_MethodDecl(p):
    """MethodDecl : FUNC Receiver ID FunctionDeclTail
    """
    # FunctionDeclTail is a tuple of (Parameters, Results, Body)
    p[0] = GoMethDecl(p[2], p[3], *p[4])


def p_Receiver(p):
    """Receiver : Parameters
    """
    p[0] = p[1]


# =============================================================================
# EXPRESSIONS
# =============================================================================


def p_Operand(p):
    """Operand : Literal
               | MethodExpr
               | LBRACK Expression RBRACK
    """
    if len(p) == 2:  # Literal or MethodExpr
        p[0] = p[1]
    else:  # Expression
        p[0] = p[2]


def p_Literal(p):
    """Literal : BasicLit
               | FunctionLit
               | CompositeLit
    """
    p[0] = p[1]


def p_BasicLit(p):
    """BasicLit : INT
                | FLOAT
                | IMAG
                | STRING
                | RUNE
    """
    if p.slice[1].type == "INT":
        p[1] = int(p[1])
    elif p.slice[1].type == "FLOAT":
        p[1] = float(p[1])
    elif p.slice[1].type == "IMAG":
        p[1] = complex(p[1][:-1] + "j")

    dtype = p.slice[1].type.lower()
    if dtype == "imag":
        dtype = "complex"

    p[0] = GoBasicLit(p[1], GoType(dtype, True))


def p_CompositeLit(p):
    """CompositeLit : LiteralType LiteralValue
                    | ID DOT ID LiteralValue
                    | ID LiteralValue
                    | LSQBRACK TRIDOT RSQBRACK Type LiteralValue
                    | LSQBRACK TRIDOT RSQBRACK ID DOT ID LiteralValue
                    | LSQBRACK TRIDOT RSQBRACK ID LiteralValue
    """
    if len(p) < 6:  # No square brackets
        if isinstance(p[1], GoBaseType):  # LiteralType
            dtype = p[1]
        elif len(p) == 5:  # ID DOT ID
            dtype = GoFromModule(p[1], p[3])
        else:  # ID
            dtype = GoType(p[1])
    elif isinstance(p[4], GoBaseType):  # Type
        dtype = GoArray("variable", p[4])
    elif len(p) == 8:  # ID DOT ID
        dtype = GoArray("variable", GoFromModule(p[4], p[6]))
    else:
        dtype = GoArray("variable", GoType(p[4]))

    p[0] = GoCompositeLit(dtype, p[len(p) - 1])


def p_LiteralType(p):
    """LiteralType : ArrayType
                   | StructType
    """
    p[0] = p[1]


def p_LiteralValue(p):
    """LiteralValue : LCURLBR RCURLBR
                    | LCURLBR ElementList RCURLBR
                    | LCURLBR ElementList COMMA RCURLBR
    """
    if len(p) == 3:  # No ElementList given
        p[0] = []
    else:  # ElementList
        p[0] = p[2]


def p_ElementList(p):
    """ElementList : KeyedElement
                   | ElementList COMMA KeyedElement
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_KeyedElement(p):
    """KeyedElement : Expression
                    | LiteralValue
                    | ID COLON Expression
                    | Expression COLON Expression
                    | LiteralValue COLON Expression
                    | ID COLON LiteralValue
                    | Expression COLON LiteralValue
                    | LiteralValue COLON LiteralValue
    """
    if len(p) == 2:  # No key
        key = None
    else:  # Key given
        key = p[1]

    p[0] = GoKeyedElement(key, p[len(p) - 1])


def p_FunctionLit(p):
    """FunctionLit : FUNC Function
    """
    p[0] = p[2]


def p_PrimaryExpr(p):
    """PrimaryExpr : Operand
                   | ID
                   | PrimaryExpr Selector
                   | PrimaryExpr Index
                   | PrimaryExpr Arguments
    """
    if len(p) == 2:  # Operand or ID
        p[0] = p[1]
    else:  # PrimaryExpr given; make a new PrimaryExpr with args as children
        p[0] = GoPrimaryExpr(p[1], p[2])


def p_Selector(p):
    """Selector : DOT ID
    """
    p[0] = GoSelector(p[2])


def p_Index(p):
    """Index : LSQBRACK Expression RSQBRACK
    """
    p[0] = GoIndex(p[2])


def p_Arguments(p):
    """Arguments : LBRACK RBRACK
                 | LBRACK ExpressionList RBRACK
                 | LBRACK Expression RBRACK
                 | LBRACK ExpressionList TRIDOT RBRACK
                 | LBRACK Expression TRIDOT RBRACK
                 | LBRACK TRIDOT RBRACK
    """
    # Remove support for variadic params and remove trailing comma
    new_p = []
    for i, item in enumerate(p):
        if (type(item) is not str or item != "...") and (
            i != len(p) - 2 or type(item) is not str or item != ","
        ):
            new_p.append(item)

    if len(new_p) == 3:  # no arguments
        p[0] = GoArguments([])
        return

    if type(new_p[2]) is list:  # ExpressionList
        expressions = new_p[2]
    elif isinstance(new_p[2], GoBaseExpr):  # Expression
        expressions = [new_p[2]]
    else:  # no expressions, only type
        expressions = []

    p[0] = GoArguments(expressions)


# XXX
def p_MethodExpr(p):
    """MethodExpr : ReceiverType DOT ID   %prec ID
                  | ID DOT ID        %prec ID
                  | ID DOT ID DOT ID
    """
    if len(p) == 4:  # Single import from ReceiverType/package
        p[0] = GoFromModule(p[1], p[3])
    else:  # Double import from package/class
        p[0] = GoFromModule(GoFromModule(p[1], p[3]), p[5])


# XXX
def p_ReceiverType(p):
    """ReceiverType : LBRACK MULT ID DOT ID RBRACK
                    | LBRACK MULT ID RBRACK
                    | LBRACK ReceiverType RBRACK
    """
    if len(p) == 7:  # Deferencing a package import
        p[0] = GoDeref(GoFromModule(p[3], p[5]))
    elif len(p) == 5:  # Deferencing a variable
        p[0] = GoDeref(p[3])
    else:  # ReceiverType
        p[0] = p[2]


def p_Expression(p):
    """Expression : UnaryExpr
                  | Expression LOGOR Expression
                  | Expression LOGAND Expression
                  | Expression EQUALS Expression
                  | Expression NOTEQ Expression
                  | Expression LESS Expression
                  | Expression LESSEQ Expression
                  | Expression GREAT Expression
                  | Expression GREATEQ Expression
                  | Expression PLUS Expression
                  | Expression MINUS Expression
                  | Expression BITOR Expression
                  | Expression BITXOR Expression
                  | Expression MULT Expression
                  | Expression DIV Expression
                  | Expression MODULO Expression
                  | Expression LSHIFT Expression
                  | Expression RSHIFT Expression
                  | Expression BITAND Expression
                  | Expression BITCLR Expression
    """
    if len(p) == 2:  # UnaryExpr given
        p[0] = p[1]
    else:
        if isinstance(p[1], GoBasicLit) and isinstance(p[3], GoBasicLit):
            # Direct calculation
            error = False
            try:
                p[0] = GoBasicLit(p[1].item, None)

                if p[2] == "||":
                    p[0].item = p[1].item or p[3].item
                elif p[2] == "&&":
                    p[0].item = p[1].item and p[3].item
                elif p[2] == "==":
                    p[0].item = p[1].item == p[3].item
                elif p[2] == "!=":
                    p[0].item = p[1].item != p[3].item
                elif p[2] == "<":
                    p[0].item = p[1].item < p[3].item
                elif p[2] == "<=":
                    p[0].item = p[1].item <= p[3].item
                elif p[2] == ">":
                    p[0].item = p[1].item > p[3].item
                elif p[2] == ">=":
                    p[0].item = p[1].item >= p[3].item
                elif p[2] == "+":
                    p[0].item += p[3].item
                elif p[2] == "-":
                    p[0].item -= p[3].item
                elif p[2] == "|":
                    p[0].item |= p[3].item
                elif p[2] == "^":
                    p[0].item ^= p[3].item
                elif p[2] == "*":
                    p[0].item *= p[3].item
                elif p[2] == "/":
                    p[0].item /= p[3].item
                elif p[2] == "%":
                    p[0].item %= p[3].item
                elif p[2] == "<<":
                    p[0].item <<= p[3].item
                elif p[2] == ">>":
                    p[0].item >>= p[3].item
                elif p[2] == "&":
                    p[0].item &= p[3].item
                elif p[2] == "&^":
                    p[0].item &= ~p[3].item
                else:
                    error = True

                precedence = ["complex", "float", "int"]
                if p[2] in [">", "<", "==", "!=", ">=", "<="]:
                    p[0].dtype = GoType(
                        "bool", p[1].dtype.basic_lit & p[3].dtype.basic_lit
                    )
                    print(p[0].dtype.name)
                elif p[1].dtype == p[3].dtype or precedence.index(
                    p[1].dtype.name
                ) > precedence.index(p[3].dtype.name):
                    p[0].dtype = p[1].dtype
                else:
                    p[0].dtype = p[3].dtype
            except Exception:
                error = True

            if error:
                go_traceback("")
                print(
                    'SyntaxError: Binary operator "{}" not applicable for '
                    'arguments of types "{}" and "{}"'.format(
                        p[2], p[1].dtype.name, p[3].dtype.name
                    )
                )
                exit()
        else:
            # 1st arg. is LHS, 2nd is RHS, 3rd is the operator
            p[0] = GoExpression(p[1], p[3], p[2])


def p_ExpressionBot(p):
    """ExpressionBot : empty
                     | Expression
    """
    if p[1] is None:  # empty
        p[0] = GoBaseExpr("empty")
    else:
        p[0] = p[1]


def p_ExpressionBotList(p):
    """ExpressionBotList : COMMA Expression
                         | COMMA Expression ExpressionBotList
    """
    if len(p) == 3:
        p[0] = [p[2]]
    else:
        p[0] = [p[2]] + p[3]


def p_UnaryExpr(p):
    """UnaryExpr : PrimaryExpr
                 | unary_op UnaryExpr
    """
    if len(p) == 2:  # PrimaryExpr
        p[0] = p[1]
    else:  # unary_op used
        if isinstance(p[2], GoBasicLit):  # Direct calculation
            error = False
            try:
                if p[2].dtype.name in ("string", "rune"):  # Error
                    error = True
                elif p[1] == "+":
                    pass
                elif p[1] == "-":
                    p[2].item = -1 * p[2].item
                elif p[1] == "!":
                    p[2].item = not p[2].item
                elif p[1] == "^":
                    if p[2].dtype.name == "int":
                        p[2].item = ~p[2].item
                    else:
                        error = True
                elif p[1] == "*":
                    error = True
                elif p[1] == "++":
                    p[2].item += 1
                elif p[1] == "--":
                    p[2].item -= 1
                else:
                    error = True
            except Exception:
                error = True

            if error:
                position = go_traceback(p.slice[1].value)
                print(
                    'SyntaxError: Unary operator "{}" not applicable for '
                    'argument of type "{}" at position {}'.format(
                        p[1], p[2].dtype.name.lower(), position
                    )
                )
                exit()
            else:
                p[0] = p[2]
        else:
            # 1st arg. is expression, 2nd arg. is unary_op
            p[0] = GoUnaryExpr(p[2], p[1])


def p_addmul_op(p):
    """addmul_op : add_op
                 | mul_op
    """
    p[0] = p[1]


def p_add_op(p):
    """add_op : PLUS
              | MINUS
              | BITOR
              | BITXOR
    """
    p[0] = p[1]


def p_mul_op(p):
    """mul_op  : MULT
               | DIV
               | MODULO
               | LSHIFT
               | RSHIFT
               | BITAND
               | BITCLR
    """
    p[0] = p[1]


def p_unary_op(p):
    """unary_op : PLUS
                | MINUS
                | LOGNOT
                | BITXOR
                | MULT
                | BITAND
                | REC
                | DECR
                | INCR
    """
    p[0] = p[1]


# =============================================================================
# STATEMENTS
# =============================================================================


def p_Statement(p):
    """Statement : Declaration
                 | SimpleStmt
                 | ReturnStmt
                 | Block
                 | IfStmt
                 | SwitchStmt
                 | ForStmt
                 | BreakStmt
                 | ContinueStmt
                 | GotoStmt
                 | FallthroughStmt
    """
    p[0] = p[1]


def p_SimpleStmt(p):
    """SimpleStmt : Expression
                  | Assignment
                  | ShortVarDecl
                  | IncDecStmt
    """
    p[0] = p[1]


def p_IncDecStmt(p):
    """IncDecStmt : Expression INCR
                  | Expression DECR
    """
    # 1st arg. is expression, 2nd arg. is unary_op
    p[0] = GoUnaryExpr(p[1], p[2])


def p_Assignment(p):
    """Assignment : Expression assign_op Expression
                  | Expression assign_op ExpressionList
                  | ExpressionList assign_op Expression
                  | ExpressionList assign_op ExpressionList
    """
    if type(p[1]) is list:  # LHS is ExpressionList
        lhs = p[1]
    else:  # LHS is a single Expression
        lhs = [p[1]]

    if type(p[3]) is list:  # RHS is ExpressionList
        rhs = p[3]
    else:  # RHS is a single Expression
        rhs = [p[3]]

    # 1st arg. is LHS, 2nd arg. is RHS, and 3rd arg. is the assign op
    p[0] = GoAssign(lhs, rhs, p[2])


def p_assign_op(p):
    """assign_op : addmul_op ASSIGN
                 | ASSIGN
    """
    if len(p) == 2:  # simple assignment
        p[0] = None
    else:
        p[0] = p[1]


def p_IfStmt(p):
    """IfStmt : IF LBRACK Expression RBRACK Block ElseBot
              | IF LBRACK SimpleStmt SEMICOLON Expression RBRACK Block ElseBot
    """
    if len(p) == 7:  # No SimpleStmt
        stmt = None
    else:
        stmt = p[3]
    p[0] = GoIf(stmt, p[len(p) - 4], p[len(p) - 2], p[len(p) - 1])


def p_ElseBot(p):
    """ElseBot : empty
               | ELSE ElseTail
    """
    if len(p) == 2:  # empty
        p[0] = GoBlock([])
    else:
        p[0] = p[2]


def p_ElseTail(p):
    """ElseTail : IfStmt
                | Block
    """
    if isinstance(p[1], GoBlock):
        p[0] = p[1]
    else:
        p[0] = GoBlock([p[1]])


def p_SwitchStmt(p):
    """SwitchStmt : ExprSwitchStmt
    """
    p[0] = p[1]


def p_ExprSwitchStmt(p):
    """ExprSwitchStmt : SWITCH LBRACK SimpleStmt SEMICOLON  ExpressionBot RBRACK LCURLBR ExprCaseClauseList RCURLBR
                      | SWITCH LBRACK ExpressionBot RBRACK LCURLBR ExprCaseClauseList RCURLBR
    """
    if len(p) == 8:  # No SimpleStmt given
        stmt = None
    else:
        stmt = p[2]
    p[0] = GoSwitch(stmt, p[len(p) - 5], p[len(p) - 2])


def p_ExprCaseClauseList(p):
    """ExprCaseClauseList : empty
                          | ExprCaseClauseList ExprCaseClause
    """
    if len(p) == 2:  # empty
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_ExprCaseClause(p):
    """ExprCaseClause : ExprSwitchCase COLON StatementList
    """
    p[0] = GoCaseClause(*p[1], p[3])


def p_ExprSwitchCase(p):
    """ExprSwitchCase : CASE ExpressionList
                      | CASE Expression
                      | DEFAULT
    """
    if len(p) == 2:  # default
        expressions = []
    elif type(p[2]) is list:
        expressions = p[2]
    else:
        expressions = [p[2]]
    p[0] = (p[1], expressions)


def p_ForStmt(p):
    """ForStmt : FOR LBRACK ExpressionBot RBRACK Block
               | FOR LBRACK ForClause RBRACK Block
               | FOR LBRACK RangeClause RBRACK Block
    """
    if isinstance(p[3], GoBaseExpr):  # while loop
        clause = GoForClause(None, p[3], None)
    else:
        clause = p[3]
    p[0] = GoFor(clause, p[5])


def p_ForClause(p):
    """ForClause : SimpleStmt SEMICOLON SimpleStmt SEMICOLON SimpleStmt
                 | SimpleStmt SEMICOLON SimpleStmt SEMICOLON empty
                 | SimpleStmt SEMICOLON empty SEMICOLON SimpleStmt
                 | SimpleStmt SEMICOLON empty SEMICOLON empty
                 | empty SEMICOLON SimpleStmt SEMICOLON SimpleStmt
                 | empty SEMICOLON SimpleStmt SEMICOLON empty
                 | empty SEMICOLON empty SEMICOLON SimpleStmt
                 | empty SEMICOLON empty SEMICOLON empty
    """
    p[0] = GoForClause(p[1], p[3], p[5])


def p_RangeClause(p):
    """RangeClause : ExpressionList assign_op RANGE Expression
                   | Expression assign_op RANGE Expression
                   | ExpressionList SHDECL RANGE Expression
                   | Expression SHDECL RANGE Expression
                   | empty RANGE Expression
    """
    if len(p) == 4:  # empty
        lhs = []
    else:
        lhs = p[1]
    p[0] = GoRange(lhs, p[len(p) - 1])


def p_ReturnStmt(p):
    """ReturnStmt : RETURN ExpressionList
                  | RETURN Expression
                  | RETURN
    """
    if len(p) == 2:
        expressions = []
    elif type(p[2]) is list:
        expressions = p[2]
    else:
        expressions = [p[2]]
    p[0] = GoReturn(expressions)


def p_BreakStmt(p):
    """BreakStmt : BREAK ID
                 | BREAK
    """
    if len(p) == 3:
        p[0] = GoLabelCtrl(p[1], p[2])
    else:
        p[0] = GoLabelCtrl(p[1], None)


def p_ContinueStmt(p):
    """ContinueStmt : CONTINUE ID
                    | CONTINUE
    """
    if len(p) == 3:
        p[0] = GoLabelCtrl(p[1], p[2])
    else:
        p[0] = GoLabelCtrl(p[1], None)


def p_GotoStmt(p):
    """GotoStmt : GOTO ID
    """
    p[0] = GoLabelCtrl(p[1], p[2])


def p_FallthroughStmt(p):
    """FallthroughStmt : FALLTHROUGH
    """
    p[0] = GoControl("fallthrough")


# =============================================================================
# PACKAGES
# =============================================================================


def p_SourceFile(p):
    """SourceFile : PACKAGE ID SEMICOLON ImportDeclList TopLevelDeclList
    """
    p[0] = GoSourceFile(p[2], p[4], p[5])


def p_ImportDecl(p):
    """ImportDecl : IMPORT LBRACK ImportSpecList RBRACK
                  | IMPORT ImportSpec
    """
    if len(p) == 3:  # single ImportSpec
        p[0] = GoDecl("import", [p[2]])
    else:  # ImportSpecList
        p[0] = GoDecl("import", p[3])


def p_ImportDeclList(p):
    """ImportDeclList : ImportDecl SEMICOLON ImportDeclList
                      | empty
    """
    if len(p) == 2:  # empty
        p[0] = []
    else:
        p[0] = [p[1]] + p[3]


def p_ImportSpec(p):
    """ImportSpec : DOT STRING
                  | ID STRING
                  | empty STRING
    """
    # package alias kept last so as to account for empty/default alias of None
    p[0] = GoImportSpec(p[2], p[1])


def p_ImportSpecList(p):
    """ImportSpecList : ImportSpec SEMICOLON ImportSpecList
                      | empty
    """
    if len(p) == 2:  # empty
        p[0] = []
    else:
        p[0] = [p[1]] + p[3]


parser = yacc.yacc()
