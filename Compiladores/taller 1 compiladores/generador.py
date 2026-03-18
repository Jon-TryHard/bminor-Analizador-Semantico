import os
from railroad import Diagram, Sequence, Choice, Terminal, NonTerminal, Optional, ZeroOrMore

def T(x): return Terminal(x)
def N(x): return NonTerminal(x)

def guardar_svg(diagrama, nombre):
    """Función auxiliar para guardar el archivo."""
    with open(f"out/svg/{nombre}.svg", "w", encoding="utf-8") as f:
        diagrama.writeSvg(f.write)

def generar_bonus_b(regla_texto, nombre_archivo):
    """BONUS B: Generación semi-automática.
        Divide la cadena por espacios. Si la palabra está en MAYÚSCULAS, 
                    es un Terminal; si está en minúsculas, es un NonTerminal."""

    # Limpiamos la regla (quitamos el nombre de la regla y el ::=)
    cuerpo = regla_texto.split("::=")[1].strip().split(" ")
    
    elementos = []
    for p in cuerpo:
        # Los símbolos como ( ) { } o palabras en mayúsculas son Terminales
        if not p.islower() or p in ["(", ")", "{", "}", "[", "]", ";", ":", ","]:
            elementos.append(T(p))
        else:
            elementos.append(N(p))
            
    diagrama = Diagram(Sequence(*elementos))
    guardar_svg(diagrama, nombre_archivo)
    print(f"Bonus B: Generado automáticamente -> {nombre_archivo}.svg")

def generar_diagramas():
    if not os.path.exists('out/svg'):
        os.makedirs('out/svg')

    # 1. WHILE (Control)
    diag_while = Diagram(T("while"), T("("), N("opt_expr"), T(")"), Choice(0, N("closed_stmt"), N("open_stmt")))
    guardar_svg(diag_while, "while_stmt")

    # 2. TERNARIO
    diag_ternario = Diagram(N("expr2"), T("?"), N("expr1"), T(":"), N("expr1"))
    guardar_svg(diag_ternario, "expr_ternary")

    # 3. CLASES
    diag_class = Diagram(T("class"), T("ID"), T("{"), ZeroOrMore(N("class_member")), T("}"))
    guardar_svg(diag_class, "class_decl")

    # 4. ASIGNACIÓN COMPUESTA
    diag_assign = Diagram(N("lval"), Choice(0, T("="), T("+="), T("-="), T("*="), T("/=")), N("expr1"))
    guardar_svg(diag_assign, "assignment_ops")

    # 5. NEW
    diag_new = Diagram(T("new"), T("ID"), T("("), N("opt_expr_list"), T(")"))
    guardar_svg(diag_new, "expr_new")

    # 6. ACCESO (.)
    diag_dot = Diagram(N("expr9"), T("."), T("ID"))
    guardar_svg(diag_dot, "expr_dot_access")
 
    # 7. INC / DEC
    diag_inc_dec = Diagram(Choice(0, Sequence(Choice(0, T("++"), T("--")), N("expr8")), Sequence(N("expr9"), Choice(0, T("++"), T("--")))))
    guardar_svg(diag_inc_dec, "expr_inc_dec")

    # --- EJECUCIÓN DEL BONUS B ---
    # Aquí pasamos reglas simples del grammar.txt como texto
    generar_bonus_b("print_stmt ::= PRINT opt_expr_list ;", "bonus_print")
    generar_bonus_b("return_stmt ::= RETURN opt_expr ;", "bonus_return")
    generar_bonus_b("if_cond ::= IF ( opt_expr )", "bonus_if_cond")

    print("¡Todos los diagramas (incluyendo Bonus) generados en out/svg/!")

if __name__ == "__main__":
    generar_diagramas()