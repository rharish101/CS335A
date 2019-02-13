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
    if len(p) == 1:
        p[0] = p[1]
    elif len(p) == 3:
        if type(p) is str:
            p[0] = GoInbuiltType(p[1])
        else:
            p[0] = p[2]
    else:
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
    if len(p) == 5:
        if type(p[4]) is str:
            arr_type = GoInbuiltType(p[4])
        else:
            arr_type = p[4]
    else:
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
        if len(p) == 3:
            if type(p[2]) is str:
                field_type = GoInbuiltType(p[2])
            else:
                field_type = p[2]
        else:
            field_type = GoFromModule(p[2], p[4])
        var_list = p[1]

    # Embedded field
    else:
        field_type = GoType("embedded")
        if len(p) == 5:
            var_list = [GoDeref(GoFromModule(p[1], p[3]))]
        elif len(p) == 5:
            var_list = [GoFromModule(p[1], p[3])]
        elif len(p) == 5:
            var_list = [GoDeref(GoVar(p[1]))]
        else:
            var_list = [GoVar(p[1])]

    p[0] = GoStructField(var_list, field_type, tag)


def p_FieldDeclList(p):
    """FieldDeclList : empty
                     | FieldDeclList FieldDecl SEMICOLON
    """
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_TagTop(p):
    """TagTop : empty
              | STRING
    """
    if p[1] is None:
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
    p[0] = (p[1], p[2])


def p_Result(p):
    """Result : Parameters
              | Type
              | ID
              | ID DOT ID
    """
    if type(p[1]) is list:
        p[0] = p[1]
    else:
        if isinstance(p[1], GoType) or isinstance(p[1], GoFromModule):
            dtype = p[1]
        elif len(p) == 2:
            dtype = GoFromModule(p[1], p[3])
        else:
            dtype = GoInbuiltType(p[1])
        p[0] = [GoParam(dtype=dtype)]


def p_Parameters(p):
    """Parameters : LBRACK RBRACK
                  | LBRACK ParameterList RBRACK
                  | LBRACK ParameterList COMMA RBRACK
    """
    if len(p) == 3:
        p[0] = []
    else:
        p[0] = p[2]


def p_ParameterList(p):
    """ParameterList : ParameterDecl
                     | ParameterList COMMA ParameterDecl
    """
    if len(p) == 2:
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

    if isinstance(p[2], GoType) or isinstance(p[2], GoFromModule):
        dtype = p[2]
    elif len(p) == 5:
        dtype = GoFromModule(p[2], p[4])
    else:
        dtype = GoInbuiltType(p[2])

    if type(p[1]) is list:
        p[0] = [GoParam(name=identifier, dtype=dtype) for identifier in p[1]]
    else:
        p[0] = [GoParam(name=p[1], dtype=dtype)]


def p_InterfaceType(p):
    """InterfaceType : INTERFACE LCURLBR MethodSpecList RCURLBR
    """
    p[0] = GoInterfaceType(p[3])


