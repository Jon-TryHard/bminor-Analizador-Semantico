# Analizador Semántico de B-Minor en Python

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

```
bminor/
├── lexer.py              # Análisis léxico (tokenización)
├── parser.py             # Análisis sintáctico (construcción del AST)
├── model.py              # Definición del Abstract Syntax Tree (AST)
├── symtab.py             # Tabla de símbolos con alcances léxicos
├── checker.py            # Analizador semántico (verificación de reglas)
├── main.py               # Punto de entrada para ejecutar pruebas
├── README.md             # Este archivo
└── tests/
    ├── good/             # Programas semánticamente válidos
    │   ├── good0.bminor
    │   ├── good1.bminor
    │   └── ...
    └── bad/              # Programas con errores semánticos
        ├── bad0.bminor
        ├── bad1.bminor
        └── ...
```

---

## Cómo Ejecutar el Analizador Semántico

### Requisitos

- Python 3.7 o superior
- Librería `multimethod` (para el patrón Visitor)
- Librería `rich` (para impresión formateada de tablas de símbolos)

Instalar dependencias:
```bash
pip install multimethod rich
```

### Ejecución Básica

Para analizar un archivo individual:

```bash
python3 main.py
```

En el archivo `main.py`, descomentar y ejecutar:

```python
from main import run_test

# Analizar un archivo específico
run_test('tests/good/good0.bminor')
run_test('tests/bad/bad0.bminor')
```

### Ejecución en Lote

Para analizar todos los archivos de prueba:

```python
import os
from main import run_test

# Pruebas válidas
for test_file in sorted(os.listdir('tests/good')):
    run_test(f'tests/good/{test_file}')

# Pruebas con errores
for test_file in sorted(os.listdir('tests/bad')):
    run_test(f'tests/bad/{test_file}')
```

### Salida Esperada

**Archivo sin errores semánticos:**
```
Probando: tests/good/good0.bminor
  [GOOD] Sin errores semánticos.
```

**Archivo con errores:**
```
Probando: tests/bad/bad0.bminor
  [BAD] Error semántico (línea 8): Identificador 'x' no declarado
  [BAD] Error semántico (línea 13): La condición del 'while' debe ser boolean, se recibió 'integer'
```

---

## 1. Tabla de Símbolos

### Implementación

La tabla de símbolos se implementa en el archivo **`symtab.py`** utilizando:

- **ChainMap** de Python para gestionar la jerarquía de alcances léxicos
- Una estructura padre-hijo que mantiene referencias entre alcances anidados
- Un diccionario local (`_map`) para cada alcance que almacena solo los símbolos definidos en ese nivel

### Características

#### 1.1. Gestión de Alcances

- **Alcance global**: Punto de entrada, contiene declaraciones globales
- **Alcances de función**: Creados cuando se procesa una definición de función
- **Alcances de bloque**: Creados para bloques `{ ... }` en `if`, `while`, etc.
- **Alcances de parámetros**: Integrados al alcance de la función

#### 1.2. Operaciones Principales

```python
from symtab import Symtab

# Crear alcance global
global_scope = Symtab("global")

# Agregar símbolo
global_scope.add("x", variable_node)

# Buscar símbolo (respeta alcance léxico)
sym = global_scope.get("x")

# Crear alcance anidado (hijo)
func_scope = Symtab("func_main", parent=global_scope)
```

#### 1.3. Detección de Conflictos

La tabla de símbolos lanza excepciones para:

- **`SymbolDefinedError`**: Intento de redeclarar un símbolo con el mismo tipo en el mismo alcance
- **`SymbolConflictError`**: Intento de redeclarar con un tipo diferente

#### 1.4. Búsqueda Léxica

La búsqueda sigue la cadena padre-hijo:
1. Busca en el alcance actual
2. Si no encuentra, busca en el padre
3. Continúa hasta el alcance global
4. Devuelve `None` si no existe

---

## 2. Patrón Visitor con Multimethod

### Implementación

El analizador semántico usa el patrón **Visitor** mediante la librería **`multimethod`** en el archivo **`checker.py`**.

### 2.1. Concepto

- Cada nodo del AST tiene un tipo específico (ej: `BinaryOp`, `VarDeclaration`, `FunctionCall`)
- El `SemanticChecker` implementa métodos sobrecargados `visit()` para cada tipo de nodo
- La librería `multimethod` automáticamente despacha al método correcto según el tipo del argumento

### 2.2. Estructura Base

```python
from multimethod import multimethod

class SemanticChecker:
    def __init__(self):
        self.symtab = Symtab("global")
        self.errors = []
        self.current_return_type = None
    
    @multimethod
    def visit(self, node: Program):
        # Procesa la raíz del programa
        for decl in node.declarations:
            self.visit(decl)
    
    @multimethod
    def visit(self, node: VarDeclaration):
        # Procesa declaraciones de variables
        pass
    
    @multimethod
    def visit(self, node: BinaryOp):
        # Procesa operaciones binarias
        pass
```

### 2.3. Métodos Implementados

