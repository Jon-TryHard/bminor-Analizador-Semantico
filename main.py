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

def run_test(filename, run_semantic=False, show_syntax=True):
    """Ejecuta el análisis sintáctico y opcionalmente el semántico en B-Minor.
    
    Args:
        filename: Ruta del archivo a analizar
        
    Returns:
        True si pasa sintaxis (y semántica si run_semantic=True)
        False si falla en cualquiera de las etapas ejecutadas
    """
    print(f"Probando: {filename}")
    
    # Leer el contenido del archivo
    with open(filename, 'r') as f:
        source = f.read()
    
    # Realizar los pasos del compilador en secuencia
    try:
        # Paso 1: Análisis léxico (tokenización)
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        
        # Paso 2: Análisis sintáctico (construcción del AST)
        parser = Parser(tokens)
        ast = parser.parse()

        if show_syntax:
            print("  [SINTÁCTICO] PASS")

        if not run_semantic:
            return True
        
        # Paso 3: Análisis semántico (verificación de reglas)
        checker = SemanticChecker()
        checker.visit(ast)
        
        # Evaluación del resultado
        if checker.errors:
            for err in checker.errors:
                print(f"  [BAD] {err}")
            return False
        else:
            print("  [GOOD] Sin errores semánticos.")
            return True
    except Exception as e:
        # Capturar errores no esperados (sintácticos o de otra índole)
        if run_semantic:
            print(f"  [BAD] Error previo al análisis semántico: {e}")
        else:
            print(f"  [SINTÁCTICO] FAIL - {e}")
        return False

# ============ EJEMPLOS DE USO ============
# Descomenta las líneas siguientes para probar archivos específicos:
#
# run_test('tests/good/good0.bminor')
# run_test('tests/bad/bad0.bminor')
#
def run_all_syntax_tests():
    """Ejecuta validación sintáctica en todos los casos de prueba."""
    ok = True
    for test_file in sorted(os.listdir('tests/good')):
        ok = run_test(f'tests/good/{test_file}') and ok
    for test_file in sorted(os.listdir('tests/bad')):
        ok = run_test(f'tests/bad/{test_file}') and ok
    return ok


def run_all_semantic_tests():
    """Ejecuta validación semántica en todos los casos de prueba.

    Convención esperada:
    - tests/good/* deben pasar sin errores semánticos.
    - tests/bad/* deben reportar errores semánticos.
    """
    ok = True
    print("=== GOOD (semantic) ===")
    for test_file in sorted(os.listdir('tests/good')):
        ok = run_test(f'tests/good/{test_file}', run_semantic=True, show_syntax=False) and ok

    print("=== BAD (semantic) ===")
    for test_file in sorted(os.listdir('tests/bad')):
        # En bad, lo correcto es que run_test devuelva False (hay errores)
        ok = (not run_test(f'tests/bad/{test_file}', run_semantic=True, show_syntax=False)) and ok

    return ok

# ============ INTERFAZ DE LÍNEA DE COMANDOS ============
if __name__ == '__main__':
    if len(sys.argv) < 2:
        success = run_all_semantic_tests()
        print("\nanalysis: semantic batch completed")
        sys.exit(0 if success else 1)

    if sys.argv[1] == 'checker':
        if len(sys.argv) < 3:
            print("Error: falta la ruta del archivo para checker")
            sys.exit(1)

        filename = sys.argv[2]
        if not os.path.exists(filename):
            print(f"Error: Archivo '{filename}' no encontrado")
            sys.exit(1)

        success = run_test(filename, run_semantic=True, show_syntax=False)
        if success:
            print("semantic check: success")
            sys.exit(0)

        print("semantic check: failed")
        sys.exit(1)

    # Ejecutar análisis sobre un archivo específico
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Error: Archivo '{filename}' no encontrado")
        sys.exit(1)

    run_semantic = len(sys.argv) > 2 and sys.argv[2] == '--semantic'
    success = run_test(filename, run_semantic=run_semantic)
    
    if success:
        if run_semantic:
            print("\nanalysis: syntax+semantic success")
        else:
            print("\nanalysis: syntax success")
        sys.exit(0)
    else:
        if run_semantic:
            print("\nanalysis: syntax/semantic failed")
        else:
            print("\nanalysis: syntax failed")
        sys.exit(1)
