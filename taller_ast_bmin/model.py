from dataclasses import dataclass
from typing import List

@dataclass
class Node: pass  # Clase base

@dataclass
class IntLiteral(Node):
    value: int    # Representa un número (ej: 5)

@dataclass
class BinaryOp(Node):
    op: str       # Operador (+, -, *, /)
    left: Node    # Lado izquierdo de la operación
    right: Node   # Lado derecho

@dataclass
class ReturnStmt(Node):
    expr: Node    # Representa la instrucción 'return'

@dataclass
class Function(Node):
    name: str     # Nombre de la función (ej: main)
    body: List[Node] # Lista de instrucciones dentro de { }

@dataclass
class Program(Node):
    declarations: List[Function] # Raíz del árbol