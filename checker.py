"""Analizador Semántico EXIGENTE para B-Minor.

Utiliza el patrón Visitor con multimethod para recorrer el AST y verificar:
- Declaración de identificadores antes de su uso
- Alcances léxicos anidados
- Chequeo de tipos en expresiones, asignaciones, operadores
- Validación de llamadas a funciones y retornos
"""

from multimethod import multimethod
from symtab import Symtab
from model import *

# =============== SISTEMA DE TIPOS ===============

TYPES = {
    'integer', 'boolean', 'string', 'float', 'char', 'void'
}

BINOP_TABLE = {
    '+': {('integer', 'integer'): 'integer', ('float', 'float'): 'float', ('string', 'string'): 'string'},
    '-': {('integer', 'integer'): 'integer', ('float', 'float'): 'float'},
    '*': {('integer', 'integer'): 'integer', ('float', 'float'): 'float'},
    '/': {('integer', 'integer'): 'integer', ('float', 'float'): 'float'},
    '%': {('integer', 'integer'): 'integer'},
    '<': {('integer', 'integer'): 'boolean', ('float', 'float'): 'boolean', ('integer', 'float'): 'boolean', ('float', 'integer'): 'boolean'},
    '<=': {('integer', 'integer'): 'boolean', ('float', 'float'): 'boolean', ('integer', 'float'): 'boolean', ('float', 'integer'): 'boolean'},
    '>': {('integer', 'integer'): 'boolean', ('float', 'float'): 'boolean', ('integer', 'float'): 'boolean', ('float', 'integer'): 'boolean'},
    '>=': {('integer', 'integer'): 'boolean', ('float', 'float'): 'boolean', ('integer', 'float'): 'boolean', ('float', 'integer'): 'boolean'},
    '==': {('integer', 'integer'): 'boolean', ('float', 'float'): 'boolean', ('integer', 'float'): 'boolean', ('float', 'integer'): 'boolean', ('boolean', 'boolean'): 'boolean', ('string', 'string'): 'boolean', ('char', 'char'): 'boolean'},
    '!=': {('integer', 'integer'): 'boolean', ('float', 'float'): 'boolean', ('integer', 'float'): 'boolean', ('float', 'integer'): 'boolean', ('boolean', 'boolean'): 'boolean', ('string', 'string'): 'boolean', ('char', 'char'): 'boolean'},
    '&&': {('boolean', 'boolean'): 'boolean'},
    '||': {('boolean', 'boolean'): 'boolean'},
    '^': {('integer', 'integer'): 'integer'},
}

UNARYOP_TABLE = {
    '-': {'integer': 'integer', 'float': 'float'},
    '!': {'boolean': 'boolean'},
    '+': {'integer': 'integer', 'float': 'float'},
}


def check_binop(op, left_type, right_type):
    if op not in BINOP_TABLE:
        return False, None
    key = (left_type, right_type)
    if key in BINOP_TABLE[op]:
        return True, BINOP_TABLE[op][key]
    return False, None


def check_unaryop(op, operand_type):
    if op not in UNARYOP_TABLE:
        return False, None
    if operand_type in UNARYOP_TABLE[op]:
        return True, UNARYOP_TABLE[op][operand_type]
    return False, None


def is_valid_type(type_name):
    if isinstance(type_name, str):
        if type_name.startswith('array_of_'):
            return True
        return type_name in TYPES
    return False


def is_array_type(type_name):
    return isinstance(type_name, str) and type_name.startswith('array_of_')


def get_array_element_type(array_type):
    """array_of_integer -> integer"""
    if not is_array_type(array_type):
        return None
    return array_type[9:]


def can_assign(target_type, value_type):
    if target_type == value_type:
        return True
    if target_type == 'error' or value_type == 'error':
        return False
    if target_type == 'float' and value_type == 'integer':
        return True
    return False


# =============== ANALIZADOR SEMÁNTICO ===============

