"""Definición del Abstract Syntax Tree (AST) para el lenguaje B-Minor.

Este módulo define todas las clases de nodos que componen el árbol de sintaxis
abstracta. Cada nodo representa una construcción del lenguaje (expresiones,
sentencias, declaraciones, etc.).

Cada nodo hereda de Node y almacena el número de línea para reportes de errores
precisos durante el análisis semántico.
"""

from dataclasses import dataclass, field
from typing import List, Optional

class Node:
    """Clase base para todos los nodos del AST.
    
    Atributos:
        lineno: Número de línea en el código fuente (para reportes de error)
    """
    lineno: int = 0

# =============== EXPRESIONES ===============

@dataclass
class IntLiteral:
    """Representa un número entero literal (ej: 42)."""
    value: int
    lineno: int = 0

@dataclass
class FloatLiteral:
    """Representa un número flotante literal (ej: 3.14)."""
    value: float
    lineno: int = 0

@dataclass
class StringLiteral:
    """Representa una cadena de texto literal (ej: "hola")."""
    value: str
    lineno: int = 0

@dataclass
class BooleanLiteral:
    """Representa un valor booleano literal (ej: true, false)."""
    value: bool
    lineno: int = 0

@dataclass
class Identifier:
    """Representa una referencia a un identificador (variable o función).
    
    El análisis semántico verificará que el identificador existe en la tabla de símbolos.
    """
    name: str
    lineno: int = 0

@dataclass
class UnaryOp:
    """Representa una operación unaria (ej: -x, !b).
    
    Atributos:
        op: Operador unario (-, !, etc.)
        operand: Expresión sobre la que se aplica el operador
        type: Anotación con el tipo resultante (asignado durante análisis semántico)
    """
    op: str
    operand: 'Node'
    lineno: int = 0
    type: Optional[str] = None

@dataclass
class BinaryOp:
    """Representa una operación binaria (ej: a + b, x < y).
    
    Atributos:
        op: Operador binario (+, -, *, /, %, <, <=, >, >=, ==, !=, &&, ||)
        left: Expresión del lado izquierdo
        right: Expresión del lado derecho
        type: Anotación con el tipo resultante (asignado durante análisis semántico)
    """
    op: str
    left: 'Node'
    right: 'Node'
    lineno: int = 0
    type: Optional[str] = None

@dataclass
class FunctionCall:
    """Representa una llamada a función (ej: print(x), sum(a, b)).
    
    Atributos:
        name: Nombre de la función a invocar
        args: Lista de expresiones pasadas como argumentos
        type: Anotación con el tipo de retorno de la función
    """
    name: str
    args: List['Node']
    lineno: int = 0
    type: Optional[str] = None

# =============== SENTENCIAS (STATEMENTS) ===============

@dataclass
class VarDeclaration:
    """Representa la declaración de una variable (ej: x: integer = 10;).
    
    Atributos:
        name: Identificador de la variable
        type_name: Tipo de dato (integer, boolean, string, etc.)
        value: Expresión inicializadora opcional
    """
    name: str
    type_name: str
    lineno: int = 0
    value: Optional['Node'] = None

@dataclass
class Assignment:
    """Representa la asignación a una variable ya declarada (ej: x = 20;).
    
    Se diferencia de VarDeclaration en que la variable ya debe estar declarada.
    
    Atributos:
        name: Identificador de la variable
        value: Nueva expresión a asignar
    """
    name: str
    value: 'Node'
    lineno: int = 0

@dataclass
class IfStmt:
    """Representa una sentencia condicional if-else.
    
    Atributos:
        condition: Expresión booleana a evaluar
        then_block: Lista de sentencias si la condición es verdadera
        else_block: Lista opcional de sentencias si la condición es falsa
    """
    condition: 'Node'
    then_block: List['Node']
    lineno: int = 0
    else_block: Optional[List['Node']] = None

@dataclass
class WhileStmt:
    """Representa un bucle while (ej: while (x > 0) { ... }).
    
    Atributos:
        condition: Expresión booleana a evaluar en cada iteración
        body: Lista de sentencias a ejecutar en cada iteración
    """
    condition: 'Node'
    body: List['Node']
    lineno: int = 0

@dataclass
class ReturnStmt:
    """Representa una sentencia return.
    
    Atributos:
        expr: Expresión a retornar, o None para funciones void
    """
    lineno: int = 0
    expr: Optional['Node'] = None

# =============== ESTRUCTURAS SUPERIORES ===============

@dataclass
class Function:
    """Representa la definición de una función.
    
    Atributos:
        name: Identificador de la función
        return_type: Tipo de dato del valor de retorno
        params: Lista de VarDeclaration para parámetros formales
        body: Lista de sentencias que forman el cuerpo
    """
    name: str
    return_type: str
    params: List['VarDeclaration']
    body: List['Node']
    lineno: int = 0

@dataclass
class Program:
    """Raíz del árbol de sintaxis (el programa completo).
    
    Atributos:
        declarations: Lista de declaraciones de nivel superior
                     (puede contener funciones y/o variables globales)
    """
    declarations: List['Node']
    lineno: int = 0