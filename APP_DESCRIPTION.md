# Resumen de la aplicación

PDFtoMD es una aplicación de escritorio en PySide6 con dos áreas principales:

- **Conversión de PDF a Markdown** con PyMuPDF/pymupdf4llm, barra de progreso y opción de usar un agente OpenAI para OCR y ecuaciones.
- **Calculation Notebook** tipo cuaderno, con bloques de texto y fórmulas evaluadas con SymPy, previsualización en MathJax y tabla de variables.

Incluye ajustes para modelo/API key, opciones de render con CDN local, y un flujo de prueba respaldado por `test_full_app.json` y `verify_test_document.py`.
