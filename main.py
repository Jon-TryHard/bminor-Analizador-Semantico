import sys
import os
import re
from lexer import Lexer
from parser import Parser
from checker import SemanticChecker


COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"


def _colorize_line_reference(message):
    pattern = r"(en línea\s+\d+|línea\s+\d+)"
    return re.sub(pattern, lambda m: f"{COLOR_BLUE}{m.group(1)}{COLOR_RESET}", message)


def _print_error(filename, message, syntax=False):
    colored_file = f"{COLOR_YELLOW}{filename}{COLOR_RESET}"
    colored_message = _colorize_line_reference(message)
    if syntax:
        colored_message = f"{COLOR_RED}{colored_message}{COLOR_RESET}"
    print(f"[ERROR] {colored_file}: {colored_message}")


def _resolve_input_file(path):
    normalized = os.path.normpath(path)
    candidates = [normalized]

    # Permite invocar con rutas cortas como bad/foo.bminor o good/foo.bminor
    if normalized.startswith(f"bad{os.sep}") or normalized.startswith(f"good{os.sep}"):
        candidates.append(os.path.normpath(os.path.join("tests", normalized)))
    else:
        candidates.append(os.path.normpath(os.path.join("tests", normalized)))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return normalized


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
            _print_error(filename, f"Error léxico: {e}")
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
            _print_error(filename, f"Error sintáctico: {e}", syntax=True)
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
        _print_error(filename, f"Error léxico: {e}")
        return False

    try:
        # Paso 2: Análisis sintáctico (construcción del AST)
        parser = Parser(tokens)
        ast = parser.parse()

    except Exception as e:
        # Si falla sintaxis, no se ejecuta el análisis semántico.
        _print_error(filename, f"Error sintáctico: {e}", syntax=True)
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
                _print_error(filename, err)
            return False
        return True
    except Exception as e:
        _print_error(filename, f"Error durante análisis semántico: {e}")
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
    first_error_group = True
    printed_semantic_output = False

    def _ensure_semantic_section_gap():
        nonlocal printed_semantic_output
        if not printed_semantic_output and not parse_ok:
            print()
            print()
        printed_semantic_output = True

    def _print_file_errors(filename, errors):
        nonlocal first_error_group
        if not errors:
            return
        _ensure_semantic_section_gap()
        if not first_error_group:
            print()
        for err in errors:
            _print_error(filename, err)
        first_error_group = False

    for filename in good_files:
        if filename not in ast_by_file:
            ok = False
            continue
        checker = SemanticChecker()
        checker.visit(ast_by_file[filename])
        if checker.errors:
            _print_file_errors(filename, checker.errors)
            ok = False

    for filename in bad_files:
        if filename not in ast_by_file:
            ok = False
            continue
        checker = SemanticChecker()
        checker.visit(ast_by_file[filename])
        if checker.errors:
            _print_file_errors(filename, checker.errors)
        else:
            _ensure_semantic_section_gap()
            if not first_error_group:
                print()
            _print_error(filename, "Se esperaban errores semánticos, pero no se detectó ninguno")
            first_error_group = False
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

        filename = _resolve_input_file(sys.argv[2])
        if not os.path.exists(filename):
            _print_error(filename, "Archivo no encontrado")
            sys.exit(1)

        success = run_test(filename, run_semantic=True, show_syntax=False)
        if success:
            print("analysis: success")
            sys.exit(0)
        sys.exit(1)

    # Ejecutar análisis sobre un archivo específico
    filename = _resolve_input_file(sys.argv[1])
    if not os.path.exists(filename):
        _print_error(filename, "Archivo no encontrado")
        sys.exit(1)

    extra_args = sys.argv[2:]
    run_semantic = '--syntax' not in extra_args
    success = run_test(filename, run_semantic=run_semantic)
    
    if success:
        print("analysis: success")
        sys.exit(0)

    sys.exit(1)
