# Plan para extender condicionales y operadores lógicos en el cuaderno

## Objetivo
Admitir condicionales multi-rama y operadores lógicos básicos en las expresiones evaluadas por el cuaderno, manteniendo el modelo seguro basado en SymPy y el entorno numérico limitado.

## Trabajo propuesto
1. **Generalizar el parser de condicionales**
   - Ampliar `FormulaBlock._parse_conditional_expr` para aceptar árboles `If`/`IfExp` con múltiples ramas (p. ej., `if/elif/else` escritos en varias líneas) y convertirlos en una sola instancia de `Piecewise` en orden de prioridad.
   - Asegurar que `_safe_sympify` siga bloqueando la recursión condicional infinita (`allow_conditional=False` en llamadas internas) y que las ramas se normalicen con `_normalize_expression` antes de simprimirlas.
   - Añadir validaciones que rechacen nodos no soportados en el AST y mantengan el modelo de expresiones puras (sin asignaciones ni llamadas arbitrarias).

2. **Incorporar operadores lógicos explícitos**
   - Exponer `And`, `Or` y `Not` de SymPy en el `safe_locals` de `_safe_sympify` y en el entorno numérico `math_env` para que puedan evaluarse tanto simbólica como numéricamente.
   - Permitir su uso dentro de las condiciones de `Piecewise` y en expresiones independientes, asegurando que el evaluador numérico (`_evaluate_numeric`) tenga equivalentes booleanos seguros.

3. **Cobertura y documentación**
   - Crear pruebas que verifiquen: (a) condicionales con `elif` se convierten a `Piecewise` en el orden correcto; (b) operadores lógicos combinados con comparaciones producen resultados esperados en modo numérico y simbólico.
   - Actualizar la guía de usuario o la descripción del cuaderno para mencionar el soporte de condicionales multi-rama y operadores lógicos.

## Archivos a tocar
- `notebook/document.py` (parsing y entorno SymPy)
- `notebook/units.py` (entorno numérico)
- `tests/` (pruebas nuevas o extendidas)
- Documentación relacionada (ej. `APP_DESCRIPTION.md` o README del cuaderno)
