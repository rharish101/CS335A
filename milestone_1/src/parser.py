#!/usr/bin/env python3
"""Parser for Go."""
from ply import yacc
from argparse import ArgumentParser
from lexer import *


def p_SourceFile(p):
    """SourceFile : PackageClause SEMICOLON SourceFileRepOne SourceFileRepTwo"""


def p_SourceFileRepOne(p):
    """SourceFileRepOne : SourceFileRepOne ImportDecl SEMICOLON
                        |"""


def p_SourceFileRepTwo(p):
    """SourceFileRepTwo : SourceFileRepTwo TopLevelDecl SEMICOLON
                        |"""


def p_Type(p):
    """Type : TypeName
            | TypeLit
            | LBRACK Type RBRACK"""


def p_TypeName(p):
    """TypeName : ID
                | QualifiedIdent"""


def p_TypeLit(p):
    """TypeLit : ArrayType
               | StructType
               | PointerType
               | FunctionType
               | InterfaceType
               | SliceType
               | MapType
               | ChannelType"""


def p_ArrayType(p):
    """ArrayType : LSQBRACK ArrayLength RSQBRACK ElementType"""


def p_ArrayLength(p):
    """ArrayLength : Expression"""


def p_ElementType(p):
    """ElementType : Type"""


def p_SliceType(p):
    """SliceType : LSQBRACK RSQBRACK ElementType"""


def p_StructType(p):
    """StructType : STRUCT LCURLBR StructTypeRepOne RCURLBR"""


def p_StructTypeRepOne(p):
    """StructTypeRepOne : StructTypeRepOne FieldDecl SEMICOLON
                        |"""


def p_FieldDecl(p):
    """FieldDecl : FieldDeclGroupOne FieldDeclOptOne"""


def p_FieldDeclGroupOne(p):
    """FieldDeclGroupOne : IdentifierList Type
                         | EmbeddedField"""


def p_FieldDeclOptOne(p):
    """FieldDeclOptOne : Tag
                       |"""


def p_EmbeddedField(p):
    """EmbeddedField : EmbeddedFieldOptOne TypeName"""


def p_EmbeddedFieldOptOne(p):
    """EmbeddedFieldOptOne : MULT
                           |"""


def p_Tag(p):
    """Tag : STRING"""


def p_PointerType(p):
    """PointerType : MULT BaseType"""


def p_BaseType(p):
    """BaseType : Type"""


def p_FunctionType(p):
    """FunctionType : FUNC Signature"""


def p_Signature(p):
    """Signature : Parameters SignatureOptOne"""


def p_SignatureOptOne(p):
    """SignatureOptOne : Result
                       |"""


def p_Result(p):
    """Result : Parameters
              | Type"""


def p_Parameters(p):
    """Parameters : LBRACK ParametersOptOne RBRACK"""


def p_ParametersOptOne(p):
    """ParametersOptOne : ParameterList ParametersOptOneOptOne
                        |"""


def p_ParametersOptOneOptOne(p):
    """ParametersOptOneOptOne : COMMA
                              |"""


def p_ParameterList(p):
    """ParameterList : ParameterDecl ParameterListRepOne"""


def p_ParameterListRepOne(p):
    """ParameterListRepOne : ParameterListRepOne COMMA ParameterDecl
                           |"""


def p_ParameterDecl(p):
    """ParameterDecl : ParameterDeclOptOne ParameterDeclOptTwo Type"""


def p_ParameterDeclOptOne(p):
    """ParameterDeclOptOne : IdentifierList
                           |"""


def p_ParameterDeclOptTwo(p):
    """ParameterDeclOptTwo : TRIDOT
                           |"""


def p_InterfaceType(p):
    """InterfaceType : INTERFACE LCURLBR InterfaceTypeRepOne RCURLBR"""


def p_InterfaceTypeRepOne(p):
    """InterfaceTypeRepOne : InterfaceTypeRepOne MethodSpec SEMICOLON
                           |"""


def p_MethodSpec(p):
    """MethodSpec : MethodName Signature
                  | InterfaceTypeName"""


def p_MethodName(p):
    """MethodName : ID"""


def p_InterfaceTypeName(p):
    """InterfaceTypeName : TypeName"""


def p_MapType(p):
    """MapType : MAP LSQBRACK KeyType RSQBRACK ElementType"""


def p_KeyType(p):
    """KeyType : Type"""


def p_ChannelType(p):
    """ChannelType : ChannelTypeGroupOne ElementType"""


def p_ChannelTypeGroupOne(p):
    """ChannelTypeGroupOne : CHAN
                           | CHAN REC
                           | REC CHAN"""


