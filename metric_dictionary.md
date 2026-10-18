# Modelo de datos y catálogo de KPIs

## 1. Modelo lógico recomendado

El Excel contiene tablas a distintos niveles de granularidad. No se deben unir todas entre sí directamente porque produciría duplicación de filas y sobreestimación de costos.

```text
                    Employees (dimensión)
                   /    |      |       \
                  /     |      |        \
        Compensation  Absences Performance Recruitment
         (EmployeeID) (eventos) (EmployeeID + año) (requisición)

Monthly_HR (agregado mensual de empresa; separado)
```

### Tablas y granularidad
- **Employees**: una fila por `EmployeeID`. Atributos organizacionales, fecha de ingreso/salida y salario base.
- **Compensation**: una fila por `EmployeeID`. Salario base, porcentaje objetivo de bono, costo mensual estimado de prestaciones y compensación anualizada.
- **Monthly_HR**: una fila por mes. Indicadores agregados de toda la organización; no tiene llave de empleado ni departamento.
- **Absences**: una fila por evento de ausencia (`AbsenceID`).
- **Recruitment**: una fila por requisición (`RequisitionID`).
- **Performance**: una fila por empleado y año de evaluación.
- **Metric_Dictionary**: definiciones descriptivas.

### Reglas de modelado
1. Usa `EmployeeID` como clave entre `Employees`, `Compensation`, `Absences` y `Performance`.
2. `Recruitment` no tiene `EmployeeID`; relaciona por departamento/fecha solo si la pregunta lo permite, o analiza como proceso separado.
3. Mantén `Monthly_HR` como una serie temporal agregada. Para desglosar nómina por departamento y mes, necesitas una tabla de movimientos/snapshot mensual a nivel empleado.
4. No sumes `AnnualizedTotalComp_MXN` y `MonthlyPayroll_MXN` como si fueran conceptos contables equivalentes.
5. Revisa duplicados, valores faltantes, fechas imposibles y consistencia entre estatus y fechas.

## 2. KPIs y fórmulas

| KPI | Fórmula | Interpretación |
|---|---|---|
| Headcount al cierre | Número de empleados activos al último día del mes | Tamaño de la fuerza laboral |
| Cambio de headcount % | `(HC final / HC inicial) - 1` | Crecimiento o contracción |
| Nómina base mensual | `SUM(BaseMonthlySalary_MXN)` de empleados activos | Costo salarial base mensual estimado |
| Cambio de nómina % | `(Nómina final / Nómina inicial) - 1` | Cambio de gasto base |
| Salario base promedio | `Nómina base / Headcount` | Nivel promedio de salario |
| Nómina por empleado | `MonthlyPayroll_MXN / Headcount_EOM` | Métrica de intensidad de costo |
| Tasa de rotación mensual | `Bajas del mes / promedio(HC inicio, HC cierre)` | Flujo de salidas; define consistentemente el denominador |
| Rotación voluntaria | `Bajas voluntarias / promedio(HC inicio, HC cierre)` | Salidas voluntarias relativas a plantilla |
| Costo mensual de prestaciones | `SUM(MonthlyBenefitsCost_MXN)` para empleados activos | Estimación de costo de prestaciones |
| Compensación anualizada estimada | `SUM(AnnualizedTotalComp_MXN)` para empleados activos | Estimación de base + bono objetivo + prestaciones anualizadas |
| Días promedio para cubrir vacante | `AVG(DaysToFill)` solo en requisiciones `Hired` | Velocidad de contratación |
| Gasto de reclutamiento | `SUM(RecruitmentCost_MXN)` de requisiciones dentro del periodo | Gasto registrado en el dataset |
| Días de ausencia | `SUM(DaysAbsent)` dentro del periodo | Volumen de ausentismo registrado |

### Fórmulas de compensación del dataset
- Bono anual objetivo: `Salario mensual base × 12 × AnnualBonusTargetPct`.
- Prestaciones anualizadas: `MonthlyBenefitsCost_MXN × 12`.
- Compensación anualizada total: `Salario base mensual × 12 × (1 + % bono objetivo) + prestaciones mensuales × 12`.

**Advertencia:** estas fórmulas representan supuestos de práctica. No incluyen impuestos, contribuciones patronales, provisiones, costo de reemplazo ni costos indirectos.

## 3. Insights iniciales (datos sintéticos)
- Headcount: 362 a 436 entre octubre de 2024 y septiembre de 2026, crecimiento de 20.4%.
- Nómina base mensual: MXN 16.42M a MXN 19.59M, crecimiento de 19.3%.
- Salario base promedio: MXN 45,362 a MXN 44,924, descenso aproximado de 1.0%.
- Operations es el departamento con más empleados activos y mayor nómina base estimada en el snapshot final.
- IT tiene un salario promedio superior al resto en el snapshot final.

### Interpretación financiera
El crecimiento de nómina (19.3%) es ligeramente inferior al crecimiento de plantilla (20.4%). El salario promedio se mantiene aproximadamente estable y cae alrededor de 1% en el periodo. Una hipótesis para investigar sería que el crecimiento se explica más por volumen de plantilla y mezcla de puestos que por aumentos generalizados de salario. **No puede confirmarse con el dataset agregado**: se requiere comparar cohortes, movimientos salariales y costo por departamento mes a mes.

## 4. Diseño de dashboard
1. **Resumen ejecutivo**: headcount, nómina base, cambio porcentual, salario promedio y horas extra.
2. **Tendencias**: línea de nómina mensual y headcount; columnas de altas/bajas; nómina por empleado.
3. **Estructura de costos**: nómina base y headcount por departamento, tabla con participación porcentual.
4. **Eficiencia operativa**: ausencias por tipo, requisiciones por estado, días promedio para cubrir vacantes.
5. **Insights y limitaciones**: interpretación guiada y explicación de supuestos.

## 5. Próximos datos que añadir para un proyecto empresarial real
- Presupuesto mensual aprobado por departamento/centro de costo.
- Nómina real y costo patronal (según política y jurisdicción).
- FTE/horas contratadas, overtime pagado y costo de reemplazo.
- Employee snapshot mensual con `EmployeeID`, `Month`, `Department`, `CostCenter`, `FTE`, `Salary`, `Status`.
- Fechas efectivas de altas, bajas, promociones y aumentos.
- Moneda, tipo de cambio y reglas de conversión si hay operaciones multinacionales.
