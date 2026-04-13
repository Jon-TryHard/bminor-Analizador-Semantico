"""Analizador Semántico para B-Minor usando el patrón Visitor con multimethod.

Este módulo implementa el análisis semántico del compilador B-Minor, responsable de:
- Verificar la declaración de identificadores antes de su uso
- Manejar alcances léxicos anidados (bloques, funciones, parámetros)
- Realizar chequeo de tipos en expresiones y asignaciones
- Validar llamadas a funciones y retornos
- Reportar errores semánticos con precisión de línea
"""

from multimethod import multimethod
from symtab import Symtab
from model import *

# =============== SISTEMA DE TIPOS ===============

# Tipos básicos soportados
TYPES = {
    'integer': 'integer',
    'boolean': 'boolean',
    'string': 'string',
    'float': 'float',
    'void': 'void'
}

# Tabla de compatibilidad de operadores binarios
BINOP_TABLE = {
    '+': {
        ('integer', 'integer'): 'integer',
        ('float', 'float'): 'float',
        ('string', 'string'): 'string',
    },
    '-': {
        ('integer', 'integer'): 'integer',
        ('float', 'float'): 'float',
    },
    '*': {
        ('integer', 'integer'): 'integer',
        ('float', 'float'): 'float',
    },
    '/': {
        ('integer', 'integer'): 'integer',
        ('float', 'float'): 'float',
    },
    '%': {
        ('integer', 'integer'): 'integer',
    },
    '<': {
        ('integer', 'integer'): 'boolean',
        ('float', 'float'): 'boolean',
    },
    '<=': {
        ('integer', 'integer'): 'boolean',
        ('float', 'float'): 'boolean',
    },
    '>': {
        ('integer', 'integer'): 'boolean',
        ('float', 'float'): 'boolean',
    },
    '>=': {
        ('integer', 'integer'): 'boolean',
        ('float', 'float'): 'boolean',
    },
    '==': {
        ('integer', 'integer'): 'boolean',
        ('float', 'float'): 'boolean',
        ('boolean', 'boolean'): 'boolean',
        ('string', 'string'): 'boolean',
    },
    '!=': {
        ('integer', 'integer'): 'boolean',
        ('float', 'float'): 'boolean',
        ('boolean', 'boolean'): 'boolean',
        ('string', 'string'): 'boolean',
    },
    '&&': {
        ('boolean', 'boolean'): 'boolean',
    },
    '||': {
        ('boolean', 'boolean'): 'boolean',
    },
}

# Tabla de compatibilidad de operadores unarios
UNARYOP_TABLE = {
    '-': {
        'integer': 'integer',
        'float': 'float',
    },
    '!': {
        'boolean': 'boolean',
    },
}


def check_binop(op, left_type, right_type):
    """Verifica si una operación binaria es válida y retorna el tipo resultante.
    
    Args:
        op: Operador binario ('+', '-', '*', '/', '%', '<', etc.)
        left_type: Tipo del operando izquierdo
        right_type: Tipo del operando derecho
        
    Returns:
        Tupla (es_válido, tipo_resultado)
        - es_válido: True si la operación es válida, False en caso contrario
        - tipo_resultado: Tipo del resultado de la operación (o None si no es válida)
    """
    if op not in BINOP_TABLE:
        return False, None
    
    key = (left_type, right_type)
    if key in BINOP_TABLE[op]:
        return True, BINOP_TABLE[op][key]
    
    return False, None


def check_unaryop(op, operand_type):
    """Verifica si una operación unaria es válida y retorna el tipo resultante.
    
    Args:
        op: Operador unario ('-', '!')
        operand_type: Tipo del operando
        
    Returns:
        Tupla (es_válido, tipo_resultado)
        - es_válido: True si la operación es válida, False en caso contrario
        - tipo_resultado: Tipo del resultado de la operación (o None si no es válida)
    """
    if op not in UNARYOP_TABLE:
        return False, None
    
    if operand_type in UNARYOP_TABLE[op]:
        return True, UNARYOP_TABLE[op][operand_type]
    
    return False, None


