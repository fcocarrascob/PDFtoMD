# AGENTS / Repository Guidelines (Cálculos Notebook focus)

Esta guía orienta a agentes que trabajen en PDFtoMD, con énfasis en el módulo **Notebook de Cálculos** (carpeta `notebook/`). Aplica a todo el repositorio; no hay otras guías anidadas.

## /init rápido
- Propósito: App de escritorio PyQt6 que convierte PDF a Markdown; incluye un notebook ligero para cálculos simbólicos/numéricos y vista previa HTML.
- Entradas principales: `main.py` (lanzador GUI), `converter/engine.py` (conversión PDF→MD), `gui/mainwindow.py` (UI), `notebook/document.py` + `notebook/renderer.py` (núcleo del notebook).
- Dependencias clave: PyQt6, pymupdf4llm, openai, pillow, numpy, sympy, markdown-it-py (opcional), bleach (opcional) y utilidades en `notebook/units.py`.
- Tests: `pytest` desde la raíz (`tests/` cubre flujo de conversión y fixtures HTML).
- Casos manuales: `test_full_app.json` (raíz) encapsula escenarios completos para validar manualmente la aplicación, sus funciones y el renderizado HTML/MathJax.
- Seguridad: El modo IA envía imágenes de páginas a OpenAI; evita documentos sensibles. No encapsules importaciones en `try/except`.

## Reglas de colaboración para agentes
- No modifiques código sin aprobación humana explícita. Propón primero un plan de implementación conciso y espera confirmación antes de ejecutar cambios.
- Las ediciones en esta guía son permitidas para mantenerla alineada con el flujo de trabajo del notebook y pruebas manuales.

## Panorama del módulo Notebook de Cálculos
- **Objetivo:** Permitir blocks de texto y expresiones matemáticas evaluables (tipo cuaderno) que luego se renderizan a HTML con MathJax.
- **Flujo principal:**
  1) `Document` agrupa bloques (`TextBlock`/`FormulaBlock`), carga/guarda desde diccionarios/JSON y mantiene opciones.
  2) `Document.evaluate()` crea un `EvaluationContext` que registra símbolos, funciones, arrays, variables, logs y errores.
  3) Cada `FormulaBlock.evaluate()` parsea, ejecuta y formatea resultados (numéricos, arrays o funciones), actualizando el contexto.
  4) `NotebookRenderer.render()` transforma el documento evaluado a HTML completo (incluye MathJax embebido o CDN) y paneles de resultados.
  5) `notebook/units.py` expone helpers numéricos seguros (`linspace`, `arange`, `sweep`, funciones lógicas) para las expresiones.

## Componentes clave y responsabilidades
- `notebook/document.py`
  - **SymbolRegistry / EvaluationContext:** Crea símbolos SymPy bajo demanda y acumula variables, funciones, arrays, logs y errores por bloque.
  - **TextBlock:** Renderiza CommonMark vía `markdown-it` si está instalado; fallback HTML mínimo con escape/sanitización opcional via `bleach`.
  - **FormulaBlock:**
    - Detecta asignaciones (`a = 3`, `f(x)=x^2`), arrays (`linspace`, `arange`, `sweep`) y expresiones condicionales (If/elif/else → `Piecewise`).
    - Usa `_safe_sympify` con diccionario seguro de funciones y símbolos para evitar inyección accidental; añade funciones de usuario al contexto.
    - Evalúa numéricamente con sustituciones de valores previos; registra errores sin colapsar el documento (estado `evaluation_status`).
    - Genera LaTeX con `sympy.latex`, limpiando multiplicaciones (`\cdot`) y preservando `latex`/`result` aunque haya error.
    - Serializa/deserializa bloques via `to_dict`/`from_dict` para persistencia.
- `notebook/renderer.py`
  - `NotebookRenderer.render()` recibe un `Document`, ejecuta `evaluate()` y genera HTML con estilos embebidos, tablas de variables, funciones, arrays y paneles de errores/logs.
  - Permite `mathjax_path` local u `mathjax_url` CDN; elige según parámetros para compatibilidad offline.
  - Tema base en `NotebookTheme` concentra colores para facilitar ajustes rápidos.
- `notebook/units.py`
  - Implementa utilidades numéricas simples (sin NumPy) y entorno seguro `math_env()` usado por el evaluador: trigonometría, log/exp, `And/Or/Not`, etc.
  - Maneja casos borde: `linspace` con num ≤ 1, `arange` con step negativo/positivo y validación de step=0.

## Prácticas recomendadas al modificar el notebook
- Mantén la evaluación determinista y sin efectos colaterales: no ejecutes I/O ni red desde expresiones.
- Extiende las funciones permitidas agregando helpers en `math_env()` y registrándolos en `_safe_sympify` si deben ser símbolos de SymPy.
- Preserva la captura de errores: usa `EvaluationContext.register_error` y no dejes excepciones sin controlar dentro de `FormulaBlock.evaluate()`.
- Al ajustar HTML, mantén compatibilidad con MathJax (usa `$$ ... $$` para fórmulas) y conserva el orden de bloques.
- No envuelvas importaciones en `try/except` (salvo dependencias opcionales ya existentes como `markdown-it` o `bleach`).

## Interacción con el resto de la app
- El notebook se usa para mostrar cálculos derivados; su salida HTML puede integrarse en vistas/fixtures (p. ej., `test_full_app_preview.html`).
- No depende de la conversión PDF→MD, pero comparte directrices de seguridad: evita incluir imágenes o contenido ejecutable en la salida Markdown/HTML.
- Si agregas modelos IA para cálculos, mantén aislamiento: no mezcles lógica de conversión de PDFs con evaluación de expresiones.

## Testing y depuración
- Ejecuta `pytest` para validar regresiones. Añade pruebas unitarias en `tests/` para nuevos bloques, casos de error o helpers numéricos.
- Para depurar, puedes imprimir el `context.logs` o revisar tablas generadas por `NotebookRenderer` en el HTML; evita print ruidoso en producción.
- Verifica que las funciones opcionales (`markdown-it`, `bleach`) tengan fallbacks estables para entornos sin dependencias completas.
