#!/usr/bin/env python3
"""Script para ejecutar pruebas en lote sobre los archivos de prueba."""

import os
import sys
import subprocess

def run_tests(directory):
    """Ejecuta pruebas sobre todos los archivos en un directorio."""
    results = {"pass": 0, "fail": 0}
    
    # Listar archivos en el directorio
    files = sorted([f for f in os.listdir(directory) if f.endswith('.bminor')])
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        
        # Ejecutar el analizador
        result = subprocess.run(
            [sys.executable, 'main.py', filepath],
            capture_output=True,
            text=True
        )
        
        # Determinar si la prueba pasó o falló
        # Archivos en good/ deben pasar (exit code 0)
        # Archivos en bad/ deben fallar (exit code 1)
        expected_pass = 'good' in directory
        actual_pass = result.returncode == 0
        
        if expected_pass == actual_pass:
            results["pass"] += 1
            status = "[PASS]"
        else:
            results["fail"] += 1
            status = "[FAIL]"
        
        print(f"{status}: {filename}")
        
        # Mostrar errores si es necesario
        if result.returncode != 0 and 'ERROR' in result.stdout:
            # Mostrar solo las líneas de error
            for line in result.stdout.split('\n'):
                if 'ERROR' in line or 'error' in line:
                    print(f"  > {line}")
    
    return results

if __name__ == '__main__':
    print("=" * 60)
    print("PRUEBAS ARCHIVOS VÁLIDOS (good/)")
    print("=" * 60)
    good_results = run_tests('tests/good')
    
    print("\n" + "=" * 60)
    print("PRUEBAS ARCHIVOS INVÁLIDOS (bad/)")
    print("=" * 60)
    bad_results = run_tests('tests/bad')
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    total_pass = good_results["pass"] + bad_results["pass"]
    total_fail = good_results["fail"] + bad_results["fail"]
    total = total_pass + total_fail
    
    print(f"Correctas: {total_pass}/{total}")
    print(f"Incorrectas: {total_fail}/{total}")
    print(f"Tasa de éxito: {100*total_pass//total}%")
