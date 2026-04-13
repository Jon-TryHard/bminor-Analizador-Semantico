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

def run_test(filename):
    """Ejecuta el análisis semántico en un archivo B-Minor.
    
    Args:
        filename: Ruta del archivo a analizar
        
    Returns:
        True si el archivo es semánticamente válido (sin errores)
        False si se encontraron errores semánticos o críticos
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
        print(f"  [ERROR CRÍTICO] {e}")
        return False

# ============ EJEMPLOS DE USO ============
# Descomenta las líneas siguientes para probar archivos específicos:
#
# run_test('tests/good/good0.bminor')
# run_test('tests/bad/bad0.bminor')
#
# Para probar todos los archivos de una carpeta:
# for test_file in sorted(os.listdir('tests/good')):
#     run_test(f'tests/good/{test_file}')
# 
# for test_file in sorted(os.listdir('tests/bad')):
#     run_test(f'tests/bad/{test_file}')

# ============ INTERFAZ DE LÍNEA DE COMANDOS ============
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python main.py <archivo.bminor>")
        print("Ejemplo: python main.py tests/good/good0.bminor")
        sys.exit(1)
    
    # Ejecutar análisis semántico sobre el archivo especificado
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Error: Archivo '{filename}' no encontrado")
        sys.exit(1)
    
    success = run_test(filename)
    
    if success:
        print("\nsemantic check: success")
        sys.exit(0)
    else:
        print("\nsemantic check: failed")
        sys.exit(1)
