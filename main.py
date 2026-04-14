"""Punto de entrada para ejecutar el análisis semántico de archivos B-Minor.

Este módulo facilita la prueba del analizador semántico sobre archivos de prueba
individuales o en lotes. Se encarga de orquestar los análisis léxico, sintáctico
y semántico en secuencia.
"""

import sys
import os
from lexer import Lexer
from parser import Parser
from checker import SemanticChecker


def _collect_test_files():
    """Devuelve la lista ordenada de archivos good y bad."""
    good_files = [f"tests/good/{name}" for name in sorted(os.listdir('tests/good'))]
    bad_files = [f"tests/bad/{name}" for name in sorted(os.listdir('tests/bad'))]
    return good_files, bad_files


def _batch_lex(files):
    """Ejecuta análisis léxico para todos los archivos.

    Si algún archivo falla, se detiene el pipeline por fases.
    """
    lexer = Lexer()
    tokens_by_file = {}
    ok = True

    for filename in files:
        try:
            with open(filename, 'r') as f:
                source = f.read()
            tokens_by_file[filename] = lexer.tokenize(source)
        except Exception as e:
            print(f"[ERROR] {filename}: Error léxico: {e}")
            ok = False

    return ok, tokens_by_file


def _batch_parse(files, tokens_by_file):
    """Ejecuta análisis sintáctico para todos los archivos ya tokenizados."""
    ast_by_file = {}
    ok = True

    for filename in files:
        if filename not in tokens_by_file:
            ok = False
            continue
        try:
            parser = Parser(tokens_by_file[filename])
            ast_by_file[filename] = parser.parse()
        except Exception as e:
            print(f"[ERROR] {filename}: Error sintáctico: {e}")
            ok = False

    return ok, ast_by_file

def run_test(filename, run_semantic=False, show_syntax=True):
    """Ejecuta el análisis sintáctico y opcionalmente el semántico en B-Minor.
    
    Args:
        filename: Ruta del archivo a analizar
        
    Returns:
        True si pasa sintaxis (y semántica si run_semantic=True)
        False si falla en cualquiera de las etapas ejecutadas
    """
    # Leer el contenido del archivo
    with open(filename, 'r') as f:
        source = f.read()
    
    # Realizar los pasos del compilador en secuencia
    ast = None
    try:
        # Paso 1: Análisis léxico (tokenización)
        lexer = Lexer()
        tokens = lexer.tokenize(source)

    except Exception as e:
        print(f"[ERROR] {filename}: Error léxico: {e}")
        return False

    try:
        # Paso 2: Análisis sintáctico (construcción del AST)
        parser = Parser(tokens)
        ast = parser.parse()

    except Exception as e:
        # Si falla sintaxis, no se ejecuta el análisis semántico.
        print(f"[ERROR] {filename}: Error sintáctico: {e}")
        return False

    if not run_semantic:
        return True

    try:
        # Paso 3: Análisis semántico (verificación de reglas)
        checker = SemanticChecker()
        checker.visit(ast)

        # Evaluación del resultado
        if checker.errors:
            for err in checker.errors:
                print(f"[ERROR] {filename}: {err}")
            return False
        return True
    except Exception as e:
        print(f"[ERROR] {filename}: Error durante análisis semántico: {e}")
        return False

# ============ EJEMPLOS DE USO ============
# Descomenta las líneas siguientes para probar archivos específicos:
#
# run_test('tests/good/good0.bminor')
# run_test('tests/bad/bad0.bminor')
#
def run_all_syntax_tests():
    """Ejecuta validación por fases: lexer de todos y luego parser de todos."""
    good_files, bad_files = _collect_test_files()
    all_files = good_files + bad_files

    lex_ok, tokens_by_file = _batch_lex(all_files)
    if not lex_ok:
        return False

    parse_ok, _ = _batch_parse(all_files, tokens_by_file)
    if not parse_ok:
        return False
    return True


def run_all_semantic_tests():
    """Ejecuta validación semántica en todos los casos de prueba.

    Convención esperada:
    - tests/good/* deben pasar sin errores semánticos.
    - tests/bad/* deben reportar errores semánticos.
    """
    good_files, bad_files = _collect_test_files()
    all_files = good_files + bad_files

    lex_ok, tokens_by_file = _batch_lex(all_files)
    parse_ok, ast_by_file = _batch_parse(all_files, tokens_by_file)

    ok = lex_ok and parse_ok
    for filename in good_files:
        if filename not in ast_by_file:
            ok = False
            continue
        checker = SemanticChecker()
        checker.visit(ast_by_file[filename])
        if checker.errors:
            for err in checker.errors:
                print(f"[ERROR] {filename}: {err}")
            ok = False

    for filename in bad_files:
        if filename not in ast_by_file:
            ok = False
            continue
        checker = SemanticChecker()
        checker.visit(ast_by_file[filename])
        if checker.errors:
            for err in checker.errors:
                print(f"[ERROR] {filename}: {err}")
        else:
            print(f"[ERROR] {filename}: Se esperaban errores semánticos, pero no se detectó ninguno")
            ok = False

    return ok

# ============ INTERFAZ DE LÍNEA DE COMANDOS ============
if __name__ == '__main__':
    if len(sys.argv) < 2:
        success = run_all_semantic_tests()
        if success:
            print("analysis: success")
        sys.exit(0 if success else 1)

    if sys.argv[1] == 'checker':
        if len(sys.argv) < 3:
            print("Error: falta la ruta del archivo para checker")
            sys.exit(1)

        filename = sys.argv[2]
        if not os.path.exists(filename):
            print(f"[ERROR] Archivo '{filename}' no encontrado")
            sys.exit(1)

        success = run_test(filename, run_semantic=True, show_syntax=False)
        if success:
            print("analysis: success")
            sys.exit(0)
        sys.exit(1)

    # Ejecutar análisis sobre un archivo específico
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"[ERROR] Archivo '{filename}' no encontrado")
        sys.exit(1)

    run_semantic = len(sys.argv) > 2 and sys.argv[2] == '--semantic'
    success = run_test(filename, run_semantic=run_semantic)
    
    if success:
        print("analysis: success")
        sys.exit(0)

    sys.exit(1)
