# HR Financial Analytics — Python Portfolio Project

## Objetivo
Analizar la evolución de la plantilla y la nómina base, estimar costos de prestaciones/compensación y conectar indicadores de RR. HH. con preguntas financieras. Todos los datos son sintéticos.

## Archivos
- `app.py`: dashboard interactivo en Streamlit.
- `hr_analytics_synthetic_sample.xlsx`: fuente sintética original.
- `requirements.txt`: dependencias.
- `analysis.py`: análisis reproducible y generación de tablas resumen.
- `metric_dictionary.md`: modelo de datos, fórmulas y limitaciones.

## Cómo ejecutar
Requiere Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

El navegador abrirá el dashboard local. Mantén el Excel en la misma carpeta que `app.py`.

## Preguntas de negocio
1. ¿Cómo evolucionan headcount y nómina base mensual?
2. ¿Qué departamentos concentran el mayor costo salarial estimado?
3. ¿Cuánto representan las prestaciones y la compensación anualizada bajo los supuestos del dataset?
4. ¿Qué tipos de ausencia acumulan más días?
5. ¿Cuánto tarda en cubrirse una vacante y cuál es el gasto de contratación registrado?
6. ¿Qué información adicional se necesita para medir costo real vs. presupuesto?

## Hallazgos descriptivos de la muestra
- El headcount reportado pasa de 362 en octubre de 2024 a 436 en septiembre de 2026 (+20.4%).
- La nómina base mensual pasa de MXN 16.42 millones a MXN 19.59 millones (+19.3%).
- El salario base promedio reportado pasa de aproximadamente MXN 45,362 a MXN 44,924 (-1.0%).
- En el periodo de 24 meses, la tabla mensual registra 113 altas y 31 bajas. Para comparar cambio neto con el headcount, excluye las altas del primer mes porque el headcount inicial ya es un cierre de mes.
- En septiembre de 2026, Operations tiene el mayor headcount (112) y mayor nómina base estimada por departamento (aprox. MXN 4.64 millones); IT tiene un salario base promedio mayor (aprox. MXN 49,449).

Estos son resultados descriptivos de datos generados aleatoriamente; no prueban causas ni representan una organización real.

## Siguiente fase sugerida
Añadir una tabla de presupuesto mensual por departamento y centro de costo, así como nómina real, FTE, horas contratadas, costo patronal y fecha efectiva de movimientos. Esto permitiría construir análisis de variación vs. presupuesto y costo por FTE.
