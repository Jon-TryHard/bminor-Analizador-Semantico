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
            # Palabras clave de tipos y control de flujo
            ('FLOAT_LITERAL', r'\d+\.\d+'),                    # Números flotantes (antes de NUMBER)
            ('NUMBER',     r'\d+'),                            # Números enteros
            ('STRING',     r'"(?:[^"\\]|\\.)*"'),              # Strings con comillas dobles
            ('CHAR',       r"'(?:[^'\\]|\\.)'"),               # Caracteres con comillas simples
            ('TRUE',       r'\btrue\b'),                       # Booleano true
            ('FALSE',      r'\bfalse\b'),                      # Booleano false
            ('TYPE',       r'\b(integer|boolean|char|string|float)\b'),  # Tipos
            ('RETURN',     r'\breturn\b'),                     # Palabra clave return
            ('VOID',       r'\bvoid\b'),                       # Tipo void
            ('IF',         r'\bif\b'),                         # Palabra clave if
            ('ELSE',       r'\belse\b'),                       # Palabra clave else
            ('WHILE',      r'\bwhile\b'),                      # Palabra clave while
            ('FOR',        r'\bfor\b'),                        # Palabra clave for
            ('ARRAY',      r'\barray\b'),                      # Palabra clave array
            ('FUNC',       r'\b(function|func)\b'),            # Palabra clave function
            ('ID',         r'[A-Za-z_][A-Za-z0-9_]*'),         # Identificadores
            
            # Operadores incluyendo comparación y lógicos
            ('EQL',        r'=='),                             # Operador ==
            ('NEQ',        r'!='),                             # Operador !=
            ('LEQ',        r'<='),                             # Operador <=
            ('GEQ',        r'>='),                             # Operador >=
            ('AND',        r'&&'),                             # Operador &&
            ('OR',         r'\|\|'),                           # Operador ||
            ('LT',         r'<'),                              # Operador <
            ('GT',         r'>'),                              # Operador >
            ('PLUS',       r'\+'),                             # Operador +
            ('MINUS',      r'-'),                              # Operador -
            ('MULT',       r'\*'),                             # Operador *
            ('DIV',        r'/'),                              # Operador /
            ('MOD',        r'%'),                              # Operador %
            ('NOT',        r'!'),                              # Operador !
            
            # Delimitadores y puntuación
            ('LBRACE',     r'\{'),                             # Llave de apertura
            ('RBRACE',     r'\}'),                             # Llave de cierre
            ('LPAREN',     r'\('),                             # Paréntesis de apertura
            ('RPAREN',     r'\)'),                             # Paréntesis de cierre
            ('LBRACKET',   r'\['),                             # Corchete de apertura
            ('RBRACKET',   r'\]'),                             # Corchete de cierre
            ('COLON',      r':'),                              # Dos puntos
            ('ASSIGN',     r'='),                              # Operador de asignación
            ('COMMA',      r','),                              # Coma
            ('SEMI',       r';'),                              # Punto y coma
            
            # Espacios en blanco
            ('SPACE',      r'\s+'),                            # Espacios en blanco
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
        # Primero, eliminar comentarios del código fuente
        source = self._remove_comments(source)
        
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

    def _remove_comments(self, source):
        """Elimina comentarios del código fuente.
        
        Soporta:
        - Comentarios de bloque: /* ... */
        - Comentarios de línea: // ...
        
        Args:
            source: Código fuente con comentarios
            
        Returns:
            Código fuente sin comentarios, preservando nuevas líneas
        """
        result = []
        i = 0
        line_count = source.count('\n', 0, 0)
        
        while i < len(source):
            # Detectar comentario de bloque /* ... */
            if i < len(source) - 1 and source[i:i+2] == '/*':
                # Buscar el cierre del comentario
                end = source.find('*/', i + 2)
                if end == -1:
                    # Comentario no cerrado, ignorar hasta el final
                    break
                # Preservar saltos de línea en el comentario
                comment_section = source[i+2:end]
                result.append('\n' * comment_section.count('\n'))
                i = end + 2
            
            # Detectar comentario de línea // ...
            elif i < len(source) - 1 and source[i:i+2] == '//':
                # Buscar el fin de la línea
                end = source.find('\n', i)
                if end == -1:
                    # Comentario hasta el final del archivo
                    break
                # Saltar hasta la siguiente línea
                i = end
            
            else:
                result.append(source[i])
                i += 1
        
        return ''.join(result)