def p_Block(p):
    """Block : LCURLBR StatementList RCURLBR"""


def p_StatementList(p):
    """StatementList : StatementListRepOne"""


def p_StatementListRepOne(p):
    """StatementListRepOne : StatementListRepOne Statement SEMICOLON
                           |"""


def p_Declaration(p):
    """Declaration : ConstDecl
                   | TypeDecl
                   | VarDecl"""


def p_TopLevelDecl(p):
    """TopLevelDecl : Declaration
                    | FunctionDecl
                    | MethodDecl"""


def p_ConstDecl(p):
    """ConstDecl : CONST ConstDeclGroupOne"""


def p_ConstDeclGroupOne(p):
    """ConstDeclGroupOne : ConstSpec
                         | LBRACK ConstDeclGroupOneRepOne RBRACK"""


def p_ConstDeclGroupOneRepOne(p):
    """ConstDeclGroupOneRepOne : ConstDeclGroupOneRepOne ConstSpec SEMICOLON
                               |"""


def p_ConstSpec(p):
    """ConstSpec : IdentifierList ConstSpecOptOne"""


def p_ConstSpecOptOne(p):
    """ConstSpecOptOne : ConstSpecOptOneOptOne ASSIGN ExpressionList
                       |"""


def p_ConstSpecOptOneOptOne(p):
    """ConstSpecOptOneOptOne : Type
                             |"""


def p_IdentifierList(p):
    """IdentifierList : ID IdentifierListRepOne"""


def p_IdentifierListRepOne(p):
    """IdentifierListRepOne : IdentifierListRepOne COMMA ID
                            |"""


def p_ExpressionList(p):
    """ExpressionList : Expression ExpressionListRepOne"""


def p_ExpressionListRepOne(p):
    """ExpressionListRepOne : ExpressionListRepOne COMMA Expression
                            |"""


def p_TypeDecl(p):
    """TypeDecl : TYPE TypeDeclGroupOne"""


def p_TypeDeclGroupOne(p):
    """TypeDeclGroupOne : TypeSpec
                        | LBRACK TypeDeclGroupOneRepOne RBRACK"""


def p_TypeDeclGroupOneRepOne(p):
    """TypeDeclGroupOneRepOne : TypeDeclGroupOneRepOne TypeSpec SEMICOLON
                              |"""


def p_TypeSpec(p):
    """TypeSpec : AliasDecl
                | TypeDef"""


def p_AliasDecl(p):
    """AliasDecl : ID ASSIGN Type"""


def p_TypeDef(p):
    """TypeDef : ID Type"""


def p_VarDecl(p):
    """VarDecl : VAR VarDeclGroupOne"""


def p_VarDeclGroupOne(p):
    """VarDeclGroupOne : VarSpec
                       | LBRACK VarDeclGroupOneRepOne RBRACK"""


def p_VarDeclGroupOneRepOne(p):
    """VarDeclGroupOneRepOne : VarDeclGroupOneRepOne VarSpec SEMICOLON
                             |"""


def p_VarSpec(p):
    """VarSpec : IdentifierList VarSpecGroupOne"""


def p_VarSpecGroupOne(p):
    """VarSpecGroupOne : Type VarSpecGroupOneOptOne
                       | ASSIGN ExpressionList"""


def p_VarSpecGroupOneOptOne(p):
    """VarSpecGroupOneOptOne : ASSIGN ExpressionList
                             |"""


def p_ShortVarDecl(p):
    """ShortVarDecl : IdentifierList SHDECL ExpressionList"""


def p_FunctionDecl(p):
    """FunctionDecl : FUNC FunctionName Signature FunctionDeclOptOne"""


def p_FunctionDeclOptOne(p):
    """FunctionDeclOptOne : FunctionBody
                          |"""


def p_FunctionName(p):
    """FunctionName : ID"""


def p_FunctionBody(p):
    """FunctionBody : Block"""


def p_MethodDecl(p):
    """MethodDecl : FUNC Receiver MethodName Signature MethodDeclOptOne"""


def p_MethodDeclOptOne(p):
    """MethodDeclOptOne : FunctionBody
                        |"""


def p_Receiver(p):
    """Receiver : Parameters"""


def p_Operand(p):
    """Operand : Literal
               | OperandName
               | LBRACK Expression RBRACK"""


def p_Literal(p):
    """Literal : BasicLit
               | CompositeLit
               | FunctionLit"""


def p_BasicLit(p):
    """BasicLit : INT
                | FLOAT
                | IMAG
                | RUNE
                | STRING"""