def p_MethodSpecList(p):
    """MethodSpecList : empty
                      | MethodSpecList MethodSpec SEMICOLON
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_MethodSpec(p):
    """MethodSpec : ID Signature
                  | ID DOT ID
                  | ID
    """
    if len(p) == 3:
        p[0] = GoMethodFunc(p[1], *p[2])
    elif len(p) == 4:
        p[0] = GoFromModule(p[1], p[3])
    else:
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
    if len(p) == 2:
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


def p_TopLevelDecl(p):
    """TopLevelDecl : Declaration
                    | FunctionDecl
                    | MethodDecl
    """


def p_TopLevelDeclList(p):
    """TopLevelDeclList : TopLevelDecl SEMICOLON TopLevelDeclList
                        | empty
    """


def p_ConstDecl(p):
    """ConstDecl  : CONST LBRACK ConstSpecList RBRACK
                  | CONST ConstSpec
                  | CONST ID
    """


def p_ConstSpec(p):
    """ConstSpec : IdentifierList
                 | IdentifierList Type ASSIGN Expression
                 | ID Type ASSIGN Expression
                 | IdentifierList Type ASSIGN ExpressionList
                 | ID Type ASSIGN ExpressionList
                 | IdentifierList ID DOT ID ASSIGN Expression
                 | ID ID DOT ID ASSIGN Expression
                 | IdentifierList ID DOT ID ASSIGN ExpressionList
                 | ID ID DOT ID ASSIGN ExpressionList
                 | IdentifierList ID ASSIGN Expression
                 | ID ID ASSIGN Expression
                 | IdentifierList ID ASSIGN ExpressionList
                 | ID ID ASSIGN ExpressionList
                 | IdentifierList ASSIGN Expression
                 | ID ASSIGN Expression
                 | IdentifierList ASSIGN ExpressionList
                 | ID ASSIGN ExpressionList
    """


def p_ConstSpecList(p):
    """ConstSpecList : empty
                     | ConstSpecList ConstSpec SEMICOLON
                     | ConstSpecList ID SEMICOLON
    """


def p_IdentifierList(p):
    """IdentifierList : ID IdentifierBotList
    """


def p_IdentifierBotList(p):
    """IdentifierBotList : COMMA ID
                         | IdentifierBotList COMMA ID
    """


def p_ExpressionList(p):
    """ExpressionList : Expression ExpressionBotList
    """


def p_ExpressionListBot(p):
    """ExpressionListBot : empty
                         | ExpressionList
    """


def p_TypeDecl(p):
    """TypeDecl : TYPE TypeSpecTopList
    """


def p_TypeSpec(p):
    """TypeSpec : AliasDecl
                | TypeDef
    """


def p_TypeSpecList(p):
    """TypeSpecList : empty
                    | TypeSpecList TypeSpec SEMICOLON
    """


def p_TypeSpecTopList(p):
    """TypeSpecTopList : TypeSpec
                       | LBRACK TypeSpecList  RBRACK
    """


def p_AliasDecl(p):
    """AliasDecl : ID ASSIGN Type
                 | ID ASSIGN ID DOT ID
                 | ID ASSIGN ID
    """


def p_TypeDef(p):
    """TypeDef : ID Type
               | ID ID
               | ID ID DOT ID
    """


def p_VarDecl(p):
    """VarDecl : VAR VarSpecTopList
    """


def p_VarSpec(p):
    """VarSpec : IdentifierList Type VarSpecMid
               | ID Type VarSpecMid
               | IdentifierList ID VarSpecMid
               | ID ID VarSpecMid
               | IdentifierList ID DOT ID VarSpecMid
               | ID ID DOT ID VarSpecMid
               | IdentifierList ASSIGN ExpressionList
               | ID ASSIGN ExpressionList
               | IdentifierList ASSIGN Expression
               | ID ASSIGN Expression
    """


def p_VarSpecMid(p):
    """VarSpecMid : empty
                  | ASSIGN ExpressionList
                  | ASSIGN Expression
    """


def p_VarSpecList(p):
    """VarSpecList : empty
                   | VarSpecList VarSpec SEMICOLON
    """


def p_VarSpecTopList(p):
    """VarSpecTopList : VarSpec
                      | LBRACK VarSpecList RBRACK
    """


def p_ShortVarDecl(p):
    """ShortVarDecl : IdentifierList SHDECL ExpressionList
                    | IdentifierList SHDECL Expression
                    | ID SHDECL ExpressionList
                    | ID SHDECL Expression
    """


def p_FunctionDecl(p):
    """FunctionDecl : FUNC FunctionName FunctionDeclTail
    """


def p_FunctionDeclTail(p):
    """FunctionDeclTail : Function
                        | Signature
    """


def p_FunctionName(p):
    """FunctionName : ID
    """


def p_Function(p):
    """Function : Signature FunctionBody
    """


def p_FunctionBody(p):
    """FunctionBody : Block
    """


def p_MethodDecl(p):
    """MethodDecl : FUNC Receiver ID FunctionDeclTail
    """


def p_Receiver(p):
    """Receiver : Parameters
    """


# =============================================================================
# EXPRESSIONS
# =============================================================================


def p_Operand(p):
    """Operand  : Literal
                | MethodExpr
                | LBRACK Expression RBRACK
    """


def p_Literal(p):
    """Literal  : BasicLit
                | FunctionLit
    """


def p_BasicLit(p):
    """BasicLit : INT
                | FLOAT
                | IMAG
                | STRING
                | RUNE
    """


def p_FunctionLit(p):
    """FunctionLit : FUNC Function
    """


def p_PrimaryExpr(p):
    """PrimaryExpr : Operand
                   | ID
                   | PrimaryExpr Selector
                   | PrimaryExpr Index
                   | PrimaryExpr Arguments
    """


def p_Selector(p):
    """Selector : DOT ID
    """


def p_Index(p):
    """Index : LSQBRACK Expression RSQBRACK
    """


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


def p_ReceiverType(p):
    """ReceiverType : LBRACK MULT ID DOT ID RBRACK
                    | LBRACK MULT ID RBRACK
                    | LBRACK ReceiverType RBRACK
    """


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


def p_ExpressionBot(p):
    """ExpressionBot : empty
                     | Expression
    """


def p_ExpressionBotList(p):
    """ExpressionBotList : COMMA Expression
                         | COMMA Expression ExpressionBotList
    """


def p_UnaryExpr(p):
    """UnaryExpr : PrimaryExpr
                 | unary_op UnaryExpr
    """


def p_addmul_op(p):
    """addmul_op : empty
                 | add_op
                 | mul_op
    """


def p_add_op(p):
    """add_op : PLUS
              | MINUS
              | BITOR
              | BITXOR
    """


def p_mul_op(p):
    """mul_op  : MULT
               | DIV
               | MODULO
               | LSHIFT
               | RSHIFT
               | BITAND
               | BITCLR
    """


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


def p_SimpleStmt(p):
    """SimpleStmt : Expression
                  | Assignment
                  | ShortVarDecl
                  | IncDecStmt
    """


def p_IncDecStmt(p):
    """IncDecStmt : Expression INCR
                  | Expression DECR
    """


def p_Assignment(p):
    """Assignment : Expression assign_op Expression
                  | ExpressionList assign_op Expression
                  | Expression assign_op ExpressionList
                  | ExpressionList assign_op ExpressionList
    """


def p_assign_op(p):
    """assign_op : addmul_op ASSIGN
    """


def p_IfStmt(p):
    """IfStmt : IF Expression Block ElseBot
              | IF SimpleStmt SEMICOLON  Expression Block ElseBot
    """


def p_ElseBot(p):
    """ElseBot : empty
               | ELSE ElseTail
    """


def p_ElseTail(p):
    """ElseTail : IfStmt
                | Block
    """


def p_SwitchStmt(p):
    """SwitchStmt : ExprSwitchStmt
    """


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


def p_BreakStmt(p):
    """BreakStmt : BREAK ID
    """


def p_ContinueStmt(p):
    """ContinueStmt : CONTINUE ID
    """


def p_GotoStmt(p):
    """GotoStmt : GOTO ID
    """


def p_FallthroughStmt(p):
    """FallthroughStmt : FALLTHROUGH
    """


# =============================================================================
# PACKAGES
# =============================================================================


def p_SourceFile(p):
    """SourceFile : PACKAGE ID SEMICOLON ImportDeclList TopLevelDeclList
    """


def p_ImportDecl(p):
    """ImportDecl : IMPORT LBRACK ImportSpecList RBRACK
                  | IMPORT ImportSpec
    """


def p_ImportDeclList(p):
    """ImportDeclList : ImportDecl SEMICOLON ImportDeclList
                      | empty
    """


def p_ImportSpec(p):
    """ImportSpec : DOT STRING
                  | ID STRING
                  | empty STRING
    """


def p_ImportSpecList(p):
    """ImportSpecList : ImportSpec SEMICOLON ImportSpecList
                      | empty
    """


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
