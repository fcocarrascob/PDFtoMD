# PDF to Markdown Converter + Calculation Notebook

Aplicación de escritorio en PySide6 con dos pestañas principales: conversor PDF→Markdown (con modo asistido por OpenAI) y cuaderno de cálculo tipo SMath basado en SymPy.

## Dependencias clave
- PySide6 / PySide6-Addons (GUI y QWebEngineView para MathJax).
- pymupdf, pymupdf4llm (lectura y extracción de PDFs).
- openai (modo asistido por LLM al convertir PDFs).
- sympy (parsing y evaluación de expresiones numéricas).

## Arquitectura y flujo
- `main.py` inicia `QApplication`, aplica estilos y abre `gui/MainWindow` con pestañas.
- **Pestaña PDF→MD:**
  - `converter/engine.py` gestiona la conversión. Si hay API key, usa `converter/ai_agent.py` (modelos OpenAI) para transcribir páginas como imágenes; si no, cae a pymupdf4llm.
  - El progreso se reporta por QThread (`ConversionWorker`) y la UI muestra barra/estado.
- **Calculation Notebook:**
  - Modelo: `notebook/document.py` define `Document`, `TextBlock`, `FormulaBlock` y un `EvaluationContext`.
  - Evaluación: `notebook/units.py` expone funciones matemáticas numéricas; todas las operaciones trabajan con valores float/int.
  - Render: `notebook/renderer.py` genera HTML con bloques + tabla de variables y carga MathJax en `QWebEngineView`.
  - UI: `gui/notebook_tab.py` lista bloques, editor, previsualización y barra de atajos (operadores matemáticos, símbolos griegos y plantillas lógicas básicas).

## Funciones del cuaderno (`notebook/units.py`)
- `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`, `pi`
- `sum`, `min`, `max`, `abs`, `range`
- `linspace(start, stop, num)`, `arange(start, stop, step)`
- `sweep(func, xs)` para mapear funciones escalares sobre listas/iterables
- `imap(func, xs)`, `imap2(func, xs, ys)` para aplicar funciones unary/binary (tipo map/zip) y devolver lista
- `irange(...)` para ver rangos como lista, `isum(xs)` y `imean(xs)` como agregados rápidos
- Booleanas: `And(*args)`, `Or(*args)`, `Not(arg)`

## Cuaderno de prueba y ejemplos
- `test_full_app.json` cubre todo el flujo:
  - **Fase 1**: definición de funciones (`f`, `area_rectangulo`, composiciones).
  - **Fase 2**: generación de arrays con `linspace`/`arange`, casos con variables y pasos decimales/negativos.
  - **3.1–3.7**: combinaciones de funciones con arrays, barridos con `sweep`, condicionales y expresiones lógicas.
  - **3.8 Mezclas lógicas y arrays**: usa `es_positivo`, `es_no_cero`, `sweep`, `And`/`Or`/`Not`, `max` y `arange` descendente para validar lógica + números.
- `test_full_app_preview.html` muestra el render esperado.
- Validación rápida: `python verify_test_document.py` carga el cuaderno, evalúa, lista funciones/arrays/variables y regenera el preview.

## Cómo usar
1. Instala dependencias en tu venv: `pip install -r requirements.txt`.
2. Ejecuta: `python main.py`.
3. PDF→MD: arrastra PDFs; opcional marca “Use AI Agent” y configura API key/modelo en Settings.
4. Notebook: agrega bloques; ejemplos simples:
   - `L = 3.5`
   - `B = 4.0`
   - `P = B * L` → se mostrará `14.00` con la tabla de variables debajo.

## Funcionalidades actuales
- Conversión de PDFs a Markdown con o sin OpenAI.
- Split de PDFs en partes por número de páginas.
- Cuaderno con bloques ordenados de texto/fórmula, evaluación incremental.
- Cálculos numéricos puros con SymPy (sin manejo de unidades físicas).
- Previsualización HTML con MathJax y tabla de variables evaluadas.
- Barra de atajos para insertar operadores matemáticos, símbolos griegos y plantillas lógicas básicas apoyadas en las funciones booleanas ya soportadas.

## Render y formato
- MathJax soporta inline (`$...$`) y bloque (`$$...$$`); exporta con CDN o bundle local (configurable en Settings) y formato A4 claro.
- Todas las fórmulas se evalúan de arriba hacia abajo en un contexto compartido (SymPy). Los valores se obtienen mediante evaluación numérica pura.
- Las multiplicaciones se muestran con `·` entre números y símbolos (`mul_symbol="\\cdot"`).
- Los errores de evaluación/parseo se muestran en el panel de errores, pero el resto de los bloques sigue evaluando.

## Pruebas y regresión
- Punto de verdad para QA: `INSTRUCCIONES_PRUEBA.md` describe el flujo y `test_full_app.json` es el cuaderno maestro (funciones, arrays, casos mixtos y extra de matemáticas). El preview esperado queda en `test_full_app_preview.html`.
- Validación rápida: `python verify_test_document.py`.
- Al agregar una nueva función/feature: suma un bloque representativo al final de `test_full_app.json`, ejecuta el script y comprueba que siga sin errores. Si cambia el comportamiento esperado, actualiza también `INSTRUCCIONES_PRUEBA.md`.
- Para futuros agentes: mantener sincronizados estos artefactos (instrucciones, cuaderno JSON y preview HTML) antes de dar por buena cualquier mejora.

## TODO / posibles mejoras
- Undo/redo y mover bloques (drag & drop) en el notebook.
- Validaciones y mensajes de error más claros en fórmulas.
- Tests automatizados adicionales para casos complejos (potencias, divisiones, funciones trigonométricas).
- Integración futura con SymPy para funciones avanzadas (linspace, sweep, evaluación simbólica).