def p_OperandName(p):
    """OperandName : ID
                   | QualifiedIdent"""


def p_QualifiedIdent(p):
    """QualifiedIdent : PackageName DOT ID"""


def p_CompositeLit(p):
    """CompositeLit : LiteralType LiteralValue"""


def p_LiteralType(p):
    """LiteralType : StructType
                   | ArrayType
                   | LSQBRACK TRIDOT RSQBRACK ElementType
                   | SliceType
                   | MapType
                   | TypeName"""


def p_LiteralValue(p):
    """LiteralValue : LCURLBR LiteralValueOptOne RCURLBR"""


def p_LiteralValueOptOne(p):
    """LiteralValueOptOne : ElementList LiteralValueOptOneOptOne
                          |"""


def p_LiteralValueOptOneOptOne(p):
    """LiteralValueOptOneOptOne : COMMA
                                |"""


def p_ElementList(p):
    """ElementList : KeyedElement ElementListRepOne"""


def p_ElementListRepOne(p):
    """ElementListRepOne : ElementListRepOne COMMA KeyedElement
                         |"""


def p_KeyedElement(p):
    """KeyedElement : KeyedElementOptOne Element"""


def p_KeyedElementOptOne(p):
    """KeyedElementOptOne : Key COLON
                          |"""


def p_Key(p):
    """Key : FieldName
           | Expression
           | LiteralValue"""


def p_FieldName(p):
    """FieldName : ID"""


def p_Element(p):
    """Element : Expression
               | LiteralValue"""


def p_FunctionLit(p):
    """FunctionLit : FUNC Signature FunctionBody"""


def p_PrimaryExpr(p):
    """PrimaryExpr : Operand
                   | Conversion
                   | MethodExpr
                   | PrimaryExpr Selector
                   | PrimaryExpr Index
                   | PrimaryExpr Slice
                   | PrimaryExpr TypeAssertion
                   | PrimaryExpr Arguments"""


def p_Selector(p):
    """Selector : DOT ID"""


def p_Index(p):
    """Index : LSQBRACK Expression RSQBRACK"""


def p_Slice(p):
    """Slice : LSQBRACK SliceOptOne COLON SliceOptTwo RSQBRACK
             | LSQBRACK SliceOptThree COLON Expression COLON Expression RSQBRACK"""


def p_SliceOptOne(p):
    """SliceOptOne : Expression
                   |"""


def p_SliceOptTwo(p):
    """SliceOptTwo : Expression
                   |"""


def p_SliceOptThree(p):
    """SliceOptThree : Expression
                     |"""


def p_TypeAssertion(p):
    """TypeAssertion : DOT LBRACK Type RBRACK"""


def p_Arguments(p):
    """Arguments : LBRACK ArgumentsOptOne RBRACK"""


def p_ArgumentsOptOne(p):
    """ArgumentsOptOne : ArgumentsOptOneGroupOne ArgumentsOptOneOptOne ArgumentsOptOneOptTwo
                       |"""


def p_ArgumentsOptOneGroupOne(p):
    """ArgumentsOptOneGroupOne : ExpressionList
                               | Type ArgumentsOptOneGroupOneOptOne"""


def p_ArgumentsOptOneGroupOneOptOne(p):
    """ArgumentsOptOneGroupOneOptOne : COMMA ExpressionList
                                     |"""


def p_ArgumentsOptOneOptOne(p):
    """ArgumentsOptOneOptOne : TRIDOT
                             |"""


def p_ArgumentsOptOneOptTwo(p):
    """ArgumentsOptOneOptTwo : COMMA
                             |"""


def p_MethodExpr(p):
    """MethodExpr : ReceiverType DOT MethodName"""


def p_ReceiverType(p):
    """ReceiverType : Type"""


def p_Expression(p):
    """Expression : UnaryExpr
                  | Expression binaryop Expression"""


def p_UnaryExpr(p):
    """UnaryExpr : PrimaryExpr
                 | unaryop UnaryExpr"""


def p_binaryop(p):
    """binaryop : LOGOR
                | LOGAND
                | relop
                | addop
                | mulop"""


def p_relop(p):
    """relop : EQUALS
             | NOTEQ
             | LESS
             | LESSEQ
             | GREAT
             | GREATEQ"""


def p_addop(p):
    """addop : PLUS
             | MINUS
             | BITOR
             | BITXOR"""


def p_mulop(p):
    """mulop : MULT
             | DIV
             | MODULO
             | LSHIFT
             | RSHIFT
             | BITAND
             | BITCLR"""


def p_unaryop(p):
    """unaryop : PLUS
               | MINUS
               | LOGNOT
               | BITXOR
               | MULT
               | BITAND
               | REC"""


