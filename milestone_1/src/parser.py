#!/usr/bin/env python3
"""Parser for Go."""
from ply import yacc
from argparse import ArgumentParser
from lexer import *

parsed = []

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


def p_SourceFile(p):
    """SourceFile : PACKAGE ID SEMICOLON ImportDeclList TopLevelDeclList
    """
    parsed.append(p.slice)


def p_ImportDeclList(p):
    """ImportDeclList : ImportDecl SEMICOLON ImportDeclList
                      | empty
    """
    parsed.append(p.slice)


def p_TopLevelDeclList(p):
    """TopLevelDeclList : TopLevelDecl SEMICOLON TopLevelDeclList
                        | empty
    """
    parsed.append(p.slice)


def p_TopLevelDecl(p):
    """TopLevelDecl : Declaration
                    | FunctionDecl
                    | MethodDecl
    """
    parsed.append(p.slice)


def p_ImportDecl(p):
    """ImportDecl : IMPORT LBRACK ImportSpecList RBRACK
                  | IMPORT ImportSpec
    """
    parsed.append(p.slice)


def p_ImportSpecList(p):
    """ImportSpecList : ImportSpec SEMICOLON ImportSpecList
                      | empty
    """
    parsed.append(p.slice)


def p_ImportSpec(p):
    """ImportSpec : DOT string_lit
                  | ID string_lit
                  | empty string_lit
    """
    parsed.append(p.slice)


def p_Block(p):
    """Block : LCURLBR StatementList RCURLBR
    """
    parsed.append(p.slice)


def p_StatementList(p):
    """StatementList : Statement SEMICOLON StatementList
                     | empty
    """
    parsed.append(p.slice)


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
    parsed.append(p.slice)


def p_Declaration(p):
    """Declaration : ConstDecl
                   | TypeDecl
                   | VarDecl
    """
    parsed.append(p.slice)


def p_ConstDecl(p):
    """ConstDecl  : CONST LBRACK ConstSpecList RBRACK
                  | CONST ConstSpec
                  | CONST ID
    """
    parsed.append(p.slice)


def p_ConstSpecList(p):
    """ConstSpecList : empty
                     | ConstSpecList ConstSpec SEMICOLON
                     | ConstSpecList ID SEMICOLON
    """
    parsed.append(p.slice)


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
    parsed.append(p.slice)


def p_IdentifierList(p):
    """IdentifierList : ID IdentifierBotList
    """
    parsed.append(p.slice)


def p_IdentifierBotList(p):
    """IdentifierBotList : COMMA ID
                         | IdentifierBotList COMMA ID
    """
    parsed.append(p.slice)


def p_ExpressionList(p):
    """ExpressionList : Expression ExpressionBotList
    """
    parsed.append(p.slice)


def p_ExpressionBotList(p):
    """ExpressionBotList : COMMA Expression
                         | COMMA Expression ExpressionBotList
    """
    parsed.append(p.slice)


def p_TypeDecl(p):
    """TypeDecl : TYPE TypeSpecTopList
    """
    parsed.append(p.slice)


def p_TypeSpecTopList(p):
    """TypeSpecTopList : TypeSpec
                       | LBRACK TypeSpecList  RBRACK
    """
    parsed.append(p.slice)


def p_TypeSpecList(p):
    """TypeSpecList : empty
                    | TypeSpecList TypeSpec SEMICOLON
    """
    parsed.append(p.slice)


def p_TypeSpec(p):
    """TypeSpec : AliasDecl
                | TypeDef
    """
    parsed.append(p.slice)


def p_AliasDecl(p):
    """AliasDecl : ID ASSIGN Type
                 | ID ASSIGN ID DOT ID
                 | ID ASSIGN ID
    """
    parsed.append(p.slice)


def p_TypeDef(p):
    """TypeDef : ID Type
               | ID ID
               | ID ID DOT ID
    """
    parsed.append(p.slice)


def p_Type(p):
    """Type : TypeLit
            | LBRACK ID RBRACK
            | LBRACK Type RBRACK
            | LBRACK ID DOT ID RBRACK
    """
    parsed.append(p.slice)


