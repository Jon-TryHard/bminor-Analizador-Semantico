# Analizador Semántico de B-Minor en Python

## Estudiantes

- **Jonathan David Ochoa Echeverri**
- **Juan Camilo Gil Ramírez**
- **Juan José Ruiz Mellizo**

---

## Introducción

Este proyecto implementa un **analizador semántico** para el lenguaje de programación **B-Minor** en Python. El analizador verifica la coherencia semántica de programas B-Minor escritos sin errores sintácticos, detectando problemas como:

- Identificadores no declarados
- Redeclaraciones de variables
- Errores de tipo en expresiones y asignaciones
- Violaciones de tipos en operadores
- Incompatibilidades en llamadas a funciones
- Retornos con tipos incorrectos

---

## Estructura del Proyecto



bminor-Analizador-Semantico/
├── IR/                           # Código fuente del analizador
│   ├── lexer.py                  # Análisis léxico (tokenización)
│   ├── parser.py                 # Análisis sintáctico (construcción del AST)
│   ├── model.py                  # Definición del Abstract Syntax Tree (AST)
│   ├── symtab.py                 # Tabla de símbolos con alcances léxicos
│   ├── checker.py                # Analizador semántico (verificación de reglas)
│   └── main.py                   # Punto de entrada para ejecutar pruebas
├── tests/                        # Batería de pruebas del proyecto
│   ├── good/                     # Programas semánticamente válidos
│   │   ├── good0.bminor
│   │   └── ...
│   └── bad/                      # Programas con errores semánticos
│       ├── bad0.bminor
│       └── ...
└── README.md                     # Este archivo


---

## Cómo Ejecutar el Analizador Semántico

### Requisitos

- Python 3.10 o superior
- Librería `multimethod` (para el patrón Visitor)
- Librería `rich` (para impresión formateada de tablas de símbolos)

Instalar dependencias dentro de tu entorno virtual (`venv`):

```bash
pip install multimethod rich
```


***Ejecución Básica
Al estar todos los scripts en la raíz del proyecto, puedes ejecutar los análisis directamente:

Para analizar toda la batería de pruebas de las carpetas good y bad de forma automática:

```
python main.py
```

***Para analizar un archivo individual dentro de las carpetas de pruebas:

-Prueba válida (Good):
```
python main.py checker test/good/good0.bminor
```


-Prueba con errores (Bad):
```
python main.py checker test/bad/bad0.bminor
```

Salida EsperadaArchivo sin errores semánticos:Probando: test/good/good0.bminor
    -[GOOD] Sin errores semánticos.
semantic check: success
Archivo con errores:Probando: test/bad/bad0.bminor
    -[BAD] Error semántico (línea 8): Identificador 'x' no declarado
semantic check: failed







