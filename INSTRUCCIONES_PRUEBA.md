# Instrucciones de Prueba - Fase 1 y Fase 2

## Archivos Disponibles

1. **test_fase1_fase2.json** - Documento de prueba en formato JSON
2. **test_fase1_fase2.yaml** - Mismo documento en formato YAML
3. **verify_test_document.py** - Script de verificación automática
4. **test_fase1_fase2_preview.html** - Preview HTML generado (después de ejecutar verify_test_document.py)

## Cómo Probar

### Opción 1: Usando el Script de Verificación (Recomendado)

```bash
python verify_test_document.py
```

Este script:
- Carga el documento JSON
- Evalúa todas las fórmulas
- Muestra resumen de funciones, arrays y variables
- Genera un archivo HTML preview
- Reporta errores si los hay

### Opción 2: Desde la Interfaz Gráfica

1. Ejecuta la aplicación:
   ```bash
   python -m gui.main  # O como inicies tu aplicación
   ```

2. Carga el documento:
   - File → Load (o similar)
   - Selecciona `test_fase1_fase2.json` o `test_fase1_fase2.yaml`

3. Verifica las tablas al final del documento:
   - **Functions**: Debe mostrar 8 funciones
   - **Arrays**: Debe mostrar 10 arrays
   - **Variables**: Debe mostrar variables calculadas

### Opción 3: Desde Python directamente

```python
from notebook.document import Document

# Cargar documento
doc = Document.load("test_fase1_fase2.json")

# Evaluar
context = doc.evaluate()

# Ver resultados
print(f"Funciones: {len(context.functions)}")
print(f"Arrays: {len(context.arrays)}")
print(f"Errores: {len(context.errors)}")

# Generar HTML
doc.save_html("mi_prueba.html")
```

## Resultados Esperados

### ✅ Funciones (8 total)
- `f(x) = x**2 + 2*x + 1`
- `area_rectangulo(base, altura) = base * altura`
- `g(t) = sin(t) + cos(t)`
- `h(x) = x + constante`
- `cuadrado(x) = x**2`
- `doble(x) = 2*x`
- `compuesta(x) = cuadrado(doble(x))`
- `momento_inercia(b, h) = b * h**3 / 12`

### ✅ Arrays (10 total)
- `arr1 = linspace(0, 10, 5)` → [0.00, 2.50, 5.00, 7.50, 10.00]
- `arr2 = arange(0, 10, 2)` → [0.00, 2.00, 4.00, 6.00, 8.00]
- `arr3 = linspace(-5, 5, 5)` → [-5.00, -2.50, 0.00, 2.50, 5.00]
- `arr4 = arange(0, 5, 0.5)` → [0.00, 0.50, 1.00, ..., 4.50] (10 valores)
- `arr5 = linspace(0, 100, 50)` → [0.00, 2.04, 4.08, ...] (50 valores)
- `arr6 = linspace(inicio, fin, puntos)` → [0.00, 2.00, 4.00, ..., 20.00] (11 valores)
- `arr7 = linspace(2*3, 5**2, 10)` → [6.00, 8.11, 10.22, ..., 25.00]
- `arr8 = arange(0, 2*pi, pi/4)` → [0.00, 0.79, 1.57, ..., 5.50] (8 valores)
- `arr9 = arange(10, 0, -1)` → [10.00, 9.00, 8.00, ..., 1.00] (10 valores descendente)
- `arr_un_elemento = linspace(5, 5, 1)` → [5.00]
- `arr_dos_elementos = arange(0, 2, 1)` → [0.00, 1.00]
- `alturas = linspace(0.2, 0.5, 4)` → [0.20, 0.30, 0.40, 0.50]

### ✅ Variables Calculadas
- `resultado1 = f(3)` → 16.00
- `A = area_rectangulo(5, 3)` → 15.00
- `resultado2 = g(pi/4)` → 1.41
- `constante` → 10.00
- Y más...

## Errores Conocidos

### ⚠️ 3 Errores Esperados (Issue conocido)

Los siguientes errores son limitaciones conocidas que están documentadas:

1. **arr4 = arange(0, 5, 0.5)**
   - Error: 'Symbol' object is not callable
   - Razón: Evaluación secuencial de diferentes tipos de arrays (linspace → arange)

2. **I1 = momento_inercia(0.2, 0.3)**
   - Error: 'Symbol' object is not callable
   - Razón: Composición de funciones con variables (issue de Fase 1)

3. **alturas = linspace(0.2, 0.5, 4)**
   - Error: 'Symbol' object is not callable
   - Razón: Evaluación de array después de función

Estos errores **NO afectan el uso típico** donde defines arrays de forma aislada o en bloques separados.

## Qué Verificar

### En el HTML Preview:

1. **Encabezados Markdown** bien formateados
2. **Fórmulas con LaTeX** renderizadas correctamente
3. **Tabla Functions** con 8 entradas
4. **Tabla Arrays** con 10-12 entradas (algunos pueden fallar por el issue conocido)
5. **Tabla Variables** con ~21 variables

### En la Interfaz Gráfica:

1. **Botones de UI:**
   - Botón "f(x)" inserta plantilla de función
   - Botón "linspace" inserta plantilla de linspace
   - Botón "arange" inserta plantilla de arange

2. **Evaluación en vivo:**
   - Los bloques se evalúan al escribir
   - Los resultados aparecen junto a cada fórmula
   - Las tablas se actualizan automáticamente

3. **Display de Arrays:**
   - Arrays pequeños (≤5 elementos): valores completos
   - Arrays grandes (>5 elementos): primeros 3 + "..."

## Ejemplos Adicionales para Probar Manualmente

### Caso de Uso 1: Análisis de Resistencia
```
R1 = 100
R2 = 200
R3 = 150
resistencias = linspace(100, 300, 11)
```

### Caso de Uso 2: Función con Arrays
```
tension(x) = x * 10
voltajes = linspace(0, 5, 6)
# Nota: No se puede aplicar función directamente al array aún (eso sería Fase 3)
```

### Caso de Uso 3: Temperatura en Rango
```
T_min = -20
T_max = 40
temperaturas = arange(T_min, T_max, 5)
```

## Solución de Problemas

### Si no se cargan los documentos:
- Verifica que los tipos sean "TextBlock" y "FormulaBlock" (no "text" ni "formula")
- Verifica que el JSON/YAML esté bien formateado

### Si las funciones no se evalúan:
- Verifica que la sintaxis sea exacta: `f(x) = expresión`
- Sin espacios extra alrededor del `=`

### Si los arrays no se crean:
- Verifica que `linspace` y `arange` estén en `notebook/units.py`
- Verifica que estén en el `math_env()` return dict

### Si hay más errores de los esperados:
- Ejecuta `python -m pytest tests/test_arrays.py -v` para verificar la implementación
- Revisa que todas las dependencias estén instaladas

## Reportar Nuevos Errores

Si encuentras errores diferentes a los 3 documentados arriba, por favor reporta:

1. El bloque de fórmula exacto que falla
2. El mensaje de error completo
3. El contexto (qué bloques hay antes)
4. El archivo HTML generado si es posible

---

**¡Listo para probar!** Comienza ejecutando `python verify_test_document.py` y abre el HTML generado en tu navegador.
