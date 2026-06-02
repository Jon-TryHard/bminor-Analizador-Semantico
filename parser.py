"""Análisis sintáctico para el lenguaje B-Minor.

Este módulo implementa un parser recursivo descendente para construir el AST
desde la secuencia de tokens producida por el lexer.
"""

from model import *


class Parser:
    """Parser recursivo descendente para B-Minor."""

    PRECEDENCE = {
        'OR': 1,
        'AND': 2,
        'EQL': 3,
        'NEQ': 3,
        'LT': 4,
        'LEQ': 4,
        'GT': 4,
        'GEQ': 4,
        'PLUS': 5,
        'MINUS': 5,
        'MULT': 6,
        'DIV': 6,
        'MOD': 6,
        'POW': 7,
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def consume(self, expected_type=None):
        tok = self.peek()
        if not tok:
            raise Exception("Fin de archivo inesperado")
        if expected_type and tok['type'] != expected_type:
            raise Exception(
                f"Se esperaba {expected_type} en línea {tok['line']}, pero se obtuvo {tok['type']}"
            )
        self.pos += 1
        return tok

    def _line(self):
        tok = self.peek()
        return tok['line'] if tok else 0

    # ---------- Tipos ----------

    def parse_type(self):
        tok = self.peek()
        if not tok:
            raise Exception("Tipo esperado al final del archivo")

        if tok['type'] == 'ARRAY':
            self.consume('ARRAY')
            self.consume('LBRACKET')
            size_expr = None
            if self.peek() and self.peek()['type'] != 'RBRACKET':
                if self.peek()['type'] == 'NUMBER':
                    num_tok = self.consume('NUMBER')
                    size_expr = IntLiteral(value=int(num_tok['value']), lineno=num_tok['line'])
                elif self.peek()['type'] == 'ID':
                    id_tok = self.consume('ID')
                    size_expr = Identifier(name=id_tok['value'], lineno=id_tok['line'])
                else:
                    bad = self.peek()
                    raise Exception(f"Tamaño de array inválido en línea {bad['line']}")
            self.consume('RBRACKET')
            base, nested_sizes = self.parse_type()
            # Normalizar tipos de array: "array_of_BASE"
            sizes = []
            if size_expr is not None:
                sizes.append(size_expr)
            sizes.extend(nested_sizes)
            return f"array_of_{base}", sizes

        if tok['type'] == 'TYPE':
            return self.consume('TYPE')['value'], []

        if tok['type'] == 'VOID':
            return self.consume('VOID')['value'], []

        # Tipos de clase (identificadores de usuario)
        if tok['type'] == 'ID':
            return self.consume('ID')['value'], []

        raise Exception(f"Tipo esperado en línea {tok['line']}, pero se obtuvo {tok['type']}")

    # ---------- Expresiones ----------

    def parse_expression(self, min_prec=1):
        left = self.parse_unary()

        while True:
            op_tok = self.peek()
            if not op_tok:
                break

            op_type = op_tok['type']
            prec = self.PRECEDENCE.get(op_type)
            if prec is None or prec < min_prec:
                break

            self.consume()
            # '^' se considera asociativo por la derecha.
            next_min_prec = prec if op_type == 'POW' else prec + 1
            right = self.parse_expression(next_min_prec)
            left = BinaryOp(op=op_tok['value'], left=left, right=right, lineno=op_tok['line'])

        return left

    def parse_unary(self):
        tok = self.peek()
        if not tok:
            raise Exception("Expresión esperada al final del archivo")

        if tok['type'] in ('MINUS', 'NOT', 'PLUS'):
            op_tok = self.consume()
            operand = self.parse_unary()
            return UnaryOp(op=op_tok['value'], operand=operand, lineno=op_tok['line'])

        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()

        while True:
            tok = self.peek()
            if not tok:
                break

            if tok['type'] == 'LPAREN':
                if not isinstance(node, Identifier):
                    raise Exception(f"Llamada inválida en línea {tok['line']}")
                self.consume('LPAREN')
                args = []
                if self.peek() and self.peek()['type'] != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.peek() and self.peek()['type'] == 'COMMA':
                        self.consume('COMMA')
                        args.append(self.parse_expression())
                self.consume('RPAREN')
                node = FunctionCall(name=node.name, args=args, lineno=tok['line'])
                continue

            if tok['type'] == 'DOT':
                self.consume('DOT')
                member_tok = self.consume('ID')
                member_name = member_tok['value']
                line = member_tok['line']

                if self.peek() and self.peek()['type'] == 'LPAREN':
                    self.consume('LPAREN')
                    args = []
                    if self.peek() and self.peek()['type'] != 'RPAREN':
                        args.append(self.parse_expression())
                        while self.peek() and self.peek()['type'] == 'COMMA':
                            self.consume('COMMA')
                            args.append(self.parse_expression())
                    self.consume('RPAREN')
                    node = MethodCall(obj=node, method=member_name, args=args, lineno=line)
                else:
                    node = MemberAccess(obj=node, member=member_name, lineno=line)
                continue

            if tok['type'] == 'LBRACKET':
                self.consume('LBRACKET')
                index = self.parse_expression()
                self.consume('RBRACKET')
                node = IndexExpr(array=node, index=index, lineno=tok['line'])
                continue

            if tok['type'] in ('INC', 'DEC'):
                op_tok = self.consume()
                node = PostfixOp(op=op_tok['value'], operand=node, lineno=op_tok['line'])
                continue

            break

        return node

    def parse_primary(self):
        tok = self.peek()
        if not tok:
            raise Exception("Expresión esperada al final del archivo")

        if tok['type'] == 'ID' and tok['value'] == 'new' and self.peek(1) and self.peek(1)['type'] == 'ID' and self.peek(2) and self.peek(2)['type'] == 'LPAREN':
            new_tok = self.consume('ID')
            class_tok = self.consume('ID')
            self.consume('LPAREN')
            args = []
            if self.peek() and self.peek()['type'] != 'RPAREN':
                args.append(self.parse_expression())
                while self.peek() and self.peek()['type'] == 'COMMA':
                    self.consume('COMMA')
                    args.append(self.parse_expression())
            self.consume('RPAREN')
            return NewExpr(class_name=class_tok['value'], args=args, lineno=new_tok['line'])

        if tok['type'] == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_expression()
            self.consume('RPAREN')
            return expr

        if tok['type'] == 'LBRACE':
            line = tok['line']
            self.consume('LBRACE')
            elements = []
            if self.peek() and self.peek()['type'] != 'RBRACE':
                elements.append(self.parse_expression())
                while self.peek() and self.peek()['type'] == 'COMMA':
                    self.consume('COMMA')
                    elements.append(self.parse_expression())
            self.consume('RBRACE')
            return ArrayLiteral(elements=elements, lineno=line)

        tok = self.consume()

        if tok['type'] == 'NUMBER':
            return IntLiteral(value=int(tok['value']), lineno=tok['line'])
        if tok['type'] == 'FLOAT_LITERAL':
            return FloatLiteral(value=float(tok['value']), lineno=tok['line'])
        if tok['type'] == 'TRUE':
            return BooleanLiteral(value=True, lineno=tok['line'])
        if tok['type'] == 'FALSE':
            return BooleanLiteral(value=False, lineno=tok['line'])
        if tok['type'] == 'STRING':
            value = tok['value'][1:-1]
            value = value.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
            return StringLiteral(value=value, lineno=tok['line'])
        if tok['type'] == 'CHAR':
            value = tok['value'][1:-1]
            return CharLiteral(value=value, lineno=tok['line'])
        if tok['type'] == 'ID':
            if tok['value'] == 'this':
                return Identifier(name='this', lineno=tok['line'])
            return Identifier(name=tok['value'], lineno=tok['line'])

        raise Exception(f"Expresión inválida en línea {tok['line']}: {tok['type']}")

    # ---------- Sentencias ----------

    def parse_block(self):
        lbrace = self.consume('LBRACE')
        statements = []
        while self.peek() and self.peek()['type'] != 'RBRACE':
            statements.append(self.parse_statement())
        self.consume('RBRACE')
        return BlockStmt(statements=statements, lineno=lbrace['line'])

    def parse_if(self):
        tok = self.consume('IF')
        self.consume('LPAREN')
        cond = self.parse_expression()
        self.consume('RPAREN')

        then_stmt = self.parse_statement()
        then_block = then_stmt.statements if isinstance(then_stmt, BlockStmt) else [then_stmt]

        else_block = None
        if self.peek() and self.peek()['type'] == 'ELSE':
            self.consume('ELSE')
            else_stmt = self.parse_statement()
            else_block = else_stmt.statements if isinstance(else_stmt, BlockStmt) else [else_stmt]

        return IfStmt(condition=cond, then_block=then_block, else_block=else_block, lineno=tok['line'])

    def parse_while(self):
        tok = self.consume('WHILE')
        self.consume('LPAREN')
        cond = self.parse_expression()
        self.consume('RPAREN')

        body_stmt = self.parse_statement()
        body = body_stmt.statements if isinstance(body_stmt, BlockStmt) else [body_stmt]
        return WhileStmt(condition=cond, body=body, lineno=tok['line'])

    def parse_for_clause_assignment_or_expr(self):
        expr = self.parse_expression()
        if self.peek() and self.peek()['type'] == 'ASSIGN':
            assign_tok = self.consume('ASSIGN')
            value = self.parse_expression()
            if isinstance(expr, Identifier):
                return Assignment(name=expr.name, value=value, lineno=expr.lineno)
            if isinstance(expr, IndexExpr):
                return ArrayAssignment(array=expr.array, index=expr.index, value=value, lineno=expr.lineno)
            if isinstance(expr, MemberAccess):
                return MemberAssignment(target=expr, value=value, lineno=expr.lineno)
            raise Exception(f"Asignación inválida en línea {assign_tok['line']}")
        return expr

    def parse_for(self):
        tok = self.consume('FOR')
        self.consume('LPAREN')

        init = None
        if self.peek() and self.peek()['type'] != 'SEMI':
            init = self.parse_for_clause_assignment_or_expr()
        self.consume('SEMI')

        condition = None
        if self.peek() and self.peek()['type'] != 'SEMI':
            condition = self.parse_expression()
        self.consume('SEMI')

        step = None
        if self.peek() and self.peek()['type'] != 'RPAREN':
            step = self.parse_for_clause_assignment_or_expr()
        self.consume('RPAREN')

        body_stmt = self.parse_statement()
        body = body_stmt.statements if isinstance(body_stmt, BlockStmt) else [body_stmt]
        return ForStmt(init=init, condition=condition, step=step, body=body, lineno=tok['line'])

    def parse_print(self):
        tok = self.consume('PRINT')
        args = []

        # print como instrucción: acepta formato con o sin paréntesis.
        if self.peek() and self.peek()['type'] == 'LPAREN':
            self.consume('LPAREN')
            if self.peek() and self.peek()['type'] != 'RPAREN':
                args.append(self.parse_expression())
                while self.peek() and self.peek()['type'] == 'COMMA':
                    self.consume('COMMA')
                    args.append(self.parse_expression())
            self.consume('RPAREN')
        else:
            if self.peek() and self.peek()['type'] != 'SEMI':
                args.append(self.parse_expression())
                while self.peek() and self.peek()['type'] == 'COMMA':
                    self.consume('COMMA')
                    args.append(self.parse_expression())

        self.consume('SEMI')
        return PrintStmt(args=args, lineno=tok['line'])

    def parse_return(self):
        tok = self.consume('RETURN')
        expr = None
        if self.peek() and self.peek()['type'] != 'SEMI':
            expr = self.parse_expression()
        self.consume('SEMI')
        return ReturnStmt(expr=expr, lineno=tok['line'])

    def parse_var_decl_from_name(self, name_tok):
        self.consume('COLON')
        var_type, array_sizes = self.parse_type()
        value = None
        if self.peek() and self.peek()['type'] == 'ASSIGN':
            self.consume('ASSIGN')
            value = self.parse_expression()
        self.consume('SEMI')
        return VarDeclaration(name=name_tok['value'], type_name=var_type, value=value, lineno=name_tok['line'], array_sizes=array_sizes)

    def parse_statement(self):
        tok = self.peek()
        if not tok:
            raise Exception("Sentencia esperada al final del archivo")

        if tok['type'] == 'LBRACE':
            return self.parse_block()

        if tok['type'] == 'IF':
            return self.parse_if()

        if tok['type'] == 'WHILE':
            return self.parse_while()

        if tok['type'] == 'FOR':
            return self.parse_for()

        if tok['type'] == 'RETURN':
            return self.parse_return()

        if tok['type'] == 'PRINT':
            return self.parse_print()

        if tok['type'] == 'ID' and self.peek(1) and self.peek(1)['type'] == 'COLON':
            name_tok = self.consume('ID')
            self.consume('COLON')
            if self.peek() and self.peek()['type'] == 'FUNC':
                raise Exception(
                    f"No se permite declarar funciones dentro de bloques (línea {name_tok['line']})"
                )
            var_type, array_sizes = self.parse_type()
            value = None
            if self.peek() and self.peek()['type'] == 'ASSIGN':
                self.consume('ASSIGN')
                value = self.parse_expression()
            self.consume('SEMI')
            return VarDeclaration(name=name_tok['value'], type_name=var_type, value=value, lineno=name_tok['line'], array_sizes=array_sizes)

        if tok['type'] == 'ID' and self.peek(1) and self.peek(1)['type'] == 'ASSIGN':
            expr = self.parse_expression()
            self.consume('ASSIGN')
            value = self.parse_expression()
            self.consume('SEMI')
            if isinstance(expr, Identifier):
                return Assignment(name=expr.name, value=value, lineno=expr.lineno)
            if isinstance(expr, IndexExpr):
                return ArrayAssignment(array=expr.array, index=expr.index, value=value, lineno=expr.lineno)
            if isinstance(expr, MemberAccess):
                return MemberAssignment(target=expr, value=value, lineno=expr.lineno)
            raise Exception(f"Asignación inválida en línea {tok['line']}")

        if tok['type'] == 'ID' and self.peek(1) and self.peek(1)['type'] == 'LBRACKET':
            expr = self.parse_expression()
            if self.peek() and self.peek()['type'] == 'ASSIGN':
                self.consume('ASSIGN')
                value = self.parse_expression()
                self.consume('SEMI')
                if isinstance(expr, IndexExpr):
                    return ArrayAssignment(array=expr.array, index=expr.index, value=value, lineno=expr.lineno)
                raise Exception(f"Asignación inválida en línea {tok['line']}")
            self.consume('SEMI')
            return ExprStmt(expr=expr, lineno=tok['line'])

        expr = self.parse_expression()
        if self.peek() and self.peek()['type'] == 'ASSIGN':
            assign_tok = self.consume('ASSIGN')
            value = self.parse_expression()
            self.consume('SEMI')
            if isinstance(expr, Identifier):
                return Assignment(name=expr.name, value=value, lineno=expr.lineno)
            if isinstance(expr, IndexExpr):
                return ArrayAssignment(array=expr.array, index=expr.index, value=value, lineno=expr.lineno)
            if isinstance(expr, MemberAccess):
                return MemberAssignment(target=expr, value=value, lineno=expr.lineno)
            raise Exception(f"Asignación inválida en línea {assign_tok['line']}")
        self.consume('SEMI')
        return ExprStmt(expr=expr, lineno=tok['line'])

    # ---------- Funciones y programa ----------

    def parse_parameter(self):
        name = self.consume('ID')
        self.consume('COLON')
        t_type, array_sizes = self.parse_type()
        return VarDeclaration(name=name['value'], type_name=t_type, lineno=name['line'], array_sizes=array_sizes)

    def parse_parameter_list(self):
        params = []
        self.consume('LPAREN')
        if self.peek() and self.peek()['type'] != 'RPAREN':
            params.append(self.parse_parameter())
            while self.peek() and self.peek()['type'] == 'COMMA':
                self.consume('COMMA')
                params.append(self.parse_parameter())
        self.consume('RPAREN')
        return params

    def parse_named_function_decl(self, name_tok):
        self.consume('FUNC')
        ret_type, _ = self.parse_type()
        params = self.parse_parameter_list()

        if self.peek() and self.peek()['type'] == 'ASSIGN':
            self.consume('ASSIGN')
            body_block = self.parse_block()
            return Function(name=name_tok['value'], return_type=ret_type, params=params, body=body_block.statements, lineno=name_tok['line'])

        self.consume('SEMI')
        return Function(name=name_tok['value'], return_type=ret_type, params=params, body=[], lineno=name_tok['line'])

    def parse_function_keyword_style(self):
        self.consume('FUNC')
        name_tok = self.consume('ID')
        params = self.parse_parameter_list()
        self.consume('COLON')
        ret_type, _ = self.parse_type()
        if self.peek() and self.peek()['type'] == 'ASSIGN':
            self.consume('ASSIGN')
        body_block = self.parse_block()
        return Function(name=name_tok['value'], return_type=ret_type, params=params, body=body_block.statements, lineno=name_tok['line'])

    def parse_class_declaration(self):
        class_tok = self.consume('ID')
        name_tok = self.consume('ID')
        self.consume('LBRACE')

        fields = []
        methods = []
        while self.peek() and self.peek()['type'] != 'RBRACE':
            member_name_tok = self.consume('ID')
            self.consume('COLON')

            if self.peek() and self.peek()['type'] == 'FUNC':
                method = self.parse_named_function_decl(member_name_tok)
                methods.append(method)
                continue

            member_type, array_sizes = self.parse_type()
            value = None
            if self.peek() and self.peek()['type'] == 'ASSIGN':
                self.consume('ASSIGN')
                value = self.parse_expression()
            self.consume('SEMI')
            fields.append(
                VarDeclaration(
                    name=member_name_tok['value'],
                    type_name=member_type,
                    value=value,
                    lineno=member_name_tok['line'],
                    array_sizes=array_sizes
                )
            )

        self.consume('RBRACE')
        return ClassDeclaration(name=name_tok['value'], fields=fields, methods=methods, lineno=class_tok['line'])

    def parse_declaration(self):
        tok = self.peek()
        if not tok:
            raise Exception("Declaración esperada al final del archivo")

        if tok['type'] == 'FUNC':
            return self.parse_function_keyword_style()

        if tok['type'] == 'ID' and tok['value'] == 'class' and self.peek(1) and self.peek(1)['type'] == 'ID' and self.peek(2) and self.peek(2)['type'] == 'LBRACE':
            return self.parse_class_declaration()

        if tok['type'] != 'ID':
            raise Exception(f"Declaración no esperada: {tok['type']} en línea {tok['line']}")

        name_tok = self.consume('ID')
        self.consume('COLON')

        if self.peek() and self.peek()['type'] == 'FUNC':
            return self.parse_named_function_decl(name_tok)

        # Declaración global de variable.
        var_type, array_sizes = self.parse_type()
        value = None
        if self.peek() and self.peek()['type'] == 'ASSIGN':
            self.consume('ASSIGN')
            value = self.parse_expression()
        self.consume('SEMI')
        return VarDeclaration(name=name_tok['value'], type_name=var_type, value=value, lineno=name_tok['line'], array_sizes=array_sizes)

    def parse(self):
        declarations = []
        while self.peek():
            declarations.append(self.parse_declaration())
        return Program(declarations=declarations)
