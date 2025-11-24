# PDF to Markdown Converter + Calculation Notebook

Aplicación de escritorio en PySide6 que combina dos pestañas:
- **PDF to Markdown:** convierte PDFs a Markdown usando PyMuPDF/pymupdf4llm y, opcionalmente, OpenAI para OCR/ecuaciones.
- **Calculation Notebook:** cuaderno tipo SMath con bloques de texto y fórmulas evaluadas con SymPy para cálculos numéricos puros y previsualización en MathJax.

## Dependencias clave
- PySide6 / PySide6-Addons (GUI y QWebEngineView para MathJax).
- pymupdf, pymupdf4llm (lectura y extracción de PDFs).
- openai (modo asistido por LLM al convertir PDFs).
- sympy (parsing y evaluación de expresiones matemáticas).

## Arquitectura y flujo
- `main.py` inicia QApplication, aplica estilos y abre `gui/MainWindow` con pestañas.
- **Pestaña PDF→MD:**
  - `converter/engine.py` gestiona la conversión. Si hay API Key se usa `converter/ai_agent.py` (modelos OpenAI) para transcribir páginas como imágenes; si no, cae a pymupdf4llm.
  - El progreso se reporta por QThread (`ConversionWorker`) y la UI muestra barra/estado.
- **Calculation Notebook:**
  - Modelo: `notebook/document.py` define `Document`, `TextBlock`, `FormulaBlock` y un `EvaluationContext` con símbolos y valores numéricos.
  - Evaluación: `notebook/units.py` expone funciones matemáticas estándar (sqrt, sin, cos, etc.); todas las operaciones trabajan con valores numéricos puros (float/int).
  - Render: `notebook/renderer.py` genera HTML con bloques + tabla de variables y carga MathJax en `QWebEngineView`.
  - UI: `gui/notebook_tab.py` lista bloques, editor, preview y una barra de atajos (operadores matemáticos y símbolos griegos).

## Cómo usar
1) Instala dependencias en tu venv: `pip install -r requirements.txt`.
2) Ejecuta: `python main.py`.
3) PDF→MD: arrastra PDFs, opcional marca "Use AI Agent" y configura API Key/modelo en Settings.
4) Notebook: agrega bloques; ejemplos:
   - `L = 3.5`
   - `B = 4.0`
   - `P = B * L` → se mostrará `14.00` con la tabla de variables debajo.

## Funciones actuales
- Conversión de PDFs a Markdown con o sin OpenAI.
- Split de PDFs en partes por número de páginas.
- Cuaderno con bloques ordenados de texto/fórmula, evaluación incremental.
- Cálculos numéricos puros con SymPy (sin manejo de unidades físicas).
- Previsualización HTML con MathJax y tabla de variables evaluadas.
- Barra de atajos para insertar operadores matemáticos y símbolos griegos.

### Render y formato
- MathJax soporta inline (`$...$`) y bloque (`$$...$$`); exporta con CDN o bundle local (configurable en Settings) y formato A4 claro.
- Todas las fórmulas se evalúan de arriba hacia abajo en un contexto compartido (SymPy). Los valores se obtienen mediante evaluación numérica pura.
- Las multiplicaciones se muestran con `·` entre números y símbolos (`mul_symbol="\cdot"`).
- Los errores de evaluación/parseo se muestran en el panel de errores, pero el resto de los bloques sigue evaluando.


## Pruebas y regresion
- Punto de verdad para QA: `INSTRUCCIONES_PRUEBA.md` describe el flujo de prueba y `test_full_app.json` es el cuaderno maestro con todas las secciones (funciones, arrays, casos mixtos y extra de matematicas). El preview esperado queda en `test_full_app_preview.html`.
- Validacion rapida: `python verify_test_document.py` carga `test_full_app.json`, evalua, lista funciones/arrays/variables y regenera el preview.
- Al agregar una nueva funcion/feature: suma un bloque representativo al final de `test_full_app.json`, ejecuta el script y comprueba que siga sin errores. Si cambia el comportamiento esperado, actualiza tambien `INSTRUCCIONES_PRUEBA.md`.
- Para futuros agentes: mantener sincronizados estos tres artefactos (instrucciones, cuaderno JSON y preview HTML) antes de dar por buena cualquier mejora.

## TODO / posibles mejoras
- Undo/redo y mover bloques (drag & drop) en el notebook.
- Validaciones y mensajes de error más claros en fórmulas.
- Tests automatizados adicionales para casos complejos (potencias, divisiones, funciones trigonométricas).
- Integración futura con Sympy para funciones avanzadas (linspace, sweep, evaluación simbólica).

## Pipeline de evaluación/render en el notebook
- Entrada: bloques de texto (Markdown) y fórmulas (expresiones SymPy-friendly, valores numéricos).
- Evaluación:
  - Se comparte un `EvaluationContext` con valores numéricos y símbolos.
  - Las expresiones se evalúan numéricamente usando Python `eval` con un entorno seguro de funciones matemáticas.
  - En paralelo se genera un `sympy_expr` para render. Si el parse inicial falla, se reintenta un parse tolerante (`sympify(..., evaluate=False)`) para obtener siempre LaTeX; los fallos de parse se anotan como advertencias.
  - Errores de evaluación o parseo se muestran en el panel de errores, pero los demás bloques siguen evaluando.
- Render:
  - LaTeX se genera desde `sympy_expr` cuando existe; si no, se usa un fallback del texto crudo.
  - MathJax renderiza inline (`$...$`) y bloque (`$$...$$`); la exportación HTML incluye MathJax (CDN o bundle local) y puede ocultar el panel de logs según preferencias.
  - El HTML se estiliza con tema claro y layout tipo página A4; la tabla de variables muestra nombre, expresión y valor numérico.
