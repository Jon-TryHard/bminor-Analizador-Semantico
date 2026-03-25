import sys

def report_error(message, line=None):
    """Imprime un error formateado y detiene la ejecución."""
    loc = f" en línea {line}" if line else ""
    print(f"❌ [Error de Compilación]{loc}: {message}")
    sys.exit(1)