# def p_TypeName(p):
#     '''TypeName  : ID DOT ID
#     '''
#     parsed.append(p.slice)

# def p_QualifiedIdent(p):
#     '''QualifiedIdent : ID DOT ID
#     '''
#     parsed.append(p.slice)


def p_TypeLit(p):
    """TypeLit : ArrayType
               | StructType
               | InterfaceType
               | FunctionType
    """
    parsed.append(p.slice)


def p_ArrayType(p):
    """ArrayType : LSQBRACK ArrayLength RSQBRACK Type
                 | LSQBRACK ArrayLength RSQBRACK ID
                 | LSQBRACK ArrayLength RSQBRACK ID DOT ID
    """
    parsed.append(p.slice)


def p_ArrayLength(p):
    """ArrayLength : Expression
    """
    parsed.append(p.slice)


def p_StructType(p):
    """StructType : STRUCT LCURLBR FieldDeclList RCURLBR
    """
    parsed.append(p.slice)


def p_FieldDeclList(p):
    """FieldDeclList : empty
                 | FieldDeclList FieldDecl SEMICOLON
    """
    parsed.append(p.slice)


def p_FieldDecl(p):
    """FieldDecl : IdentifierList Type TagTop
                 | IdentifierList ID TagTop
                 | IdentifierList ID DOT ID TagTop
                 | MULT ID DOT ID TagTop
                 | ID DOT ID TagTop
                 | MULT ID TagTop
                 | ID TagTop
    """
    parsed.append(p.slice)


def p_TagTop(p):
    """TagTop : empty
              | Tag
    """
    parsed.append(p.slice)


def p_Tag(p):
    """Tag : string_lit
    """
    parsed.append(p.slice)


def p_FunctionType(p):
    """FunctionType : FUNC Signature
    """
    parsed.append(p.slice)


def p_InterfaceType(p):
    """InterfaceType : INTERFACE LCURLBR MethodSpecList RCURLBR
    """
    parsed.append(p.slice)


def p_MethodSpecList(p):
    """MethodSpecList : empty
                 | MethodSpecList MethodSpec SEMICOLON
    """
    parsed.append(p.slice)


def p_MethodSpec(p):
    """MethodSpec : ID Signature
                  | ID DOT ID
                  | ID
    """


# Signature      = Parameters [ Result ] .
# Result         = Parameters | Type .
# Parameters     = "(" [ ParameterList [ "," ] ] ")" .
# ParameterList  = ParameterDecl { "," ParameterDecl } .
# ParameterDecl  = [ IdentifierList ] [ "..." ] Type .


def p_Signature(p):
    """Signature : Parameters
                 | Parameters Result
    """
    parsed.append(p.slice)


def p_Result(p):
    """Result : Parameters
              | Type
              | ID
              | ID DOT ID
    """
    parsed.append(p.slice)


def p_Parameters(p):
    """Parameters : LBRACK RBRACK
                  | LBRACK ParameterList RBRACK
                  | LBRACK ParameterList COMMA RBRACK

    """
    parsed.append(p.slice)


def p_ParameterList(p):
    """ParameterList : ParameterDecl
                     | ParameterList COMMA ParameterDecl
    """
    parsed.append(p.slice)



def p_ParameterDecl(p):
    """ParameterDecl : TRIDOT Type
                     | IdentifierList Type
                     | IdentifierList TRIDOT Type
                     | ID Type
                     | ID TRIDOT Type
                     | TRIDOT ID
                     | IdentifierList ID
                     | IdentifierList TRIDOT ID
                     | ID ID
                     | ID TRIDOT ID
                     | TRIDOT ID DOT ID
                     | IdentifierList ID DOT ID
                     | IdentifierList TRIDOT ID DOT ID
                     | ID ID DOT ID
                     | ID TRIDOT ID DOT ID
    """
    parsed.append(p.slice)


def p_VarDecl(p):
    """VarDecl : VAR VarSpecTopList
    """
    parsed.append(p.slice)


