# Atlas de Sintaxis: B-Minor+

# Taller: Extensión de la Gramática B-Minor (B-Minor+)
**Estudiante: Jonathan David Ochoa Echeverri**
**Estudiante: Juan Camilo Gil Ramírez**
**Estudiante: Juan José Ruiz Mellizo**

## Introducción
"""Este documento funciona como un Atlas Visual del lenguaje B-Minor+. Se han integrado nuevas construcciones sintácticas sin modificar la gramática base original, utilizando reglas adicionales y nuevos no-terminales."""


### Ciclo While
Permite la repetición de bloques de código mientras una condición sea verdadera.
![While](svg/while_stmt.svg)

## Expresiones
### Operadores de Asignación Compuesta
Incluye `+=`, `-=`, `*=`, y `/=`. Tienen asociatividad a la derecha.
![Asignación](svg/assignment_ops.svg)

### Operador Ternario
Operador condicional de tres operandos `cond ? val1 : val2`.
![Ternario](svg/expr_ternary.svg)

### Incremento y Decremento
Soporte para operadores unarios en modo prefijo y sufijo.
![Inc Dec](svg/expr_inc_dec.svg)

### Gestión de Objetos
Creación de instancias con `new` y acceso a miembros mediante el operador punto `.`.
![New](svg/expr_new.svg)
![Punto](svg/expr_dot_access.svg)

## Clases
Definición de estructuras de datos y métodos.
![Clases](svg/class_decl.svg)

## Tabla de Precedencia y Asociatividad
Para integrar las extensiones en B-Minor+, se definieron los siguientes niveles:

| Operador | Descripción | Asociatividad | Nivel (Gramática) |
| :--- | :--- | :--- | :--- |
| `++`, `--` | Incremento/Decremento | N/A (Unario) | `expr8` / `expr9` |
| `.`, `new` | Acceso e Instanciación | Izquierda | `expr9` / `factor` |
| `?:` | Ternario | Derecha | Entre `expr1` y `expr2` |
| `+=`, `-=`, ... | Asignación Compuesta | Derecha | `expr1` |

## Bonus B: Generación Semi-Automática
Para cumplir con el bonus, se desarrolló la función `generar_bonus_b` en Python. Esta herramienta es capaz de leer una regla gramatical en formato texto (BNF) y transformarla automáticamente en un diagrama de rieles, distinguiendo entre tokens terminales y no-terminales.

**Diagramas generados mediante el proceso automático:**

* **Sentencia de Impresión (Print):**
![Bonus Print](svg/bonus_print.svg)
* **Sentencia de Retorno (Return):**
![Bonus Return](svg/bonus_return.svg)
* **Condición de Bloque If:**
![Bonus If Cond](svg/bonus_if_cond.svg)

**Justificación:** Los operadores de asignación compuesta se colocan en el nivel más bajo (`expr1`) para permitir que todas las operaciones aritméticas se resuelvan antes de la asignación. El operador ternario tiene una precedencia mayor que la asignación pero menor que los operadores lógicos para permitir expresiones como `a > b ? x : y` sin paréntesis.
**Nota sobre el Bonus B:** Las reglas simplificadas del lenguaje base se generaron mediante un script de automatización que procesa la estructura BNF directamente, facilitando la expansión del atlas visual sin intervención manual en reglas no recursivas.