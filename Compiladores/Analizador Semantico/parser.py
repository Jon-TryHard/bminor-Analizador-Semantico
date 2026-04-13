"""Análisis sintáctico para el lenguaje B-Minor.

Este módulo implementa un parser que construye el Abstract Syntax Tree (AST)
a partir de la secuencia de tokens generada por el análisis léxico.

Utiliza un análisis recursivo descendente (recursive descent parsing) para
interpretar la gramática del lenguaje.
"""

import re
from model import *

class Parser:
    """Parser recursivo descendente para B-Minor.
    
    Atributos:
        tokens: Lista de tokens a procesar
        pos: Posición actual en la secuencia de tokens
    """
    
    def __init__(self, tokens):
        """Inicializa el parser con una secuencia de tokens.
        
        Args:
            tokens: Lista de diccionarios con estructura {'type', 'value', 'line'}
        """
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        """Obtiene el token actual sin consumirlo.
        
        Returns:
            Diccionario del token actual, o None si se alcanzó el final
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None):
        """Consume el token actual y avanza el posicionador.
        
        Args:
            expected_type: Tipo de token esperado (opcional, para validación)
            
        Returns:
            Diccionario del token consumido
            
        Raises:
            Exception: Si se alcanzó fin de archivo inesperadamente
                      o si el token no coincide con el tipo esperado
        """
        tok = self.peek()
        if not tok:
            raise Exception("Fin de archivo inesperado")
        if expected_type and tok['type'] != expected_type:
            raise Exception(f"Se esperaba {expected_type} en línea {tok['line']}, pero se obtuvo {tok['type']}")
        self.pos += 1
        return tok

    # =============== ANÁLISIS DE EXPRESIONES ===============

    def parse_expression(self):
        """Analiza una expresión con operadores binarios.
        
        Maneja identificadores, números y operaciones binarias básicas.
        El análisis es iterativo para construir árboles correctos de operaciones.
        
        Returns:
            Nodo del AST representando la expresión
        """
        # Versión simplificada: comienza con el operando primario izquierdo
        left = self.parse_primary()
        
        # Procesar operadores binarios
        while self.peek() and self.peek()['type'] == 'OP':
            op_tok = self.consume('OP')
            right = self.parse_primary()
            left = BinaryOp(op=op_tok['value'], left=left, right=right, lineno=op_tok['line'])
        
        return left

    def parse_primary(self):
        """Analiza una expresión primaria (literal, identificador o llamada a función).
        
        Returns:
            Nodo del AST representando la expresión primaria
            
        Raises:
            Exception: Si la expresión no es válida
        """
        tok = self.consume()
        
        # Número entero literal
        if tok['type'] == 'NUMBER':
            return IntLiteral(value=int(tok['value']), lineno=tok['line'])
        
        # Identificador (posiblemente seguido de parámetros si es llamada a función)
        if tok['type'] == 'ID':
            # Verificar si es una llamada a función
            if self.peek() and self.peek()['type'] == 'LPAREN':
                self.consume('LPAREN')
                args = []
                # Procesar lista de argumentos si no está vacía
                if self.peek()['type'] != 'RPAREN':
                    args.append(self.parse_expression())
                    # Procesar argumentos adicionales separados por comas
                    while self.peek()['type'] == 'COMMA':
                        self.consume('COMMA')
                        args.append(self.parse_expression())
                self.consume('RPAREN')
                return FunctionCall(name=tok['value'], args=args, lineno=tok['line'])
            
            # Es solo un identificador (referencia a variable)
            return Identifier(name=tok['value'], lineno=tok['line'])
        
        raise Exception(f"Expresión inválida en línea {tok['line']}")

    # =============== ANÁLISIS DE SENTENCIAS ===============

    def parse_statement(self):
        """Analiza una sentencia (declaración, asignación, control, etc.).
        
        Returns:
            Nodo del AST representando la sentencia
            
        Raises:
            Exception: Si la sentencia no es reconocida
        """
        tok = self.peek()
        
        # Sentencia return
        if tok['type'] == 'RETURN':
            self.consume('RETURN')
            expr = self.parse_expression()
            self.consume('SEMI')
            return ReturnStmt(expr=expr, lineno=tok['line'])
        
        # Declaración o asignación (diferenciadas por ':' o '=')
        elif tok['type'] == 'ID':
            name_tok = self.consume('ID')
            
            # Declaración de variable: nombre : tipo [= valor];
            if self.peek()['type'] == 'COLON':
                self.consume('COLON')
                t_tok = self.consume('TYPE')
                val = None
                # Inicializador opcional
                if self.peek()['type'] == 'ASSIGN':
                    self.consume('ASSIGN')
                    val = self.parse_expression()
                self.consume('SEMI')
                return VarDeclaration(name=name_tok['value'], type_name=t_tok['value'], value=val, lineno=name_tok['line'])
            
            # Asignación a variable: nombre = valor;
            else:
                self.consume('ASSIGN')
                val = self.parse_expression()
                self.consume('SEMI')
                return Assignment(name=name_tok['value'], value=val, lineno=name_tok['line'])

        # Sentencia condicional if
        elif tok['type'] == 'IF':
            self.consume('IF')
            self.consume('LPAREN')
            cond = self.parse_expression()
            self.consume('RPAREN')
            then_b = self.parse_block()
            # Rama else opcional
            else_b = None
            if self.peek() and self.peek()['type'] == 'ELSE':
                self.consume('ELSE')
                else_b = self.parse_block()
            return IfStmt(condition=cond, then_block=then_b, else_block=else_b, lineno=tok['line'])

        raise Exception(f"Sentencia no reconocida: {tok['type']} en línea {tok['line']}")

    # =============== ANÁLISIS DE BLOQUES ===============

    def parse_block(self):
        """Analiza un bloque de sentencias entre llaves: { ... }
        
        Returns:
            Lista de nodos del AST representando las sentencias del bloque
        """
        self.consume('LBRACE')
        statements = []
        # Procesar sentencias hasta encontrar la llave de cierre
        while self.peek() and self.peek()['type'] != 'RBRACE':
            statements.append(self.parse_statement())
        self.consume('RBRACE')
        return statements

    def parse_function(self):
        self.consume('FUNC')
        name_tok = self.consume('ID')
        self.consume('LPAREN')
        params = []
        if self.peek()['type'] != 'RPAREN':
            params.append(self.parse_parameter())
            while self.peek()['type'] == 'COMMA':
                self.consume('COMMA')
                params.append(self.parse_parameter())
        self.consume('RPAREN')
        
        self.consume('COLON')
        ret_type = self.consume('TYPE')['value']
        
        # B-Minor a veces usa '=' antes del bloque de función
        if self.peek()['type'] == 'ASSIGN':
            self.consume('ASSIGN')
            
        body = self.parse_block()
        return Function(name=name_tok['value'], return_type=ret_type, params=params, body=body, lineno=name_tok['line'])

    def parse_parameter(self):
        name = self.consume