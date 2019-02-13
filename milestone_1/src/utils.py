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


class GoConstDecl:
    def __init__(self, declarations):
        self.declarations = declarations


class GoConstSpec:
    def __init__(self, specs):
        self.specs = specs