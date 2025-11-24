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

### Render y unidades
- MathJax soporta inline (`$...$`) y bloque (`$$...$$`); exporta con CDN o bundle local (configurable en Settings) y formato A4 claro.
- Todas las fórmulas se evalúan de arriba hacia abajo en un contexto compartido (SymPy + pint). Si el valor se obtiene con pint, se reparsea para obtener LaTeX y se anotan advertencias de parse si algo falla.
- Las multiplicaciones se muestran con `·` entre números y símbolos (`mul_symbol="\cdot"`), eliminando casos como `fcb`.
- Las unidades se mantienen al final de la expresión; se evita duplicarlas si ya aparecen en el LaTeX.
- Los errores de unidades/parseo se muestran en el panel de errores, pero el resto de los bloques sigue evaluando.

## TODO / posibles mejoras
- Añadir conversión/selección de unidades personalizada en la UI (combo editable + `to(<unit>)`).
- Permitir no simplificar unidades (ej. mantener MPa·mm) según preferencia de usuario.
- Undo/redo y mover bloques (drag & drop) en el notebook.
- Validaciones y mensajes de error más claros en fórmulas con unidades inválidas.
- Tests automatizados adicionales para casos mixtos (potencias, divisiones con unidades, conversiones).
- Configuración persistente de la barra de unidades (lista editable por usuario).

## Pipeline de evaluación/render en el notebook
- Entrada: bloques de texto (Markdown) y fórmulas (expresiones SymPy-friendly, con unidades opcionales).
- Evaluación:
  - Se comparte un `EvaluationContext` con valores numéricos, cantidades pint y símbolos.
  - Si una asignación incluye unidades o una expresión produce cantidades, se evalúa con pint; el valor numérico y unidades se normalizan (y pueden convertir a una unidad objetivo).
  - En paralelo se intenta generar un `sympy_expr` para render. Si el parse inicial falla, se reintenta un parse tolerante (`sympify(..., evaluate=False)`) para obtener siempre LaTeX; los fallos de parse se anotan como advertencias.
  - Errores de unidades o parseo se muestran en el panel de errores, pero los demás bloques siguen evaluando.
- Render:
  - LaTeX se genera desde `sympy_expr` cuando existe; si no, se usa un fallback del texto crudo.
  - MathJax renderiza inline (`$...$`) y bloque (`$$...$$`); la exportación HTML incluye MathJax (CDN o bundle local) y puede ocultar el panel de logs según preferencias.
  - El HTML se estiliza con tema claro y layout tipo página A4; la tabla de variables muestra nombre, expresión, valor y unidades.

## ¿SymPy es suficiente o conviene añadir NumPy?
Para los cálculos de fórmulas normativas (ACI 318, AISC 360) que maneja el cuaderno, SymPy + pint ya cubren los casos habituales:
- **Parsing y álgebra simbólica:** SymPy interpreta expresiones como `phi*Mn >= Mu`, reorganiza términos y genera el LaTeX que se previsualiza.
- **Unidades físicas:** pint mantiene las unidades y permite convertirlas; esto evita errores al mezclar MPa, ksi, mm, in, etc.
- **Evaluación paso a paso:** cada bloque reutiliza el contexto evaluado anterior, lo que facilita cadenas de comprobaciones.

NumPy resulta útil como complemento cuando necesitas:
- **Vectorizar series grandes de combinaciones o secciones** (p. ej. iterar cientos de perfiles o envolventes de carga). En estos casos puedes preparar arrays en una celda, evaluarlos con NumPy y luego pasar resultados escalares a las fórmulas SymPy que renderizan el reporte.
- **Operaciones matriciales intensivas** (rigideces, modos, integración numérica) donde las rutinas BLAS subyacentes mejoran el tiempo de cómputo.

Para casos típicos de diseño manual o verificación de pocos elementos, SymPy es suficiente y mantiene el pipeline de unidades/LaTeX sin añadir dependencias binarias. Considera añadir NumPy si tu flujo involucra muchos escenarios repetitivos o cálculos matriciales donde la velocidad sea crítica.

## Cómo barrer un diagrama P–M con funciones simbólicas (sin NumPy)
El cuaderno `pm_interaccion_simple.json` ya calcula varios puntos de interacción evaluando valores concretos de la profundidad del eje neutro (`c`). Si quieres aumentar la densidad de puntos sin añadir dependencias, puedes encapsular el equilibrio en funciones simbólicas y evaluarlas en una pequeña lista de valores.

### Idea base
- Define funciones con SymPy que representen \( P_n(c) \) y \( M_n(c) \) reutilizando las variables de materiales y geometría que ya están en el cuaderno (por ejemplo, `fc`, `fy`, `bw`, `h`, `As1`–`As4`, distancias a ejes, etc.).
- En otro bloque, declara una lista corta de profundidades `c_vals` (por tramo: tracción, balance, compresión) y evalúa las funciones en cada `c` usando una comprensión de listas. El pipeline conserva unidades porque los símbolos y cantidades ya están registrados en el `EvaluationContext`.

### Aplicado al ejemplo
- En un bloque de fórmula debajo de los parámetros ya existentes, puedes definir:
  ```
  Pn_c = Pn_expr(c)  # usa la expresión de equilibrio axial que ya tienes en el cuaderno
  Mn_c = Mn_expr(c)  # idem para el momento
  Pn = sp.lambdify(c, Pn_c)
  Mn = sp.lambdify(c, Mn_c)
  ```
  Aquí `Pn_expr` y `Mn_expr` corresponden a las expresiones que hoy calculas en cada punto; al encapsularlas en funciones, evitas repetir la algebra en cada bloque.
- En un bloque siguiente, barre algunos valores representativos:
  ```
  c_vals = [0.08*m, 0.12*m, 0.18*m, c_balance, 0.25*m, 0.30*m]
  PM_tabla = [(Pn(ci).to(kN), Mn(ci).to(kN*m)) for ci in c_vals]
  ```
  Cada par \( P_n, M_n \) se devuelve con unidades homogéneas. La tabla se muestra en la previsualización y también queda en la tabla de variables para copiarla a Excel/Plotly.

### Propuesta de implementación en el cuaderno
- **Nuevo bloque de funciones:** añadir un bloque de fórmula justo antes de los puntos numéricos actuales, donde se definan `Pn(c)` y `Mn(c)` a partir de las mismas ecuaciones que hoy se repiten en cada “Punto”. Esto mantiene la trazabilidad del LaTeX y las unidades.
- **Bloque de barrido compacto:** sustituir o complementar los bloques individuales con un bloque que evalúe `Pn(c)` y `Mn(c)` en la lista `c_vals` de la sección anterior. Puedes conservar uno o dos puntos manuales para referencia visual y usar `PM_tabla` para el resto.
- **Exportar resultados:** en el mismo bloque o en uno siguiente, añade conversiones a kN/kN·m (como en los puntos actuales) para que `PM_tabla` esté lista para graficar sin postprocesado.

Con este patrón obtienes un barrido denso sin NumPy y sin perder el formateo LaTeX ni el manejo de unidades del cuaderno actual.
