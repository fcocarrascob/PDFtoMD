#!/usr/bin/env python3
"""Script de verificación para el documento de prueba Fase 1 y Fase 2."""

from notebook.document import Document

def main():
    print("=" * 70)
    print("VERIFICACIÓN: Documento de Prueba Fase 1 + Fase 2")
    print("=" * 70)

    # Cargar documento
    print("\n[1/4] Cargando documento...")
    try:
        doc = Document.load("test_fase1_fase2.json")
        print(f"✓ Documento cargado: {len(doc.blocks)} bloques")
    except Exception as e:
        print(f"✗ Error al cargar: {e}")
        return

    # Evaluar documento
    print("\n[2/4] Evaluando documento...")
    try:
        context = doc.evaluate()
        print("✓ Evaluación completada")
    except Exception as e:
        print(f"✗ Error en evaluación: {e}")
        return

    # Verificar funciones
    print(f"\n[3/4] Verificando funciones...")
    print(f"  Funciones definidas: {len(context.functions)}")
    if context.functions:
        print("  Lista de funciones:")
        for name, func in context.functions.items():
            params = ", ".join(func.parameters)
            print(f"    - {name}({params})")

    # Verificar arrays
    print(f"\n[4/4] Verificando arrays...")
    print(f"  Arrays creados: {len(context.arrays)}")
    if context.arrays:
        print("  Lista de arrays:")
        for name, arr in context.arrays.items():
            length = len(arr.values)
            if length <= 3:
                values_str = str([round(v, 2) for v in arr.values])
            else:
                first_three = [round(v, 2) for v in arr.values[:3]]
                values_str = f"{first_three}... ({length} valores)"
            print(f"    - {name}: {values_str}")

    # Verificar variables
    print(f"\n[5/5] Verificando variables...")
    print(f"  Variables evaluadas: {len(context.variables)}")
    if context.variables:
        print("  Muestra de variables:")
        for var in context.variables[:10]:  # Solo primeras 10
            if var.numeric_value is not None:
                print(f"    - {var.name} = {var.numeric_value:.4f}")
            else:
                print(f"    - {var.name} = (no numérico)")

    # Verificar errores
    print(f"\n" + "=" * 70)
    if context.errors:
        print(f"⚠ ADVERTENCIA: {len(context.errors)} errores encontrados")
        for i, error in enumerate(context.errors, 1):
            print(f"\n  Error {i}:")
            print(f"    Bloque: {error['block_id'][:8]}...")
            print(f"    Tipo: {error['type']}")
            print(f"    Mensaje: {error['message']}")
    else:
        print("✓ Sin errores de evaluación")

    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print(f"  ✓ Funciones: {len(context.functions)}")
    print(f"  ✓ Arrays: {len(context.arrays)}")
    print(f"  ✓ Variables: {len(context.variables)}")
    print(f"  {'⚠' if context.errors else '✓'} Errores: {len(context.errors)}")
    print("=" * 70)

    # Generar HTML
    print("\n[OPCIONAL] Generando preview HTML...")
    try:
        doc.save_html("test_fase1_fase2_preview.html")
        print("✓ HTML generado: test_fase1_fase2_preview.html")
        print("  Abre este archivo en tu navegador para ver el resultado")
    except Exception as e:
        print(f"⚠ Error generando HTML: {e}")

if __name__ == "__main__":
    main()
