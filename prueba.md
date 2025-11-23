# Variables de entrada
$$ fc = 30.0\;MPa $$
Resultado: 30.00 MPa
$$ fy = 420.0\;MPa $$
Resultado: 420.00 MPa
$$ b = 300.0\;mm $$
Resultado: 300.00 mm
$$ h = 500.0\;mm $$
Resultado: 500.00 mm
$$ cobertura = 40.0\;mm $$
Resultado: 40.00 mm
$$ diametro_barra = 16.0\;mm $$
Resultado: 16.00 mm
$$ phi = 0.9 $$
Resultado: 0.900000000000000
$$ Mu = 200000000.0\;kN*m $$
Resultado: 200.00 kN*m
$$ d = h - cobertura - \frac{diametro_{barra}}{2}\;mm $$
Resultado: 452.00 mm
# Cálculo de As
$$ k = 1 / (2 * 0.85 * fc * b)\;1/GPa/m $$
Resultado: 65.36 1/GPa/m
$$ Mn = \frac{\mathrm{M}}{\phi}\;kN*m $$
Resultado: 222.22 kN*m
$$ R = \frac{d - \sqrt{d^{2} - 4 Mn k}}{2 k}\;m²*Pa $$
Resultado: 532670.80 m²*Pa
$$ As = \frac{R}{fy}\;mm² $$
Resultado: 1268.26 mm²

## Variables
| Name | Expression | Value | Units |
| --- | --- | --- | --- |
| fc | $$ 30.0 $$ | 30.00 | MPa |
| fy | $$ 420.0 $$ | 420.00 | MPa |
| b | $$ 300.0 $$ | 300.00 | mm |
| h | $$ 500.0 $$ | 500.00 | mm |
| cobertura | $$ 40.0 $$ | 40.00 | mm |
| diametro_barra | $$ 16.0 $$ | 16.00 | mm |
| phi | $$ 0.9 $$ | 0.90 |  |
| Mu | $$ 200000000.0 $$ | 200.00 | kN*m |
| d | $$ h - cobertura - \frac{diametro_{barra}}{2} $$ | 452.00 | mm |
| k | $$ 1 / (2 * 0.85 * fc * b) $$ | 65.36 | 1/GPa/m |
| Mn | $$ \frac{\mathrm{M}}{\phi} $$ | 222.22 | kN*m |
| R | $$ \frac{d - \sqrt{d^{2} - 4 Mn k}}{2 k} $$ | 532670.80 | m²*Pa |
| As | $$ \frac{R}{fy} $$ | 1268.26 | mm² |