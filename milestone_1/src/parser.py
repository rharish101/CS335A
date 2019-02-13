#!/usr/bin/env python3
"""Parser for Go."""
from ply import yacc
from ply.lex import LexToken
from argparse import ArgumentParser
from lexer import tokens, lexer, t_error
from utils import *

precedence = (
    ("left", "ID"),
    ("left", "SHDECL"),
    ("left", "COMMA"),
    ("left", "LSQBRACK"),
    ("left", "RSQBRACK"),
    ("left", "LCURLBR"),
    ("left", "RCURLBR"),
    ("left", "TRIDOT"),
    ("left", "DOT"),
    ("left", "SEMICOLON"),
    ("left", "COLON"),
    ("left", "FLOAT"),
    ("left", "STRING"),
    ("left", "NEWLINES"),
    ("left", "BREAK"),
    ("left", "CONTINUE"),
    ("left", "RETURN"),
    ("left", "RBRACK"),
    ("left", "LBRACK"),
    ("left", "LOGOR"),
    ("left", "LOGAND"),
    ("left", "EQUALS", "NOTEQ", "LESS", "LESSEQ", "GREAT", "GREATEQ"),
    ("left", "PLUS", "MINUS", "BITOR", "BITXOR"),
    ("left", "MULT", "DIV", "MODULO", "BITAND", "BITCLR", "LSHIFT", "RSHIFT"),
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
        if isinstance(p[2], GoType):  # Type
            p[0] = p[2]
        else:  # ID
            p[0] = GoInbuiltType(p[2])
    else:  # ID DOT ID
        p[0] = GoFromModule(p[2], p[4])


def p_TypeLit(p):
    """TypeLit : ArrayType
               | StructType
               | InterfaceType
               | PointerType
               | FunctionType
    """
    p[0] = p[1]


def p_ArrayType(p):
    """ArrayType : LSQBRACK ArrayLength RSQBRACK Type
                 | LSQBRACK ArrayLength RSQBRACK ID
                 | LSQBRACK ArrayLength RSQBRACK ID DOT ID
    """
    if len(p) == 5:  # Type or ID
        if isinstance(p[4], GoType):  # Type
            arr_type = p[4]
        else:  # ID
            arr_type = GoInbuiltType(p[4])
    else:  # ID DOT ID
        arr_type = GoFromModule(p[4], p[6])
    p[0] = GoArray(p[2], arr_type)


def p_ArrayLength(p):
    """ArrayLength : Expression
    """
    p[0] = p[1]


def p_StructType(p):
    """StructType : STRUCT LCURLBR FieldDeclList RCURLBR
    """
    p[0] = GoStruct(p[3])


def p_FieldDecl(p):
    """FieldDecl : IdentifierList Type TagTop
                 | IdentifierList ID TagTop
                 | IdentifierList ID DOT ID TagTop
                 | MULT ID DOT ID TagTop
                 | ID DOT ID TagTop
                 | MULT ID TagTop
                 | ID TagTop
    """
    tag = p[len(p) - 1]

    # Explicit field
    if type(p[1]) is list:
        if len(p) == 4:
            if isinstance(p[2], GoType):  # Type
                field_type = p[2]
            else:  # ID
                field_type = GoInbuiltType(p[2])
        else:  # ID DOT ID
            field_type = GoFromModule(p[2], p[4])
        var_list = p[1]

    # Embedded field
    else:
        field_type = GoType("embedded")
        if len(p) == 6:
            var_list = [GoDeref(GoFromModule(p[2], p[4]))]
        elif len(p) == 5:
            var_list = [GoFromModule(p[1], p[3])]
        elif len(p) == 4:
            var_list = [GoDeref(GoVar(p[2]))]
        else:
            var_list = [GoVar(p[1])]

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
    """
    p[0] = GoPointType(p[2])


def p_FunctionType(p):
    """FunctionType : FUNC Signature
    """
    p[0] = GoFuncType(*p[1])


def p_Signature(p):
    """Signature : Parameters
                 | Parameters Result
    """
    # First element is Parameters, second is Result
    if len(p) == 2:  # No result given
        p[0] = (p[1], None)
    else:
        p[0] = (p[1], p[2])


def p_Result(p):
    """Result : Parameters
              | Type
              | ID
              | ID DOT ID
    """
    if type(p[1]) is list:  # Parameters
        p[0] = p[1]
    else:
        if isinstance(p[1], GoType) or isinstance(p[1], GoFromModule):  # Type
            dtype = p[1]
        elif len(p) == 4:  # ID DOT ID
            dtype = GoFromModule(p[1], p[3])
        else:  # ID
            dtype = GoInbuiltType(p[1])
        p[0] = [GoParam(dtype=dtype)]


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
        p[0] = p[1] + p[3]


def p_ParameterDecl(p):
    """ParameterDecl : TRIDOT Type
                     | TRIDOT ID DOT ID
                     | TRIDOT ID
                     | IdentifierList TRIDOT Type
                     | IdentifierList TRIDOT ID DOT ID
                     | IdentifierList TRIDOT ID
                     | ID TRIDOT Type
                     | ID TRIDOT ID DOT ID
                     | ID TRIDOT ID
                     | IdentifierList Type
                     | IdentifierList ID DOT ID
                     | IdentifierList ID
                     | ID Type
                     | ID ID DOT ID
                     | ID ID
    """
    # Remove support for variadic params
    for i, item in enumerate(p):
        if type(item) is LexToken and item.type == "TRIDOT":
            del p[i]

    if isinstance(p[2], GoType) or isinstance(p[2], GoFromModule):  # Type
        dtype = p[2]
    elif len(p) == 5:  # ID DOT ID is type
        dtype = GoFromModule(p[2], p[4])
    else:  # ID is type
        dtype = GoInbuiltType(p[2])

    if type(p[1]) is list:  # IdentifierList
        p[0] = [GoParam(name=identifier, dtype=dtype) for identifier in p[1]]
    else:  # ID
        p[0] = [GoParam(name=p[1], dtype=dtype)]


def p_InterfaceType(p):
    """InterfaceType : INTERFACE LCURLBR MethodSpecList RCURLBR
    """
    p[0] = GoInterfaceType(p[3])


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
        p[0] = GoInbuiltType(p[1])


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

    if isinstance(p[2], GoType):  # Type
        dtype = p[2]
    elif len(p) == 7:  # ID DOT ID
        dtype = GoFromModule(p[2], p[4])
    elif len(p) == 5:  # ID
        dtype = GoInbuiltType(p[2], p[4])
    else:  # Type-less
        dtype = None

    if type(p[len(p) - 1]) is list:  # ExpressionList
        expression = p[len(p) - 1]
    else:  # Expression
        expression = [p[len(p) - 1]]

    p[0] = GoConstSpec(id_list, dtype, expression)


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


def p_ExpressionListBot(p):
    """ExpressionListBot : empty
                         | ExpressionList
    """
    if p[1] is None:  # empty
        p[0] = []
    else:
        p[0] = p[1]


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
    if isinstance(p[3], GoType):
        dtype = p[3]
    elif len(p) == 6:
        dtype = GoFromModule(p[3], p[5])
    else:
        dtype = GoInbuiltType(p[3])
    p[0] = GoTypeDefAlias("alias", p[1], dtype)


def p_TypeDef(p):
    """TypeDef : ID Type
               | ID ID DOT ID
               | ID ID
    """
    if isinstance(p[2], GoType):
        dtype = p[2]
    elif len(p) == 5:
        dtype = GoFromModule(p[2], p[4])
    else:
        dtype = GoInbuiltType(p[2])
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

    if isinstance(p[2], GoType):  # Type
        dtype = p[2]
    elif len(p) == 6:  # ID DOT ID
        dtype = GoFromModule(p[2], p[4])
    elif p.type == "ID":  # LexToken with type "ID"
        dtype = GoInbuiltType(p[2])
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
    """ShortVarDecl : IdentifierList SHDECL ExpressionList
                    | IdentifierList SHDECL Expression
                    | ID SHDECL ExpressionList
                    | ID SHDECL Expression
    """
    if type(p[1]) is list:  # IdentifierList
        id_list = p[1]
    else:
        id_list = [p[1]]

    if type(p[3]) is list:
        expressions = p[1]
    else:
        expressions = [p[1]]

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
    """Operand  : Literal
                | MethodExpr
                | LBRACK Expression RBRACK
    """
    if len(p) == 2:
    	p[0] = p[1]
    else:
    	p[0] = p[2]


def p_Literal(p):
    """Literal  : BasicLit
                | FunctionLit
    """
    p[0] = p[1]


def p_BasicLit(p):
    """BasicLit : INT
                | FLOAT
                | IMAG
                | STRING
                | RUNE
    """
    p[0] = p[1]

def p_FunctionLit(p):
    """FunctionLit : FUNC Function
    """
    p[0] = GoFunc(p[1], p[2])



def p_PrimaryExpr(p):
    """PrimaryExpr : Operand
                   | ID
                   | PrimaryExpr Selector
                   | PrimaryExpr Index
                   | PrimaryExpr Arguments
    """
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[0] = GoPrimaryExpr(p[1], p[2])


def p_Selector(p):
    """Selector : DOT ID
    """
    p[0] = (p[1], p[2])


def p_Index(p):
    """Index : LSQBRACK Expression RSQBRACK
    """
    p[0] = p[2]

#XXX
def p_Arguments(p):
    """Arguments : LBRACK RBRACK
                 | LBRACK ExpressionList TRIDOT RBRACK
                 | LBRACK Expression TRIDOT RBRACK
                 | LBRACK ExpressionList RBRACK
                 | LBRACK Expression RBRACK
                 | LBRACK Type TRIDOT RBRACK
                 | LBRACK Type RBRACK
                 | LBRACK Type COMMA ExpressionList  TRIDOT RBRACK
                 | LBRACK Type COMMA ExpressionList  RBRACK
                 | LBRACK Type COMMA Expression TRIDOT RBRACK
                 | LBRACK Type COMMA Expression RBRACK
                 | LBRACK ID TRIDOT RBRACK
                 | LBRACK ID RBRACK %prec LBRACK
                 | LBRACK ID COMMA ExpressionList  TRIDOT RBRACK
                 | LBRACK ID COMMA ExpressionList  RBRACK
                 | LBRACK ID COMMA Expression TRIDOT RBRACK
                 | LBRACK ID COMMA Expression RBRACK
                 | LBRACK ID DOT ID TRIDOT RBRACK
                 | LBRACK ID DOT ID RBRACK
                 | LBRACK ID DOT ID COMMA ExpressionList  TRIDOT RBRACK
                 | LBRACK ID DOT ID COMMA ExpressionList  RBRACK
                 | LBRACK ID DOT ID COMMA Expression TRIDOT RBRACK
                 | LBRACK ID DOT ID COMMA Expression RBRACK
                 | LBRACK ExpressionList TRIDOT COMMA RBRACK
                 | LBRACK Expression TRIDOT COMMA RBRACK
                 | LBRACK ExpressionList COMMA RBRACK
                 | LBRACK Expression COMMA RBRACK
                 | LBRACK Type TRIDOT COMMA RBRACK
                 | LBRACK Type COMMA RBRACK
                 | LBRACK Type COMMA ExpressionList  TRIDOT COMMA RBRACK
                 | LBRACK Type COMMA ExpressionList  COMMA RBRACK
                 | LBRACK Type COMMA Expression TRIDOT COMMA RBRACK
                 | LBRACK Type COMMA Expression COMMA RBRACK
                 | LBRACK ID TRIDOT COMMA RBRACK
                 | LBRACK ID COMMA RBRACK
                 | LBRACK ID COMMA ExpressionList  TRIDOT COMMA RBRACK
                 | LBRACK ID COMMA ExpressionList  COMMA RBRACK
                 | LBRACK ID COMMA Expression TRIDOT COMMA RBRACK
                 | LBRACK ID COMMA Expression COMMA RBRACK
                 | LBRACK ID DOT ID TRIDOT COMMA RBRACK
                 | LBRACK ID DOT ID COMMA RBRACK
                 | LBRACK ID DOT ID COMMA ExpressionList  TRIDOT COMMA RBRACK
                 | LBRACK ID DOT ID COMMA ExpressionList  COMMA RBRACK
                 | LBRACK ID DOT ID COMMA Expression TRIDOT COMMA RBRACK
                 | LBRACK ID DOT ID COMMA Expression COMMA RBRACK
    """



def p_MethodExpr(p):
    """MethodExpr : ReceiverType DOT ID   %prec ID
                  | ID DOT ID        %prec ID
                  | ID DOT ID DOT ID
    """
    if len(p) == 4:
        p[0] = GoFromModule(p[1], p[3])
    else:
        p[0] = GoFromModule(GoFromModule(p[1], p[3]), p[5])


def p_ReceiverType(p):
    """ReceiverType : LBRACK MULT ID DOT ID RBRACK
                    | LBRACK MULT ID RBRACK
                    | LBRACK ReceiverType RBRACK
    """
    if len(p) == 7:
    	p[0] = GoDeref(GoFromModule(p[3], p[5]))
    elif len(p) == 5:
        p[0] = GoDeref(p[3])
    else:
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
    p[0] = GoExpression(p[1], p[3] ,p[2])


def p_ExpressionBot(p):
    """ExpressionBot : empty
                     | Expression
    """
    p[0] = p[1]


def p_ExpressionBotList(p):
    """ExpressionBotList : COMMA Expression
                         | COMMA Expression ExpressionBotList
    """
    if len(p) == 3:
    	p[0] = [p[2]]
    else:
    	p[0] = [p[2]] + p[3]


#XXX
def p_UnaryExpr(p):
    """UnaryExpr : PrimaryExpr
                 | unary_op UnaryExpr
    """


def p_addmul_op(p):
    """addmul_op : empty
                 | add_op
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
    """unary_op   : PLUS
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
    p[0] = GoIncDec(p[1], p[2])


def p_Assignment(p):
    """Assignment : Expression assign_op Expression
                  | ExpressionList assign_op Expression
                  | Expression assign_op ExpressionList
                  | ExpressionList assign_op ExpressionList
    """
    if type(p[1]) is list:
        if type(p[3]) is list:
            p[0] = GoAssign(p[1], p[3], p[2])
        else:
            p[0] = GoAssign(p[1], [p[3]], p[2])
    else:
        if type(p[3]) is list:
            p[0] = GoAssign([p[1]], p[3], p[2])
        else:
            p[0] = GoAssign([p[1]], [p[3]], p[2])


def p_assign_op(p):
    """assign_op : addmul_op ASSIGN
    """
    p[0] = GoAddMul(p[1], p[2])

#XXX
def p_IfStmt(p):
    """IfStmt : IF Expression Block ElseBot
              | IF SimpleStmt SEMICOLON Expression Block ElseBot
    """
    if len(p) == 5:
        p[0] = GoIf([p[2]], p[3], p[4])
    else:
        p[0] = GoIf([p[2],p[3],p[4]], p[5], p[6])


def p_ElseBot(p):
    """ElseBot : empty
               | ELSE ElseTail
    """
    p[0] = p[2]



def p_ElseTail(p):
    """ElseTail : IfStmt
                | Block
    """
    p[0] = p[1]

def p_SwitchStmt(p):
    """SwitchStmt : ExprSwitchStmt
    """
    p[0] = p[1]


def p_ExprSwitchStmt(p):
    """ExprSwitchStmt : SWITCH SimpleStmt SEMICOLON  ExpressionBot LCURLBR ExprCaseClauseList RCURLBR
                      | SWITCH ExpressionBot LCURLBR ExprCaseClauseList RCURLBR
    """



def p_ExprCaseClauseList(p):
    """ExprCaseClauseList : empty
                          | ExprCaseClauseList ExprCaseClause
    """


def p_ExprCaseClause(p):
    """ExprCaseClause : ExprSwitchCase COLON StatementList
    """


def p_ExprSwitchCase(p):
    """ExprSwitchCase : CASE ExpressionList
                      | DEFAULT
                      | CASE Expression
    """


def p_ForStmt(p):
    """ForStmt : FOR ExpressionBot Block
    """
    

def p_ReturnStmt(p):
    """ReturnStmt : RETURN ExpressionListBot
                  | RETURN Expression
    """
    p[0] = GoControl(p[1], p[2])

def p_BreakStmt(p):
    """BreakStmt : BREAK ID
    """
    p[0] = GoControl(p[1], p[2])

def p_ContinueStmt(p):
    """ContinueStmt : CONTINUE ID
    """
    p[0] = GoControl(p[1], p[2])

def p_GotoStmt(p):
    """GotoStmt : GOTO ID
    """
    p[0] = GoControl(p[1], p[2])


def p_FallthroughStmt(p):
    """FallthroughStmt : FALLTHROUGH
    """
    p[0] = p[1]


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

if __name__ == "__main__":
    argparser = ArgumentParser(description="Parser for Go")
    argparser.add_argument("input", type=str, help="input file")
    argparser.add_argument(
        "-o", "--output", type=str, default=None, help="output file name"
    )
    argparser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug output"
    )
    args = argparser.parse_args()
    if args.output is None:
        args.output = args.input.split("/")[-1] + ".dot"

    with open(args.input, "r") as go:
        input_text = go.read()
    lexer.filename = args.input
    lexer.lines = input_text.split("\n")
    result = parser.parse(input_text)

    if args.verbose:
        print(result)

    with open(args.output, "w") as outf:
        outf.write(str(result))
    print('Output file "{}" generated'.format(args.output))