| Método | Tipo de Nodo | Responsabilidad |
|--------|-------------|-----------------|
| `visit(Program)` | Raíz del AST | Recorrer todas las declaraciones |
| `visit(Function)` | Definición de función | Registrar función, crear alcance, verificar parámetros y cuerpo |
| `visit(VarDeclaration)` | Declaración de variable | Verificar tipo válido, compatibilidad de inicializador, registrar en tabla |
| `visit(Assignment)` | Asignación | Verificar variable declarada, compatibilidad de tipos |
| `visit(IfStmt)` | Sentencia if | Verificar condición booleana, crear alcances para bloques |
| `visit(WhileStmt)` | Sentencia while | Verificar condición booleana, crear alcance para cuerpo |
| `visit(BinaryOp)` | Operación binaria | Verificar compatibilidad de operandos, anotar tipo resultante |
| `visit(UnaryOp)` | Operación unaria | Verificar compatibilidad con operando, anotar tipo resultante |
| `visit(FunctionCall)` | Llamada a función | Verificar función existe, argumentos coincidan, tipos sean compatibles |
| `visit(ReturnStmt)` | Sentencia return | Verificar tipo retornado coincida con función |
| `visit(Identifier)` | Identificador | Verificar variable/función declarada, devolver tipo |
| `visit(IntLiteral/FloatLiteral/...)` | Literales | Devolver tipo primitivo |

---

## 3. Tipos Soportados

El sistema soporta los siguientes tipos de datos primitivos:

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `integer` | Números enteros | `x: integer = 42;` |
| `boolean` | Valores booleanos | `b: boolean = true;` |
| `float` | Números con punto flotante | `f: float = 3.14;` |
| `string` | Cadenas de texto | `s: string = "hola";` |
| `char` | Caracteres individuales | `c: char = 'a';` |

### Compatibilidad de Tipos

Las reglas de compatibilidad se verifican mediante funciones en `typesys.py` (módulo de referencia):

- Asignación `=`: Ambos lados deben ser del mismo tipo
- Operadores aritméticos `+, -, *, /, %`: Requieren operandos `integer`
- Operadores relacionales `<, <=, >, >=`: Requieren operandos `integer`, devuelven `boolean`
- Operadores de comparación `==, !=`: Operandos compatibles, devuelven `boolean`
- Operadores lógicos `&&, ||`: Requieren operandos `boolean`, devuelven `boolean`
- Operador negación `!`: Requiere operando `boolean`, devuelve `boolean`

---

## 4. Chequeos Semánticos Implementados

### 4.1. Declaraciones (Regla 5.1)

✅ **Verificar declaración previa**
- Cada identificador debe declararse antes de usarse
- Se busca en la tabla de símbolos respetando alcances

✅ **Prevenir redeclaraciones**
- No se permite redeclarar un símbolo en el mismo alcance
- Se lanza `SymbolDefinedError` si se intenta

✅ **Permitir sombreado (shadowing)**
- Una variable puede ocultarse en alcances internos
- El acceso siempre usa la versión más cercana

### 4.2. Alcances Léxicos (Regla 5.2)

✅ **Crear alcances para estructuras**
- Funciones crean nuevo alcance
- Bloques `{ }` crean nuevo alcance
- Parámetros se registran en alcance de función

✅ **Gestionar entrada y salida**
- Al entrar a un alcance, se crea una tabla hija
- Al salir, se restaura la tabla padre

### 4.3. Chequeo de Tipos (Regla 5.3)

✅ **Verificar compatibilidad en asignaciones**
```bminor
x: integer = 5;    // válido
x = true;          // error: no se puede asignar boolean a integer
```

✅ **Verificar operadores aritméticos**
```bminor
a: integer = 3;
b: integer = 4;
c: integer = a + b;    // válido
d: integer = a + true; // error: boolean no es valido en operación +
```

✅ **Verificar operadores relacionales**
```bminor
x: integer = 5;
b: boolean = x < 10;    // válido
c: boolean = x < true;  // error: no se pueden comparar integer y boolean
```

✅ **Verificar operadores lógicos**
```bminor
b1: boolean = true;
b2: boolean = b1 && false;  // válido
x: integer = 3;
b3: boolean = x && true;    // error: operador && requiere boolean
```

### 4.4. Condiciones (Regla 6.5)

✅ **Condiciones de if/while booleanas**
```bminor
if (true) { }           // válido
if (x > 5) { }          // válido (x > 5 es boolean)
if (x) { }              // error: se requiere boolean, se recibió integer
```

### 4.5. Funciones (Regla 5.4)

✅ **Verificación de definición**
- La función debe estar declarada antes de llamarla
- Se registra en la tabla de símbolos global

✅ **Compatibilidad de argumentos**
```bminor
f: function integer (x: integer, y: integer) = { return x + y; }

f(5, 10);        // válido
f(5, true);      // error: argumento 2 debe ser integer, se recibió boolean
f(5);            // error: se espera 2 argumentos, se recibió 1
```

✅ **Compatibilidad de retornos**
```bminor
f: function integer (x: integer) = {
    return x + 1;          // válido
}

g: function integer (x: integer) = {
    return true;           // error: se espera integer, se recibió boolean
}
```