def p_Conversion(p):
    """Conversion : Type LBRACK Expression ConversionOptOne RBRACK"""


def p_ConversionOptOne(p):
    """ConversionOptOne : COMMA
                        |"""


def p_Statement(p):
    """Statement : Declaration
                 | LabeledStmt
                 | SimpleStmt
                 | GoStmt
                 | ReturnStmt
                 | BreakStmt
                 | ContinueStmt
                 | GotoStmt
                 | FallthroughStmt
                 | Block
                 | IfStmt
                 | SwitchStmt
                 | SelectStmt
                 | ForStmt
                 | DeferStmt"""


def p_SimpleStmt(p):
    """SimpleStmt : EmptyStmt
                  | ExpressionStmt
                  | SendStmt
                  | IncDecStmt
                  | Assignment
                  | ShortVarDecl"""


def p_EmptyStmt(p):
    """
        EmptyStmt :"""


def p_LabeledStmt(p):
    """LabeledStmt : Label COLON Statement"""


def p_Label(p):
    """Label : ID"""


def p_ExpressionStmt(p):
    """ExpressionStmt : Expression"""


def p_SendStmt(p):
    """SendStmt : Channel REC Expression"""


def p_Channel(p):
    """Channel : Expression"""


def p_IncDecStmt(p):
    """IncDecStmt : Expression IncDecStmtGroupOne"""


def p_IncDecStmtGroupOne(p):
    """IncDecStmtGroupOne : INCR
                          | DECR"""


def p_Assignment(p):
    """Assignment : ExpressionList assignop ExpressionList"""


def p_assignop(p):
    """assignop : assignopOptOne ASSIGN"""


def p_assignopOptOne(p):
    """assignopOptOne : addop
                      | mulop
                      |"""


def p_IfStmt(p):
    """IfStmt : IF IfStmtOptOne Expression Block IfStmtOptTwo"""


def p_IfStmtOptOne(p):
    """IfStmtOptOne : SimpleStmt SEMICOLON
                    |"""


def p_IfStmtOptTwo(p):
    """IfStmtOptTwo : ELSE IfStmtOptTwoGroupOne
                    |"""


def p_IfStmtOptTwoGroupOne(p):
    """IfStmtOptTwoGroupOne : IfStmt
                            | Block"""


def p_SwitchStmt(p):
    """SwitchStmt : ExprSwitchStmt
                  | TypeSwitchStmt"""


def p_ExprSwitchStmt(p):
    """ExprSwitchStmt : SWITCH ExprSwitchStmtOptOne ExprSwitchStmtOptTwo LCURLBR ExprSwitchStmtRepOne RCURLBR"""


def p_ExprSwitchStmtOptOne(p):
    """ExprSwitchStmtOptOne : SimpleStmt SEMICOLON
                            |"""


def p_ExprSwitchStmtOptTwo(p):
    """ExprSwitchStmtOptTwo : Expression
                            |"""


def p_ExprSwitchStmtRepOne(p):
    """ExprSwitchStmtRepOne : ExprSwitchStmtRepOne ExprCaseClause
                            |"""


def p_ExprCaseClause(p):
    """ExprCaseClause : ExprSwitchCase COLON StatementList"""


def p_ExprSwitchCase(p):
    """ExprSwitchCase : CASE ExpressionList
                      | DEFAULT"""


def p_TypeSwitchStmt(p):
    """TypeSwitchStmt : SWITCH TypeSwitchStmtOptOne TypeSwitchGuard LCURLBR TypeSwitchStmtRepOne RCURLBR"""


def p_TypeSwitchStmtOptOne(p):
    """TypeSwitchStmtOptOne : SimpleStmt SEMICOLON
                            |"""


def p_TypeSwitchStmtRepOne(p):
    """TypeSwitchStmtRepOne : TypeSwitchStmtRepOne TypeCaseClause
                            |"""


def p_TypeSwitchGuard(p):
    """TypeSwitchGuard : TypeSwitchGuardOptOne PrimaryExpr DOT LBRACK TYPE RBRACK"""


def p_TypeSwitchGuardOptOne(p):
    """TypeSwitchGuardOptOne : ID SHDECL
                             |"""


def p_TypeCaseClause(p):
    """TypeCaseClause : TypeSwitchCase COLON StatementList"""


def p_TypeSwitchCase(p):
    """TypeSwitchCase : CASE TypeList
                      | DEFAULT"""


def p_TypeList(p):
    """TypeList : Type TypeListRepOne"""