def p_VarSpecTopList(p):
    """VarSpecTopList : VarSpec
                      | LBRACK VarSpecList RBRACK
    """
    parsed.append(p.slice)


def p_VarSpecList(p):
    """VarSpecList : empty
                   | VarSpecList VarSpec SEMICOLON
    """
    parsed.append(p.slice)


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
    parsed.append(p.slice)


def p_VarSpecMid(p):
    """VarSpecMid : empty
                  | ASSIGN ExpressionList
                  | ASSIGN Expression
    """
    parsed.append(p.slice)


def p_FunctionDecl(p):
    """FunctionDecl : FUNC FunctionName FunctionDeclTail
    """
    parsed.append(p.slice)


def p_FunctionDeclTail(p):
    """FunctionDeclTail : Function
                        | Signature
    """
    parsed.append(p.slice)


def p_FunctionName(p):
    """FunctionName : ID
    """
    parsed.append(p.slice)


def p_Function(p):
    """Function : Signature FunctionBody
    """
    parsed.append(p.slice)


def p_FunctionBody(p):
    """FunctionBody : Block
    """
    parsed.append(p.slice)


def p_MethodDecl(p):
    """MethodDecl : FUNC Receiver ID FunctionDeclTail
    """
    parsed.append(p.slice)


def p_Receiver(p):
    """Receiver : Parameters
    """
    parsed.append(p.slice)


def p_SimpleStmt(p):
    """SimpleStmt : Expression
                  | Assignment
                  | ShortVarDecl
    """
    parsed.append(p.slice)


# def p_ExpressionStmt(p):
#     '''ExpressionStmt : Expression
#     '''
#     parsed.append(p.slice)


def p_ShortVarDecl(p):
    """ShortVarDecl : IdentifierList SHDECL ExpressionList
                    | IdentifierList SHDECL Expression
                    | ID SHDECL ExpressionList
                    | ID SHDECL Expression
    """
    parsed.append(p.slice)


def p_Assignment(p):
    """Assignment : Expression assign_op Expression
                  | ExpressionList assign_op Expression
                  | Expression assign_op ExpressionList
                  | ExpressionList assign_op ExpressionList
    """
    parsed.append(p.slice)


def p_assign_op(p):
    """assign_op : addmul_op ASSIGN
    """
    parsed.append(p.slice)


def p_addmul_op(p):
    """addmul_op : empty
                 | add_op
                 | mul_op
    """
    parsed.append(p.slice)


def p_IfStmt(p):
    """IfStmt : IF Expression Block elseBot
              | IF SimpleStmt SEMICOLON  Expression Block elseBot
    """
    parsed.append(p.slice)


def p_elseBot(p):
    """elseBot : empty
               | ELSE elseTail
    """
    parsed.append(p.slice)


def p_elseTail(p):
    """elseTail : IfStmt
                | Block
    """
    parsed.append(p.slice)


def p_SwitchStmt(p):
    """SwitchStmt : ExprSwitchStmt
    """
    parsed.append(p.slice)


def p_ExprSwitchStmt(p):
    """ExprSwitchStmt : SWITCH SimpleStmt SEMICOLON  ExpressionBot LCURLBR ExprCaseClauseList RCURLBR
                      | SWITCH ExpressionBot LCURLBR ExprCaseClauseList RCURLBR
    """
    parsed.append(p.slice)


def p_ExprCaseClauseList(p):
    """ExprCaseClauseList : empty
                          | ExprCaseClauseList ExprCaseClause
    """
    parsed.append(p.slice)


def p_ExprCaseClause(p):
    """ExprCaseClause : ExprSwitchCase COLON StatementList
    """
    parsed.append(p.slice)


def p_ExprSwitchCase(p):
    """ExprSwitchCase : CASE ExpressionList
                      | DEFAULT
                      | CASE Expression
    """
    parsed.append(p.slice)


def p_ForStmt(p):
    """ForStmt : FOR ExpressionBot Block
    """
    parsed.append(p.slice)


def p_ExpressionBot(p):
    """ExpressionBot : empty
                     | Expression
    """
    parsed.append(p.slice)


