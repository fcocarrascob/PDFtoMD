# Instrucciones de Prueba - Documento Completo

## Archivos disponibles
1. **test_full_app.json** - Documento de prueba con todas las secciones (funciones, arrays, combinados, extras matematicas).
2. **verify_test_document.py** - Script de verificacion automatica.
3. **test_full_app_preview.html** - Preview HTML generado por el script.

## Como probar

### Opcion 1: Script de verificacion (recomendado)
```bash
python verify_test_document.py
```
El script carga el JSON, evalua todos los bloques, muestra resumen de funciones/arrays/variables y genera el HTML.

### Opcion 2: Desde la interfaz grafica
1) Abre la app y carga `test_full_app.json`.
2) Revisa al final de la vista previa las tablas de Functions, Arrays y Variables.

### Opcion 3: Desde Python
```python
from notebook.document import Document
doc = Document.load("test_full_app.json")
context = doc.evaluate()
print(len(context.functions), len(context.arrays), len(context.errors))
doc.save_html("mi_prueba.html")
```

## Resultados esperados

- **Funciones (9):** f, area_rectangulo, g, h, cuadrado, doble, compuesta, momento_inercia, f_lineal.
- **Arrays (15):** arr1 a arr10, alturas, arr_un_elemento, arr_dos_elementos, xs_sweep, ys_sweep.
- **Errores:** No se esperan errores de evaluacion.

### Detalle de arrays
- arr1 = linspace(0, 10, 5)
- arr2 = arange(0, 10, 2)
- arr3 = linspace(-5, 5, 5)
- arr4 = arange(0, 5, 0.5)
- arr5 = linspace(0, 100, 50)
- arr6 = linspace(inicio, fin, puntos)
- arr7 = linspace(2*3, 5**2, 10)
- arr8 = arange(0, 2*pi, pi/4)
- arr9 = arange(10, 0, -1)
- arr10 = linspace(1, exp(1), 4)
- alturas = linspace(0.2, 0.5, 4)
- arr_un_elemento = linspace(5, 5, 1)
- arr_dos_elementos = arange(0, 2, 1)
- xs_sweep = [0, 1, 2, 3]
- ys_sweep = sweep(f_lineal, xs_sweep)

## Que revisar en el HTML preview
- Encabezados y formulas LaTeX renderizados.
- Tabla **Functions** con 8 entradas.
- Tabla **Arrays** con 12 entradas.
- Tabla **Variables** mostrando valores numericos cuando aplican.

Si aparece cualquier error de evaluacion, consideralo una regresion y revisa el bloque indicado.