def p_TypeListRepOne(p):
    """TypeListRepOne : TypeListRepOne COMMA Type
                      |"""


def p_ForStmt(p):
    """ForStmt : FOR ForStmtOptOne Block"""


def p_ForStmtOptOne(p):
    """ForStmtOptOne : Condition
                     | ForClause
                     | RangeClause
                     |"""


def p_Condition(p):
    """Condition : Expression"""


def p_ForClause(p):
    """ForClause : ForClauseOptOne SEMICOLON ForClauseOptTwo SEMICOLON ForClauseOptThree"""


def p_ForClauseOptOne(p):
    """ForClauseOptOne : InitStmt
                       |"""


def p_ForClauseOptTwo(p):
    """ForClauseOptTwo : Condition
                       |"""


def p_ForClauseOptThree(p):
    """ForClauseOptThree : PostStmt
                         |"""


def p_InitStmt(p):
    """InitStmt : SimpleStmt"""


def p_PostStmt(p):
    """PostStmt : SimpleStmt"""


def p_RangeClause(p):
    """RangeClause : RangeClauseOptOne RANGE Expression"""


def p_RangeClauseOptOne(p):
    """RangeClauseOptOne : ExpressionList ASSIGN
                         | IdentifierList SHDECL
                         |"""


def p_GoStmt(p):
    """GoStmt : GO Expression"""


def p_SelectStmt(p):
    """SelectStmt : SELECT LCURLBR SelectStmtRepOne RCURLBR"""


def p_SelectStmtRepOne(p):
    """SelectStmtRepOne : SelectStmtRepOne CommClause
                        |"""


def p_CommClause(p):
    """CommClause : CommCase COLON StatementList"""


def p_CommCase(p):
    """CommCase : CASE CommCaseGroupOne
                | DEFAULT"""


def p_CommCaseGroupOne(p):
    """CommCaseGroupOne : SendStmt
                        | RecvStmt"""


def p_RecvStmt(p):
    """RecvStmt : RecvStmtOptOne RecvExpr"""


def p_RecvStmtOptOne(p):
    """RecvStmtOptOne : ExpressionList ASSIGN
                      | IdentifierList SHDECL
                      |"""


def p_RecvExpr(p):
    """RecvExpr : Expression"""


def p_ReturnStmt(p):
    """ReturnStmt : RETURN ReturnStmtOptOne"""


def p_ReturnStmtOptOne(p):
    """ReturnStmtOptOne : ExpressionList
                        |"""


def p_BreakStmt(p):
    """BreakStmt : BREAK BreakStmtOptOne"""


def p_BreakStmtOptOne(p):
    """BreakStmtOptOne : Label
                       |"""


def p_ContinueStmt(p):
    """ContinueStmt : CONTINUE ContinueStmtOptOne"""


def p_ContinueStmtOptOne(p):
    """ContinueStmtOptOne : Label
                          |"""


def p_GotoStmt(p):
    """GotoStmt : GOTO Label"""


def p_FallthroughStmt(p):
    """FallthroughStmt : FALLTHROUGH"""


def p_DeferStmt(p):
    """DeferStmt : DEFER Expression"""


def p_PackageClause(p):
    """PackageClause : PACKAGE PackageName"""


def p_PackageName(p):
    """PackageName : ID"""


def p_ImportDecl(p):
    """ImportDecl : IMPORT ImportDeclGroupOne"""


def p_ImportDeclGroupOne(p):
    """ImportDeclGroupOne : ImportSpec
                          | LBRACK ImportDeclGroupOneRepOne RBRACK"""


def p_ImportDeclGroupOneRepOne(p):
    """ImportDeclGroupOneRepOne : ImportDeclGroupOneRepOne ImportSpec SEMICOLON
                                |"""


def p_ImportSpec(p):
    """ImportSpec : ImportSpecOptOne ImportPath"""


def p_ImportSpecOptOne(p):
    """ImportSpecOptOne : DOT
                        | PackageName
                        |"""


def p_ImportPath(p):
    """ImportPath : STRING"""


parser = yacc.yacc()

if __name__ == "__main__":
    parser = ArgumentParser(description="Parser for Go")
    parser.add_argument("input", type=str, help="input file")
    parser.add_argument(
        "-o", "--output", type=str, default=None, help="output file name"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug output"
    )
    args = parser.parse_args()
    if args.output is None:
        args.output = args.input.split("/")[-1] + ".dot"

    with open(args.input, "r") as go:
        result = parser.parse(go.read())

    if args.verbose:
        print(result)

    with open(args.output, "w") as outf:
        outf.write(result)
    print('Output file "{}" generated'.format(args.output))
