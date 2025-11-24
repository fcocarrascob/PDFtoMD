#!/usr/bin/env python3
"""Script de verificacion para el documento de prueba de la app completa."""

from notebook.document import Document


def main() -> None:
    print("=" * 70)
    print("VERIFICACION: Documento de Prueba (App Completa)")
    print("=" * 70)

    # Cargar documento
    print("\n[1/5] Cargando documento...")
    try:
        doc = Document.load("test_full_app.json")
        print(f"[OK] Documento cargado: {len(doc.blocks)} bloques")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] Al cargar: {exc}")
        return

    # Evaluar documento
    print("\n[2/5] Evaluando documento...")
    try:
        context = doc.evaluate()
        print("[OK] Evaluacion completada")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] En evaluacion: {exc}")
        return

    # Verificar funciones
    print("\n[3/5] Verificando funciones...")
    print(f"  Funciones definidas: {len(context.functions)}")
    if context.functions:
        for name, func in context.functions.items():
            params = ", ".join(func.parameters)
            print(f"    - {name}({params})")

    # Verificar arrays
    print("\n[4/5] Verificando arrays...")
    print(f"  Arrays creados: {len(context.arrays)}")
    if context.arrays:
        for name, arr in context.arrays.items():
            length = len(arr.values)
            if length <= 3:
                values_str = str([round(v, 2) for v in arr.values])
            else:
                first_three = [round(v, 2) for v in arr.values[:3]]
                values_str = f"{first_three}... ({length} valores)"
            print(f"    - {name}: {values_str}")

    # Verificar variables
    print("\n[5/5] Verificando variables...")
    print(f"  Variables evaluadas: {len(context.variables)}")
    if context.variables:
        for var in context.variables[:10]:  # Solo primeras 10
            if var.numeric_value is not None:
                print(f"    - {var.name} = {var.numeric_value:.4f}")
            else:
                print(f"    - {var.name} = (no numerico)")

    # Verificar errores
    print("\n" + "=" * 70)
    if context.errors:
        print(f"[AVISO] {len(context.errors)} errores encontrados")
        for i, error in enumerate(context.errors, 1):
            print(f"\n  Error {i}:")
            print(f"    Bloque: {error['block_id'][:8]}...")
            print(f"    Tipo: {error['type']}")
            print(f"    Mensaje: {error['message']}")
    else:
        print("[OK] Sin errores de evaluacion")

    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print(f"  Funciones: {len(context.functions)}")
    print(f"  Arrays: {len(context.arrays)}")
    print(f"  Variables: {len(context.variables)}")
    print(f"  Errores: {len(context.errors)}")
    print("=" * 70)

    # Generar HTML
    print("\n[OPCIONAL] Generando preview HTML...")
    try:
        doc.save_html("test_full_app_preview.html")
        print("[OK] HTML generado: test_full_app_preview.html")
        print("  Abre este archivo en tu navegador para ver el resultado")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] Generando HTML: {exc}")


if __name__ == "__main__":
    main()