class SemanticChecker:
    def __init__(self):
        self.symtab = Symtab("global")
        self.errors = []
        self.current_return_type = None
        self.in_loop = False

    def _enter_scope(self, name):
        self.symtab = Symtab(name, parent=self.symtab)

    def _leave_scope(self):
        if self.symtab.parent is not None:
            self.symtab = self.symtab.parent

    def _declare_function_signatures(self, declarations):
        for decl in declarations:
            if not isinstance(decl, Function):
                continue
            try:
                self.symtab.add(decl.name, decl)
            except Exception as e:
                self.report(str(e), decl.lineno)

    def _stmt_guarantees_return(self, stmt):
        if isinstance(stmt, ReturnStmt):
            return True
        if isinstance(stmt, BlockStmt):
            return self._body_guarantees_return(stmt.statements)
        if isinstance(stmt, IfStmt):
            if stmt.else_block is None:
                return False
            return self._body_guarantees_return(stmt.then_block) and self._body_guarantees_return(stmt.else_block)
        return False

    def _body_guarantees_return(self, statements):
        for stmt in statements:
            if self._stmt_guarantees_return(stmt):
                return True
        return False

    def _check_array_sizes(self, node: VarDeclaration):
        for size_expr in getattr(node, 'array_sizes', []):
            size_type = self.visit(size_expr)
            if size_type != "integer" and size_type != "error":
                self.report(
                    f"El tamaño de arreglo de '{node.name}' debe ser integer, se recibió {size_type}",
                    size_expr.lineno
                )

    def report(self, message, line):
        self.errors.append(f"Error semántico (línea {line}): {message}")

    @multimethod
    def visit(self, node: Program):
        self._declare_function_signatures(node.declarations)
        for decl in node.declarations:
            self.visit(decl)

    @multimethod
    def visit(self, node: Function):
        symbol = self.symtab.get(node.name)
        if symbol is None:
            try:
                self.symtab.add(node.name, node)
            except Exception as e:
                self.report(str(e), node.lineno)
                return
        elif symbol is not node:
            self.report(f"Redefinición inválida de función '{node.name}'", node.lineno)
            return

        old_symtab = self.symtab
        self._enter_scope(f"func_{node.name}")
        old_return_type = self.current_return_type
        self.current_return_type = node.return_type

        try:
            for param in node.params:
                if not is_valid_type(param.type_name):
                    self.report(f"Tipo inválido en parámetro '{param.name}': {param.type_name}", param.lineno)
                self._check_array_sizes(param)
                try:
                    self.symtab.add(param.name, param)
                except Exception as e:
                    self.report(str(e), param.lineno)

            for stmt in node.body:
                self.visit(stmt)

            if node.return_type != "void" and not self._body_guarantees_return(node.body):
                self.report(f"La función '{node.name}' debe retornar un valor de tipo {node.return_type}", node.lineno)
        finally:
            self.current_return_type = old_return_type
            self.symtab = old_symtab

    @multimethod
    def visit(self, node: VarDeclaration):
        if not is_valid_type(node.type_name):
            self.report(f"Tipo desconocido '{node.type_name}'", node.lineno)
            return

        self._check_array_sizes(node)
        
        if node.value:
            if is_array_type(node.type_name) and isinstance(node.value, ArrayLiteral):
                # En arreglos con tipo declarado, validar cada elemento contra el tipo esperado.
                expected_elem_type = get_array_element_type(node.type_name)
                for i, elem in enumerate(node.value.elements):
                    elem_type = self.visit(elem)
                    if not can_assign(expected_elem_type, elem_type):
                        self.report(
                            f"Elemento de arreglo {i+1} de '{node.name}' tiene tipo {elem_type}, se esperaba {expected_elem_type}",
                            elem.lineno
                        )
                node.value.type = node.type_name
                val_type = node.type_name
            else:
                val_type = self.visit(node.value)
            if not can_assign(node.type_name, val_type):
                self.report(f"No se puede inicializar '{node.name}' ({node.type_name}) con tipo {val_type}", node.lineno)
        
        try:
            self.symtab.add(node.name, node)
        except Exception as e:
            self.report(str(e), node.lineno)

    @multimethod
    def visit(self, node: Assignment):
        sym = self.symtab.get(node.name)
        if not sym:
            self.report(f"Identificador '{node.name}' no declarado", node.lineno)
            return "error"
        if isinstance(sym, Function):
            self.report(f"No se puede asignar a la función '{node.name}'", node.lineno)
            return "error"
        
        target_type = getattr(sym, 'type_name', 'error')
        val_type = self.visit(node.value)
        
        if not can_assign(target_type, val_type):
            self.report(f"No se puede asignar {val_type} a variable '{node.name}' ({target_type})", node.lineno)
        
        return target_type

    @multimethod
    def visit(self, node: ArrayAssignment):
        array_type = self.visit(node.array)
        index_type = self.visit(node.index)
        value_type = self.visit(node.value)

        if index_type != "integer":
            self.report(f"El índice debe ser integer, se recibió {index_type}", node.lineno)

        if not is_array_type(array_type):
            self.report(f"No se puede asignar a tipo {array_type}", node.lineno)
            return "error"

        element_type = get_array_element_type(array_type)
        if not can_assign(element_type, value_type):
            self.report(f"No se puede asignar {value_type} a un elemento de tipo {element_type}", node.lineno)

        node.type = element_type
        return element_type

    @multimethod
    def visit(self, node: IfStmt):
        cond_type = self.visit(node.condition)
        if cond_type != "boolean":
            self.report(f"La condición del 'if' debe ser boolean, se recibió '{cond_type}'", node.lineno)
        
        self._enter_scope("if_then")
        try:
            for stmt in node.then_block:
                self.visit(stmt)
        finally:
            self._leave_scope()
        
        if node.else_block:
            self._enter_scope("if_else")
            try:
                for stmt in node.else_block:
                    self.visit(stmt)
            finally:
                self._leave_scope()

    @multimethod
    def visit(self, node: WhileStmt):
        cond_type = self.visit(node.condition)
        if cond_type != "boolean":
            self.report(f"La condición del 'while' debe ser boolean, se recibió '{cond_type}'", node.lineno)
        
        self._enter_scope("while_body")
        old_loop = self.in_loop
        self.in_loop = True
        try:
            for stmt in node.body:
                self.visit(stmt)
        finally:
            self.in_loop = old_loop
            self._leave_scope()

    @multimethod
    def visit(self, node: ForStmt):
        self._enter_scope("for_body")
        old_loop = self.in_loop
        self.in_loop = True
        try:
            if node.init:
                self.visit(node.init)

            if node.condition:
                cond_type = self.visit(node.condition)
                if cond_type != "boolean":
                    self.report(f"La condición del 'for' debe ser boolean, se recibió '{cond_type}'", node.lineno)

            if node.step:
                self.visit(node.step)

            for stmt in node.body:
                self.visit(stmt)
        finally:
            self.in_loop = old_loop
            self._leave_scope()

    @multimethod
    def visit(self, node: PrintStmt):
        for arg in node.args:
            arg_type = self.visit(arg)
            if is_array_type(arg_type):
                self.report(f"print no puede mostrar tipo array", arg.lineno)

    @multimethod
    def visit(self, node: BinaryOp):
        left_t = self.visit(node.left)
        right_t = self.visit(node.right)
        is_valid, res_t = check_binop(node.op, left_t, right_t)
        
        if not is_valid:
            self.report(f"Operación '{node.op}' no válida entre {left_t} y {right_t}", node.lineno)
            node.type = "error"
            return "error"
        
        node.type = res_t
        return res_t

    @multimethod
    def visit(self, node: UnaryOp):
        operand_t = self.visit(node.operand)
        is_valid, res_t = check_unaryop(node.op, operand_t)
        
        if not is_valid:
            self.report(f"Operador unario '{node.op}' no válido para {operand_t}", node.lineno)
            node.type = "error"
            return "error"
        
        node.type = res_t
        return res_t

    @multimethod
    def visit(self, node: PostfixOp):
        operand_t = self.visit(node.operand)
        
        if operand_t not in ('integer', 'float'):
            self.report(f"Operador {node.op} no válido para {operand_t}", node.lineno)
            node.type = "error"
            return "error"
        
        node.type = operand_t
        return operand_t

    @multimethod
    def visit(self, node: IndexExpr):
        array_t = self.visit(node.array)
        index_t = self.visit(node.index)
        
        if index_t != "integer":
            self.report(f"El índice debe ser integer, se recibió {index_t}", node.lineno)
        
        if not is_array_type(array_t):
            self.report(f"No se puede indexar tipo {array_t}", node.lineno)
            node.type = "error"
            return "error"
        
        elem_type = get_array_element_type(array_t)
        node.type = elem_type
        return elem_type if elem_type else "error"

    @multimethod
    def visit(self, node: ArrayLiteral):
        if not node.elements:
            node.type = "error"
            return "error"
        
        elem_types = [self.visit(elem) for elem in node.elements]
        first_type = elem_types[0]
        
        for i, t in enumerate(elem_types[1:], 1):
            if t != first_type:
                self.report(f"Elemento de arreglo {i+1} tiene tipo {t}, se esperaba {first_type}", node.elements[i].lineno)
        
        node.type = f"array_of_{first_type}"
        return node.type

    @multimethod
    def visit(self, node: FunctionCall):
        sym = self.symtab.get(node.name)
        if not sym or not isinstance(sym, Function):
            self.report(f"Función '{node.name}' no definida", node.lineno)
            node.type = "error"
            return "error"
        
        if len(node.args) != len(sym.params):
            self.report(f"La función '{node.name}' espera {len(sym.params)} argumentos, recibió {len(node.args)}", node.lineno)
            node.type = "error"
            return "error"
        
        has_error = False
        for i, arg in enumerate(node.args):
            arg_t = self.visit(arg)
            param_t = sym.params[i].type_name
            if not can_assign(param_t, arg_t):
                self.report(f"Argumento {i+1} de '{node.name}' debe ser {param_t}, se recibió {arg_t}", node.lineno)
                has_error = True
        
        if has_error:
            node.type = "error"
            return "error"

        node.type = sym.return_type
        return sym.return_type

    @multimethod
    def visit(self, node: ReturnStmt):
        if self.current_return_type is None:
            self.report("return fuera de una función", node.lineno)
            return "error"

        if node.expr:
            ret_type = self.visit(node.expr)
        else:
            ret_type = "void"
        
        if ret_type != self.current_return_type:
            self.report(f"Se esperaba retorno de tipo {self.current_return_type}, pero se obtuvo {ret_type}", node.lineno)
        return ret_type

    @multimethod
    def visit(self, node: ExprStmt):
        self.visit(node.expr)

    @multimethod
    def visit(self, node: BlockStmt):
        self._enter_scope("block")
        try:
            for stmt in node.statements:
                self.visit(stmt)
        finally:
            self._leave_scope()

    @multimethod
    def visit(self, node: Identifier):
        symbol = self.symtab.get(node.name)
        if not symbol:
            self.report(f"Identificador '{node.name}' no declarado", node.lineno)
            node.type = "error"
            return "error"

        if isinstance(symbol, Function):
            self.report(f"La función '{node.name}' debe invocarse con paréntesis", node.lineno)
            node.type = "error"
            return "error"
        
        if hasattr(symbol, 'type_name'):
            node.type = symbol.type_name
            return symbol.type_name
        if hasattr(symbol, 'return_type'):
            node.type = symbol.return_type
            return symbol.return_type
        node.type = "error"
        return "error"

    @multimethod
    def visit(self, node: IntLiteral):
        node.type = "integer"
        return "integer"
    
    @multimethod
    def visit(self, node: FloatLiteral):
        node.type = "float"
        return "float"
    
    @multimethod
    def visit(self, node: BooleanLiteral):
        node.type = "boolean"
        return "boolean"
    
    @multimethod
    def visit(self, node: StringLiteral):
        node.type = "string"
        return "string"
    
    @multimethod
    def visit(self, node: CharLiteral):
        node.type = "char"
        return "char"

    @multimethod
    def visit(self, node: Node):
        self.report(f"Nodo semántico no soportado: {type(node).__name__}", getattr(node, 'lineno', 0))
        return "error"