def p_ReturnStmt(p):
    """ReturnStmt : RETURN ExpressionListBot
                  | RETURN Expression
    """
    parsed.append(p.slice)


def p_ExpressionListBot(p):
    """ExpressionListBot : empty
                         | ExpressionList
    """
    parsed.append(p.slice)


def p_BreakStmt(p):
    """BreakStmt : BREAK ID
    """
    parsed.append(p.slice)


def p_ContinueStmt(p):
    """ContinueStmt : CONTINUE ID
    """
    parsed.append(p.slice)


def p_GotoStmt(p):
    """GotoStmt : GOTO ID
    """
    parsed.append(p.slice)


def p_FallthroughStmt(p):
    """FallthroughStmt : FALLTHROUGH
    """
    parsed.append(p.slice)


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
    parsed.append(p.slice)


def p_UnaryExpr(p):
    """UnaryExpr : PrimaryExpr
                 | unary_op UnaryExpr
    """
    parsed.append(p.slice)


# def p_binary_op(p):
#     '''binary_op  : LOGOR
#                  | LOGAND
#                  | rel_op
#                  | add_op
#                  | mul_op
#     '''
#     parsed.append(p.slice)

# def p_rel_op(p):
#     '''rel_op : EQUALS
#                  | NOTEQ
#                  | LESS
#                  | LESSEQ
#                  | GREAT
#                  | GREATEQ
#     '''
#     parsed.append(p.slice)


def p_add_op(p):
    """add_op : PLUS
              | MINUS
              | BITOR
              | BITXOR
    """
    parsed.append(p.slice)


def p_mul_op(p):
    """mul_op  : MULT
               | DIV
               | MODULO
               | LSHIFT
               | RSHIFT
               | BITAND
               | BITCLR
    """
    parsed.append(p.slice)


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
    parsed.append(p.slice)


def p_PrimaryExpr(p):
    """PrimaryExpr : Operand
                   | ID
                   | PrimaryExpr Selector
                   | PrimaryExpr Index
                   | PrimaryExpr Arguments
    """
    parsed.append(p.slice)


def p_Operand(p):
    """Operand  : Literal
                | MethodExpr
                | LBRACK Expression RBRACK
    """
    parsed.append(p.slice)


def p_Literal(p):
    """Literal  : BasicLit
                | FunctionLit
    """
    parsed.append(p.slice)


def p_BasicLit(p):
    """BasicLit : int_lit
                | float_lit
                | imag_lit
                | string_lit
                | rune_lit
    """
    parsed.append(p.slice)


def p_int_lit(p):
    """int_lit : INT"""
    parsed.append(p.slice)


def p_float_lit(p):
    """float_lit : FLOAT
    """
    parsed.append(p.slice)


def p_imag_lit(p):
    """imag_lit : IMAG"""
    parsed.append(p.slice)


##########################################
###################################


def p_FunctionLit(p):
    """FunctionLit : FUNC Function
    """
    parsed.append(p.slice)


def p_MethodExpr(p):
    """MethodExpr : ReceiverType DOT ID   %prec ID
                  | ID DOT ID        %prec ID
                  | ID DOT ID DOT ID
    """
    parsed.append(p.slice)


def p_ReceiverType(p):
    """ReceiverType : LBRACK MULT ID DOT ID RBRACK
                    | LBRACK MULT ID RBRACK
                    | LBRACK ReceiverType RBRACK
    """
    parsed.append(p.slice)


def p_Selector(p):
    """Selector : DOT ID
    """
    parsed.append(p.slice)


def p_Index(p):
    """Index : LSQBRACK Expression RSQBRACK
    """
    parsed.append(p.slice)


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
    parsed.append(p.slice)


def p_empty(p):
    "empty :"
    pass


def p_string_lit(p):
    """string_lit : STRING
    """
    parsed.append(p.slice)


def p_rune_lit(p):
    """rune_lit : RUNE
    """
    parsed.append(p.slice)


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
        parser.parse(go.read())

    if args.verbose:
        print(parsed)

    with open(args.output, "w") as outf:
        outf.write(str(parsed))
    print('Output file "{}" generated'.format(args.output))
