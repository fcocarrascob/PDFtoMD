# Revisión del diagrama P–M de `pm_interaccion_simple.json`

## Hallazgos
- **El acero siempre se modela plastificado y con el mismo signo.** Los bloques definen las fuerzas de acero solo como `As_c * fy` y `As_t * fy`, sin depender de la posición del eje neutro ni del signo de deformación. Eso hace que la fuerza de tracción y compresión se cancelen (misma magnitud) y que el axial dependa casi solo del bloque de concreto, distorsionando el diagrama en la zona de tracción y balance.【F:pm_interaccion_simple.json†L212-L243】【F:pm_interaccion_simple.json†L272-L321】【F:pm_interaccion_simple.json†L540-L571】
- **No hay compatibilidad de deformaciones para el acero.** Solo se calcula un `c_balance`, pero nunca se usan deformaciones para limitar esfuerzos del acero; todas las ramas toman `fy` de forma constante, por lo que no hay transición entre dominios de tracción, balance y compresión.【F:pm_interaccion_simple.json†L507-L582】
- **ϕ fijo en todo el diagrama.** Se usa `phi = 0.65` para todos los puntos, ignorando el aumento hacia 0.9 en tracción ni la interpolación ACI en el dominio intermedio; esto aplana el diagrama y subestima la flexión pura, mientras sobrestima la compresión balanceada.【F:pm_interaccion_simple.json†L92-L112】
- **Falta el límite de carga axial pura/compresión espiral.** No se compara con 0.85 f'_c (A_g - A_{st}) + f_y A_{st} ni con la reducción por excentricidad mínima, por lo que los puntos de alta compresión se exceden respecto a un diagrama típico.【F:pm_interaccion_simple.json†L588-L656】

## Recomendación de corrección (a implementar tras aprobación)
1. **Aplicar compatibilidad de deformaciones** para cada valor de `c`: `eps_cu = 0.003`, `eps_t = eps_cu * (d_t - c) / c`, `eps_c = eps_cu * (c - d_c) / c` y esfuerzos de acero `fs = clamp(Es*eps, ±fy)` con signo según la deformación.
2. **Calcular la ϕ normativa por punto**: usar 0.65 en compresión, 0.9 en tracción (eps_t ≥ 0.005) y la interpolación lineal ACI en el rango intermedio.
3. **Recalcular P_n y M_n** con las fuerzas de acero dependientes de deformación, respetando el signo (tracción negativa), y añadir el chequeo del límite de compresión axial según 0.8·ϕ·P_0 o excentricidad mínima.
4. **Actualizar el JSON de ejemplo y la prueba**: incorporar funciones `Pn(c)`/`Mn(c)` que usen las ecuaciones anteriores y generar puntos en los tramos de tracción, balance y compresión con los nuevos valores esperados.

Si apruebas este enfoque, puedo actualizar el cuaderno y el test para reflejar un diagrama P–M más realista.
