import re
from model import *
from error import report_error

class Parser:
    def __init__(self, source):
        self.tokens = self._tokenize(source)
        self.pos = 0

    def _tokenize(self, source):
        # Tokenizador simple para el ejemplo
        token_specification = [
            ('NUMBER',  r'\d+'),
            ('ID',      r'[A-Za-z_][A-Za-z0-9_]*'),
            ('OP',      r'[+\-*/]'),
            ('LBRACE',  r'\{'),
            ('RBRACE',  r'\}'),
            ('LPAREN',  r'\('),
            ('RPAREN',  r'\)'),
            ('SEMI',    r';'),
            ('SPACE',   r'\s+'),
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        return [m for m in re.finditer(tok_regex, source) if m.lastgroup != 'SPACE']

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type=None):
        token = self.peek()
        if not token: report_error("Fin de archivo inesperado")
        if expected_type and token.lastgroup != expected_type:
            report_error(f"Se esperaba {expected_type}, se obtuvo {token.lastgroup}")
        self.pos += 1
        return token

    def parse_expression(self):
        # Maneja: Termino (OP Termino)*
        left = self.parse_term()
        while self.peek() and self.peek().lastgroup == 'OP':
            op = self.consume().group()
            right = self.parse_term()
            left = BinaryOp(op, left, right)
        return left

    def parse_term(self):
        token = self.consume()
        if token.lastgroup == 'NUMBER': return IntLiteral(int(token.group()))
        if token.lastgroup == 'ID': return VarReference(token.group())
        report_error(f"Término no válido: {token.group()}")

    def parse_function(self):
        # simplificado: id ( ) { return expr ; }
        name = self.consume('ID').group()
        self.consume('LPAREN'); self.consume('RPAREN')
        self.consume('LBRACE')
        
        body = []
        if self.peek().group() == 'return':
            self.consume() # consume 'return'
            expr = self.parse_expression()
            self.consume('SEMI')
            body.append(ReturnStmt(expr))
        
        self.consume('RBRACE')
        return Function(name, body)

    def parse_program(self):
        functions = []
        while self.pos < len(self.tokens):
            functions.append(self.parse_function())
        return Program(functions)

def parse(source):
    try:
        p = Parser(source)
        return p.parse_program()
    except Exception as e:
        report_error(str(e))