### 4.6. Expresiones (Regla 5.5)

✅ **Anotación de tipos**
- Cada expresión se anota con su tipo resultante
- Se almacena en atributo `node.type`
- Se usa por nodos superiores en el árbol

---

## 5. Aspectos Pendientes / Limitaciones

### No Implementados

❌ **Arreglos**
- El sistema actualmente NO soporta tipos arreglo `integer[10]`
- Indexación no se contempla
- Necesitaría extensión del sistema de tipos

❌ **Estructuras (structs)**
- No hay soporte para tipos compuestos
- Miembro acceso no se verifica

❌ **Verificación de retorno en todas las rutas**
- No se valida que toda rama de una función retorne un valor
- Especialmente relevante para funciones con condiciones

❌ **Conversiones implícitas**
- No se permiten conversiones entre tipos
- `integer` y `float` se tratan como incompatibles

❌ **Operadores adicionales**
- Se pueden agregar operadores como `<<`, `>>`, `^` en futuras versiones
- Módulo `typesys.py` mantiene tablas de compatibilidad

❌ **Módulos e imports**
- No hay soporte para incluir otros archivos
- Todo debe estar en un único archivo fuente

---

## 6. Archivos de Prueba

### Ubicación

```
tests/
├── good/   # 10 programas válidos (good0.bminor - good9.bminor)
└── bad/    # 10 programas con errores (bad0.bminor - bad9.bminor)
```

### Ejecución de Pruebas

```python
# Ejecutar todas las pruebas
import os
from main import run_test

print("=== PRUEBAS VÁLIDAS ===")
for f in sorted(os.listdir('tests/good')):
    run_test(f'tests/good/{f}')

print("\n=== PRUEBAS CON ERRORES ===")
for f in sorted(os.listdir('tests/bad')):
    run_test(f'tests/bad/{f}')
```

### Cobertura de Casos

Los archivos de prueba cubren:

1. ✅ Variables no declaradas
2. ✅ Redeclaración de variables
3. ✅ Asignación incompatible
4. ✅ Operador aplicado a tipos inválidos
5. ✅ Condición no booleana
6. ✅ Retorno con tipo incorrecto
7. ✅ Llamada a función con argumentos incorrectos (cantidad)
8. ✅ Llamada a función con tipos de argumentos incorrectos
9. ✅ Operadores con tipos incompatibles
10. ✅ Funciones no definidas

---

## 7. Mensajes de Error

El analizador proporciona mensajes claros y específicos:

```
Error semántico (línea 12): Identificador 'x' no declarado
Error semántico (línea 18): No se puede asignar boolean a variable 'x' (integer)
Error semántico (línea 27): La función 'sum' espera 2 argumentos, recibió 3
Error semántico (línea 34): La condición del 'if' debe ser boolean, se recibió 'integer'
Error semántico (línea 45): Operación '+' no válida entre integer y boolean
Error semántico (línea 56): Se esperaba retorno de tipo integer, pero se obtuvo boolean
```

Cada error incluye:
- Tipo de error
- Identificador o construcción involucrada
- Número de línea exacto
- Descripción clara del problema

---

## 8. Extensiones Futuras

Mejoras sugeridas para versiones posteriores:

1. **Verificación de retorno en todas las rutas**
   - Detectar funciones no-void sin return en algunas ramas

2. **Soporte para arreglos**
   - Tipos como `integer[10]`, acceso indexado `a[i]`
   - Verificación de índices como enteros

3. **Estructuras y tipos compuestos**
   - Definición de structs
   - Acceso a miembros

4. **Sistema de tipos mejorado**
   - Jerarquía de clases para tipos
   - Conversiones implícitas controladas

5. **Reporte visual mejorado**
   - Visualización del árbol de alcances con `rich`
   - Resaltado de línea problemática en el código fuente

6. **Alias de tipos**
   - Permitir `type mytype = integer;`

---

## 9. Referencias

- Especificación de B-Minor: Ver `Analizador_Semantico.md`
- Patrón Visitor: https://refactoring.guru/design-patterns/visitor
- Multimethod: https://github.com/coady/multimethod
- ChainMap: https://docs.python.org/3/library/collections.html#collections.ChainMap

---

## 10. Notas de Implementación

### Decisiones Clave

1. **Uso de dataclasses**: Facilita la definición del AST con tipado
2. **Multimethod en lugar de dispatch manual**: Código más limpio y mantenible
3. **ChainMap para tabla de símbolos**: Gestión de alcances automática y eficiente
4. **Acumular errores**: Permite reportar múltiples defectos en una sola pasada

### Flujo de Análisis

```
Código fuente
    ↓
Lexer (tokenización)
    ↓
Parser (construcción AST)
    ↓
SemanticChecker (verificación)
    ├── Recorre cada nodo
    ├── Usa Symtab para gestionar alcances
    ├── Verifica tipos y reglas
    └── Acumula errores
    ↓
Reporte de errores o éxito
```

---

## Autor

Compilador B-Minor - Práctica de Compiladores

**Fecha**: Abril 2026

---

**Fin del README.md**
