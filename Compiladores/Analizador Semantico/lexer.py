"""Análisis léxico (tokenización) para el lenguaje B-Minor.

Este módulo implementa el escáner que lee el código fuente carácter por carácter
y lo divide en tokens reconocibles (palabras clave, identificadores, operadores,
literales, etc.).
"""

import re

class Lexer:
    """Tokenizador basado en expresiones regulares para B-Minor.
    
    Atributos:
        token_specification: Lista de pares (nombre_token, regex) que definen
                           los patrones reconocibles del lenguaje
        tok_regex: Expresión regular compilada que combina todos los patrones
    """
    
    def __init__(self):
        """Inicializa el análisis léxico definiendo los patrones de tokens."""
        # Especificación de tokens con sus patrones en expresión regular
        # El orden importa: los patrones se prueban en este orden
        self.token_specification = [
            ('NUMBER',  r'\d+'),                              # Números enteros
            ('TYPE',    r'\b(integer|boolean|char|string|float)\b'),  # Palabras clave de tipos
            ('RETURN',  r'\breturn\b'),                       # Palabra clave return
            ('FUNC',    r'\b(function|func)\b'),              # Palabra clave function
            ('ID',      r'[A-Za-z_][A-Za-z0-9_]*'),           # Identificadores
            ('OP',      r'[+\-*/%<>=!&|]+'),                  # Operadores
            ('LBRACE',  r'\{'),                               # Llave de apertura
            ('RBRACE',  r'\}'),                               # Llave de cierre
            ('LPAREN',  r'\('),                               # Paréntesis de apertura
            ('RPAREN',  r'\)'),                               # Paréntesis de cierre
            ('COLON',   r':'),                                # Dos puntos
            ('ASSIGN',  r'='),                                # Operador de asignación
            ('COMMA',   r','),                                # Coma
            ('SEMI',    r';'),                                # Punto y coma
            ('SPACE',   r'\s+'),                              # Espacios en blanco
            ('IF',      r'\bif\b'),                           # Palabra clave if
            ('ELSE',    r'\belse\b'),                         # Palabra clave else
            ('WHILE',   r'\bwhile\b'),                        # Palabra clave while
        ]
        # Compilar una expresión regular que reconoce cualquier token válido
        self.tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in self.token_specification)

    def tokenize(self, source):
        """Convierte el código fuente en una lista de tokens.
        
        Args:
            source: Cadena con el código fuente a analizar
            
        Returns:
            Lista de diccionarios con estructura:
            {'type': str, 'value': str, 'line': int}
        """
        tokens = []
        line_num = 1  # Contador de líneas para reportes de error
        
        # Buscar todos los coincidencias en el código fuente
        for m in re.finditer(self.tok_regex, source):
            # Identificar el tipo de token reconocido
            kind = m.lastgroup
            value = m.group()
            
            # Actualizar contador de líneas cuando hay saltos de línea
            if kind == 'SPACE':
                line_num += value.count('\n')
                continue  # No incluir espacios en blanco en la salida
            
            # Agregar el token a la lista con su información
            tokens.append({
                'type': kind,
                'value': value,
                'line': line_num
            })
        
        return tokens