def loockup_type(type_name):
    """Busca un tipo en la tabla de tipos (función con typo intencional para compatibilidad).
    
    Args:
        type_name: Nombre del tipo a buscar
        
    Returns:
        El nombre del tipo si existe, None en caso contrario
    """
    return TYPES.get(type_name)


def is_valid_type(type_name):
    """Verifica si un nombre de tipo es válido.
    
    Args:
        type_name: Nombre del tipo a validar
        
    Returns:
        True si el tipo es válido, False en caso contrario
    """
    return type_name in TYPES


def are_compatible(type1, type2):
    """Verifica si dos tipos son compatibles para asignación.
    
    Args:
        type1: Primer tipo
        type2: Segundo tipo
        
    Returns:
        True si type2 puede asignarse a type1, False en caso contrario
    """
    if type1 == type2:
        return True
    
    # Permitir conversiones automáticas si es necesario
    # Por ahora, solo tipos exactos son compatibles
    return False


# =============== ANALIZADOR SEMÁNTICO ===============

class SemanticChecker:
    """Verificador de semántica que implementa el patrón Visitor para recorrer el AST.
    
    Atributos:
        symtab: Tabla de símbolos con soporte para alcances léxicos
        errors: Lista de errores semánticos encontrados durante la verificación
        current_return_type: Tipo de retorno esperado en la función actual
    """
    
    def __init__(self):
        """Inicializa el verificador con una tabla de símbolos global vacía."""
        self.symtab = Symtab("global")
        self.errors = []
        self.current_return_type = None

    def report(self, message, line):
        """Registra un error semántico con mensaje y número de línea.
        
        Args:
            message: Descripción del error
            line: Número de línea donde se encontró el error
        """
        self.errors.append(f"Error semántico (línea {line}): {message}")

    # =============== NIVEL SUPERIOR DEL PROGRAMA ===============

    @multimethod
    def visit(self, node: Program):
        """Procesa el programa completo visitando todas sus declaraciones.
        
        El programa es la raíz del AST y contiene funciones y/o variables globales.
        """
        for decl in node.declarations:
            self.visit(decl)

    @multimethod
    def visit(self, node: Function):
        """Verifica la definición de una función (Regla 5.4 y 5.2).
        
        Realizar:
        1. Registrar la función en el alcance global
        2. Crear un nuevo alcance para el cuerpo de la función
        3. Registrar parámetros en el nuevo alcance
        4. Verificar el cuerpo respecto al tipo de retorno
        5. Restaurar el alcance anterior
        """
        # Regla 5.4: Registrar la función antes de entrar a su cuerpo (evita recursión indefinida)
        try:
            self.symtab.add(node.name, node)
        except Exception as e:
            self.report(str(e), node.lineno)

        # Regla 5.2: Crear nuevo alcance para la función
        old_symtab = self.symtab
        self.symtab = Symtab(f"func_{node.name}", parent=old_symtab)
        
        # Guardar el tipo de retorno anterior para restaurarlo después
        old_return_type = self.current_return_type
        self.current_return_type = node.return_type
        
        # Registrar parámetros formales en el nuevo alcance
        for param in node.params:
            self.visit(param)
            
        # Verificar cada sentencia del cuerpo
        for stmt in node.body:
            self.visit(stmt)
            
        # Restaurar el contexto anterior al salir de la función
        self.current_return_type = old_return_type
        self.symtab = old_symtab

    # =============== DECLARACIONES DE VARIABLES Y ASIGNACIONES ===============

    @multimethod
    def visit(self, node: VarDeclaration):
        """Procesa la declaración de una variable (Regla 5.1 y 6.1).
        
        Verificar:
        1. Que el tipo declarado sea válido y conocido
        2. Si hay inicialización, que sea compatible con el tipo
        3. Que no exista ya una variable con el mismo nombre en este alcance
        """
        # Regla 5.3: Verificar que el tipo de dato existe en el sistema de tipos
        if not loockup_type(node.type_name):
            self.report(f"Tipo desconocido '{node.type_name}'", node.lineno)
        
        # Si la variable tiene inicializador, verificar compatibilidad de tipos
        if node.value:
            val_type = self.visit(node.value)
            # Regla 6.1: La compatibilidad de tipos en inicialización
            if not check_binop('=', node.type_name, val_type):
                self.report(f"No se puede inicializar '{node.name}' ({node.type_name}) con tipo {val_type}", node.lineno)
        
        # Registrar la variable en la tabla de símbolos del alcance actual
        try:
            self.symtab.add(node.name, node)
        except Exception as e:
            self.report(str(e), node.lineno)

    @multimethod
    def visit(self, node: Assignment):
        """Procesa la asignación a una variable (Regla 6.1).
        
        Verificar:
        1. Que el identificador esté declarado
        2. Que los tipos sean compatibles
        """
        # Regla 6.1: Buscar el símbolo en la tabla (respetando alcances léxicos)
        sym = self.symtab.get(node.name)
        if not sym:
            self.report(f"Identificador '{node.name}' no declarado", node.lineno)
            return "error"
        
        # Obtener el tipo de la variable destino
        target_type = getattr(sym, 'type_name', 'error')
        # Calcular el tipo del valor a asignar
        val_type = self.visit(node.value)
        
        # Verificar compatibilidad: no se pueden asignar tipos incompatibles
        if not check_binop('=', target_type, val_type):
            self.report(f"No se puede asignar {val_type} a variable '{node.name}' ({target_type})", node.lineno)
        return target_type

    # =============== ESTRUCTURAS DE CONTROL (if, while, etc.) ===============

    @multimethod
    def visit(self, node: IfStmt):
        """Verifica una sentencia if (Regla 6.5 y 5.2).
        
        Verificar:
        1. Que la condición sea de tipo boolean
        2. Crear nuevos alcances para bloques then y else
        """
        # Regla 6.5: La condición debe ser de tipo boolean (no integer, boolean, etc.)
        cond_type = self.visit(node.condition)
        if cond_type != "boolean":
            self.report(f"La condición del 'if' debe ser boolean, se recibió '{cond_type}'", node.lineno)
        
        # Regla 5.2: Los bloques crean nuevos alcances independientes
        self.symtab = Symtab("if_then", parent=self.symtab)
        for stmt in node.then_block:
            self.visit(stmt)
        # Volver al alcance anterior
        self.symtab = self.symtab.parent
        
        # Procesar el bloque else si existe (también con nuevo alcance)
        if node.else_block:
            self.symtab = Symtab("if_else", parent=self.symtab)
            for stmt in node.else_block:
                self.visit(stmt)
            self.symtab = self.symtab.parent

    @multimethod
    def visit(self, node: WhileStmt):
        """Verifica una sentencia while (Regla 6.5 y 5.2).
        
        Verificar:
        1. Que la condición sea de tipo boolean
        2. Crear nuevo alcance para el cuerpo del bucle
        """
        # Regla 6.5: La condición debe ser de tipo boolean
        cond_type = self.visit(node.condition)
        if cond_type != "boolean":
            self.report(f"La condición del 'while' debe ser boolean, se recibió '{cond_type}'", node.lineno)
        
        # Regla 5.2: El cuerpo del while tiene su propio alcance
        self.symtab = Symtab("while_body", parent=self.symtab)
        for stmt in node.body:
            self.visit(stmt)
        # Volver al alcance anterior
        self.symtab = self.symtab.parent

    # =============== EXPRESIONES (binarias, unarias, llamadas) ===============

    @multimethod
    def visit(self, node: BinaryOp):
        """Verifica una operación binaria (Regla 6.2, 6.3, 6.4 y 5.5).
        
        Verificar:
        1. Que los operandos izquierdo y derecho sean válidos
        2. Que la operación sea válida para esos tipos
        3. Anotar el nodo con el tipo resultante
        """
        # Obtener el tipo de cada operando
        left_t = self.visit(node.left)
        right_t = self.visit(node.right)
        # Verificar si la operación es válida para esos tipos
        res_t = check_binop(node.op, left_t, right_t)
        
        if res_t == "error":
            self.report(f"Operación '{node.op}' no válida entre {left_t} y {right_t}", node.lineno)
        
        # Regla 5.5: Anotar el nodo con su tipo resultante para uso posterior
        node.type = res_t
        return res_t

    @multimethod
    def visit(self, node: UnaryOp):
        """Verifica una operación unaria (Regla 6.2 y 5.5).
        
        Verificar:
        1. Que el operando sea válido
        2. Que la operación unaria sea válida para ese tipo
        3. Anotar el nodo con el tipo resultante
        """
        operand_t = self.visit(node.operand)
        # Verificar compatibilidad del operador unario con el tipo del operando
        res_t = check_unaryop(node.op, operand_t)
        if res_t == "error":
            self.report(f"Operador unario '{node.op}' no válido para {operand_t}", node.lineno)
        # Regla 5.5: Anotar tipo resultante
        node.type = res_t
        return res_t

    @multimethod
    def visit(self, node: FunctionCall):
        """Verifica una llamada a función (Regla 5.4 y 6.6).
        
        Verificar:
        1. Que la función esté definida
        2. Que el número de argumentos coincida
        3. Que los tipos de argumentos sean compatibles
        4. Anotar el tipo de retorno de la función
        """
        # Regla 5.4: Buscar la función en la tabla de símbolos
        sym = self.symtab.get(node.name)
        if not sym or not isinstance(sym, Function):
            self.report(f"Función '{node.name}' no definida", node.lineno)
            return "error"
        
        # Verificar que el número de argumentos coincida
        if len(node.args) != len(sym.params):
            self.report(f"La función '{node.name}' espera {len(sym.params)} argumentos, recibió {len(node.args)}", node.lineno)
        else:
            # Verificar que cada argumento tenga el tipo correcto
            for i, arg in enumerate(node.args):
                arg_t = self.visit(arg)
                param_t = sym.params[i].type_name
                if arg_t != param_t:
                    self.report(f"Argumento {i+1} de '{node.name}' debe ser {param_t}, se recibió {arg_t}", node.lineno)
        
        # Anotar el tipo de retorno de la función
        node.type = sym.return_type
        return sym.return_type

    @multimethod
    def visit(self, node: ReturnStmt):
        """Verifica una sentencia return (Regla 6.6).
        
        Verificar:
        1. Que el tipo del valor retornado coincida con el tipo declarado de la función
        2. Que si no hay expresión, la función sea void
        """
        # Regla 6.6: El tipo de retorno debe coincidir con el declarado
        if node.expr:
            ret_type = self.visit(node.expr)
        else:
            ret_type = "void"
            
        if ret_type != self.current_return_type:
            self.report(f"Se esperaba retorno de tipo {self.current_return_type}, pero se obtuvo {ret_type}", node.lineno)

    # =============== IDENTIFICADORES, LITERALES Y TIPOS PRIMITIVOS ===============

    @multimethod
    def visit(self, node: Identifier):
        """Verifica que un identificador esté declarado (Regla 5.1).
        
        Busca el símbolo en la tabla respetando alcances léxicos
        y devuelve su tipo.
        """
        # Regla 5.1: El identificador debe estar declarado
        symbol = self.symtab.get(node.name)
        if not symbol:
            self.report(f"Identificador '{node.name}' no declarado", node.lineno)
            return "error"
        
        # Si es una variable, devolver su tipo declarado
        if hasattr(symbol, 'type_name'):
            return symbol.type_name
        # Si es una función referenciada como valor, devolver su tipo de retorno
        if hasattr(symbol, 'return_type'):
            return symbol.return_type
        return "error"

    # Métodos para literales: devuelven el tipo primitivo
    @multimethod
    def visit(self, node: IntLiteral):
        """Literal entero tiene tipo 'integer'."""
        return "integer"
    
    @multimethod
    def visit(self, node: FloatLiteral):
        """Literal flotante tiene tipo 'float'."""
        return "float"
    
    @multimethod
    def visit(self, node: BooleanLiteral):
        """Literal booleano tiene tipo 'boolean'."""
        return "boolean"
    
    @multimethod
    def visit(self, node: StringLiteral):
        """Literal de cadena tiene tipo 'string'."""
        return "string"