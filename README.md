# PDF to Markdown Converter + Calculation Notebook

Aplicación de escritorio en PySide6 que combina dos pestañas:
- **PDF to Markdown:** convierte PDFs a Markdown usando PyMuPDF/pymupdf4llm y, opcionalmente, OpenAI para OCR/ecuaciones.
- **Calculation Notebook:** cuaderno tipo SMath con bloques de texto y fórmulas evaluadas con SymPy + pint (unidades) y previsualización en MathJax.

## Dependencias clave
- PySide6 / PySide6-Addons (GUI y QWebEngineView para MathJax).
- pymupdf, pymupdf4llm (lectura y extracción de PDFs).
- openai (modo asistido por LLM al convertir PDFs).
- sympy (parsing de expresiones).
- pint (manejo de unidades físicas).

## Arquitectura y flujo
- `main.py` inicia QApplication, aplica estilos y abre `gui/MainWindow` con pestañas.
- **Pestaña PDF→MD:**
  - `converter/engine.py` gestiona la conversión. Si hay API Key se usa `converter/ai_agent.py` (modelos OpenAI) para transcribir páginas como imágenes; si no, cae a pymupdf4llm.
  - El progreso se reporta por QThread (`ConversionWorker`) y la UI muestra barra/estado.
- **Calculation Notebook:**
  - Modelo: `notebook/document.py` define `Document`, `TextBlock`, `FormulaBlock` y un `EvaluationContext` con símbolos, valores numéricos y cantidades pint.
  - Unidades: `notebook/units.py` expone un `UnitRegistry` y helpers; operaciones numéricas con unidades se evalúan vía pint; cuando hay unidades previas, las sustituciones usan `Quantity` y el resultado se compacta (p.ej. MPa·mm → kN/m).
  - Render: `notebook/renderer.py` genera HTML con bloques + tabla de variables y carga MathJax en `QWebEngineView`.
  - UI: `gui/notebook_tab.py` lista bloques, editor, preview y una barra de atajos (operadores y unidades frecuentes).

## Cómo usar
1) Instala dependencias en tu venv: `pip install -r requirements.txt`.
2) Ejecuta: `python main.py`.
3) PDF→MD: arrastra PDFs, opcional marca “Use AI Agent” y configura API Key/modelo en Settings.
4) Notebook: agrega bloques; ejemplos:
   - `L = 3 MPa`
   - `B = 4 mm`
   - `P = B * L` → se mostrará `12.00 kN/m` con la tabla de variables debajo.

## Funciones actuales
- Conversión de PDFs a Markdown con o sin OpenAI.
- Split de PDFs en partes por número de páginas.
- Cuaderno con bloques ordenados de texto/fórmula, evaluación incremental.
- Manejo de unidades con pint y formateo compacto en la preview.
- Previsualización HTML con MathJax y tabla de variables evaluadas.
- Barra de atajos para insertar operadores y unidades comunes.

## TODO / posibles mejoras
- Añadir conversión/selección de unidades personalizada en la UI (combo editable + `to(<unit>)`).
- Permitir no simplificar unidades (ej. mantener MPa·mm) según preferencia de usuario.
- Undo/redo y mover bloques (drag & drop) en el notebook.
- Validaciones y mensajes de error más claros en fórmulas con unidades inválidas.
- Tests automatizados adicionales para casos mixtos (potencias, divisiones con unidades, conversiones).
- Configuración persistente de la barra de unidades (lista editable por usuario).
