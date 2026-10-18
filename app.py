from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="HR Financial Analytics", page_icon="📊", layout="wide")

DATA_PATH = Path(__file__).parent / "hr_analytics_synthetic_sample.xlsx"
AS_OF = pd.Timestamp("2026-09-30")

@st.cache_data
def load_data(path):
    xls = pd.ExcelFile(path)
    data = {s: pd.read_excel(path, sheet_name=s) for s in xls.sheet_names}
    date_cols = {
        "Employees": ["HireDate", "TerminationDate"],
        "Monthly_HR": ["Month"],
        "Absences": ["AbsenceDate"],
        "Recruitment": ["RequisitionOpenDate", "RequisitionCloseDate"],
    }
    for sheet, cols in date_cols.items():
        for col in cols:
            data[sheet][col] = pd.to_datetime(data[sheet][col], errors="coerce")
    return data

if not DATA_PATH.exists():
    st.error(f"No se encontró el archivo de datos: {DATA_PATH.name}. Colócalo junto a app.py.")
    st.stop()

d = load_data(DATA_PATH)
employees = d["Employees"].copy()
monthly = d["Monthly_HR"].copy().sort_values("Month")
comp = d["Compensation"].copy()
absences = d["Absences"].copy()
recruitment = d["Recruitment"].copy()
performance = d["Performance"].copy()

# Consistent snapshot definition: employee active at the end of the selected period.
as_of = min(AS_OF, monthly["Month"].max() + pd.offsets.MonthEnd(0))
active = employees[
    (employees["HireDate"] <= as_of) &
    (employees["TerminationDate"].isna() | (employees["TerminationDate"] > as_of))
].copy()

st.title("HR Financial Analytics")
st.caption("Proyecto de portafolio · Python, pandas, Streamlit y Plotly · Datos sintéticos en MXN")
st.warning("Los datos son ficticios. Úsalos para practicar y demostrar metodología; no representan una empresa real.")

with st.sidebar:
    st.header("Filtros")
    min_month = monthly["Month"].min().date()
    max_month = monthly["Month"].max().date()
    date_range = st.date_input("Periodo de análisis", value=(min_month, max_month),
                               min_value=min_month, max_value=max_month)
    departments = sorted(employees["Department"].dropna().unique().tolist())
    selected_depts = st.multiselect("Departamentos", departments, default=departments)
    st.caption("Nota: la serie mensual de nómina y headcount viene agregada a nivel empresa; no se puede desglosar por departamento con esta tabla.")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = monthly["Month"].min(), monthly["Month"].max()

# Date selectors are day-based; include the full months touched by the selected range.
start_month = start_date.to_period("M").to_timestamp()
end_month = end_date.to_period("M").to_timestamp()
monthly_f = monthly[(monthly["Month"] >= start_month) & (monthly["Month"] <= end_month)].copy()
if monthly_f.empty:
    st.error("El periodo seleccionado no contiene meses del dataset.")
    st.stop()

# Department and employee-level KPIs use the closing snapshot of the selected period.
snapshot_date = monthly_f["Month"].max() + pd.offsets.MonthEnd(0)
active = employees[
    (employees["HireDate"] <= snapshot_date) &
    (employees["TerminationDate"].isna() | (employees["TerminationDate"] > snapshot_date))
].copy()
emp_f = active[active["Department"].isin(selected_depts)].copy()
comp_f = comp[comp["EmployeeID"].isin(emp_f["EmployeeID"])].copy()
abs_f = absences[absences["EmployeeID"].isin(emp_f["EmployeeID"]) &
                 (absences["AbsenceDate"] >= start_date) & (absences["AbsenceDate"] <= end_date)].copy()
rec_f = recruitment[(recruitment["Department"].isin(selected_depts)) &
                    (recruitment["RequisitionOpenDate"] >= start_date) &
                    (recruitment["RequisitionOpenDate"] <= end_date)].copy()
perf_f = performance[performance["EmployeeID"].isin(emp_f["EmployeeID"])].copy()

latest = monthly_f.iloc[-1]
first = monthly_f.iloc[0]
headcount_change_pct = (latest["Headcount_EOM"] / first["Headcount_EOM"] - 1) if first["Headcount_EOM"] else np.nan
payroll_change_pct = (latest["MonthlyPayroll_MXN"] / first["MonthlyPayroll_MXN"] - 1) if first["MonthlyPayroll_MXN"] else np.nan
avg_hc = (monthly_f["Headcount_EOM"].shift(1) + monthly_f["Headcount_EOM"]) / 2
monthly_f["TurnoverRate"] = monthly_f["Exits"] / avg_hc.replace(0, np.nan)
monthly_f["VoluntaryTurnoverRate"] = monthly_f["VoluntaryExits"] / avg_hc.replace(0, np.nan)
monthly_f["PayrollPerEmployee"] = monthly_f["MonthlyPayroll_MXN"] / monthly_f["Headcount_EOM"].replace(0, np.nan)

monthly_benefits = comp_f["MonthlyBenefitsCost_MXN"].sum()
annualized_total_comp = comp_f["AnnualizedTotalComp_MXN"].sum()
monthly_base_payroll = emp_f["BaseMonthlySalary_MXN"].sum()
avg_salary = emp_f["BaseMonthlySalary_MXN"].mean()
absence_days = abs_f["DaysAbsent"].sum()
hired_reqs = rec_f[rec_f["RecruitmentStatus"] == "Hired"]
avg_days_to_fill = hired_reqs["DaysToFill"].mean()
recruitment_spend = rec_f["RecruitmentCost_MXN"].sum()
avg_rating = perf_f["PerformanceRating"].mean()

# KPI row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Headcount al cierre", f"{int(latest['Headcount_EOM']):,}",
          f"{headcount_change_pct:+.1%} vs. primer mes")
k2.metric("Nómina base mensual", f"${latest['MonthlyPayroll_MXN']/1e6:.2f} M",
          f"{payroll_change_pct:+.1%} vs. primer mes")
k3.metric("Salario base promedio", f"${latest['AverageSalary_MXN']:,.0f}")
k4.metric("Horas extra (último mes)", f"{int(latest['OvertimeHours']):,}")

st.subheader("1. Evolución financiera y de plantilla")
c1, c2 = st.columns(2)
with c1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly_f["Month"], y=monthly_f["MonthlyPayroll_MXN"]/1e6,
                             name="Nómina base (MXN M)", mode="lines+markers"))
    fig.update_layout(title="Nómina base mensual", xaxis_title="", yaxis_title="MXN millones",
                      hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly_f["Month"], y=monthly_f["Headcount_EOM"],
                             name="Headcount", mode="lines+markers"))
    fig.update_layout(title="Headcount al cierre de mes", xaxis_title="", yaxis_title="Empleados",
                      hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    fig = px.bar(monthly_f, x="Month", y=["NewHires", "Exits"],
                 barmode="group", title="Altas y bajas por mes", labels={"value": "Personas", "Month": ""})
    st.plotly_chart(fig, use_container_width=True)
with c4:
    fig = px.line(monthly_f, x="Month", y="PayrollPerEmployee", markers=True,
                  title="Nómina base por empleado", labels={"PayrollPerEmployee": "MXN por empleado", "Month": ""})
    st.plotly_chart(fig, use_container_width=True)

st.subheader("2. Estructura de costo por departamento")
dept_view = (emp_f.groupby("Department", as_index=False)
             .agg(Headcount=("EmployeeID", "nunique"),
                  BaseMonthlyPayroll_MXN=("BaseMonthlySalary_MXN", "sum"),
                  AverageBaseSalary_MXN=("BaseMonthlySalary_MXN", "mean")))
dept_view["PayrollSharePct"] = dept_view["BaseMonthlyPayroll_MXN"] / dept_view["BaseMonthlyPayroll_MXN"].sum()
c5, c6 = st.columns(2)
with c5:
    fig = px.bar(dept_view.sort_values("BaseMonthlyPayroll_MXN", ascending=False),
                 x="Department", y="BaseMonthlyPayroll_MXN", title="Nómina base mensual por departamento",
                 labels={"BaseMonthlyPayroll_MXN": "MXN", "Department": ""})
    st.plotly_chart(fig, use_container_width=True)
with c6:
    fig = px.bar(dept_view.sort_values("Headcount", ascending=False),
                 x="Department", y="Headcount", title="Headcount por departamento",
                 labels={"Headcount": "Empleados", "Department": ""})
    st.plotly_chart(fig, use_container_width=True)
st.dataframe(dept_view.style.format({
    "BaseMonthlyPayroll_MXN": "${:,.0f}",
    "AverageBaseSalary_MXN": "${:,.0f}",
    "PayrollSharePct": "{:.1%}"
}), use_container_width=True, hide_index=True)

st.subheader("3. Beneficios, ausentismo y contratación")
k5, k6, k7, k8 = st.columns(4)
k5.metric("Costo mensual de prestaciones*", f"${monthly_benefits:,.0f}")
k6.metric("Compensación anualizada estimada*", f"${annualized_total_comp:,.0f}")
k7.metric("Días de ausencia en el periodo", f"{int(absence_days):,}")
k8.metric("Días promedio para cubrir vacantes", f"{avg_days_to_fill:.1f}" if pd.notna(avg_days_to_fill) else "N/D")
st.caption("*Estimación para empleados activos del snapshot y supuestos del dataset. No equivale a nómina contable ni costo total real.")

c7, c8 = st.columns(2)
with c7:
    if not abs_f.empty:
        abs_by_type = abs_f.groupby("AbsenceType", as_index=False)["DaysAbsent"].sum()
        fig = px.bar(abs_by_type, x="AbsenceType", y="DaysAbsent", title="Días de ausencia por tipo",
                     labels={"AbsenceType": "", "DaysAbsent": "Días"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay registros de ausencia para los filtros seleccionados.")
with c8:
    if not rec_f.empty:
        funnel = rec_f.groupby("RecruitmentStatus", as_index=False).size().rename(columns={"size": "Requisitions"})
        fig = px.bar(funnel, x="RecruitmentStatus", y="Requisitions", title="Requisiciones por estatus",
                     labels={"RecruitmentStatus": "", "Requisitions": "Requisiciones"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay requisiciones para los filtros seleccionados.")

st.subheader("4. Resumen ejecutivo generado a partir de los filtros")
st.markdown(f"""
- La plantilla pasó de **{int(first['Headcount_EOM']):,}** a **{int(latest['Headcount_EOM']):,}** empleados en los meses incluidos (**{headcount_change_pct:+.1%}**).
- La nómina base mensual pasó de **${first['MonthlyPayroll_MXN']:,.0f}** a **${latest['MonthlyPayroll_MXN']:,.0f} MXN** (**{payroll_change_pct:+.1%}**).
- Los departamentos seleccionados suman **{len(emp_f):,} empleados activos** y una nómina base mensual estimada de **${monthly_base_payroll:,.0f} MXN**.
- El dataset registra **{int(absence_days):,} días de ausencia** en el periodo filtrado y **{len(rec_f):,} requisiciones abiertas** según la fecha de apertura.
""")
st.info("Interpretación: usa estos indicadores como señales para investigar. Un aumento de nómina puede reflejar más empleados, cambios salariales o mezcla de puestos; por sí solo no demuestra ineficiencia.")

with st.expander("Definiciones, supuestos y limitaciones"):
    st.markdown("""
    **Definiciones principales**
    - Nómina base mensual: suma de salarios base de empleados activos al cierre del mes.
    - Headcount: empleados activos al cierre del mes.
    - Cambio de nómina: nómina del último mes del filtro / nómina del primer mes del filtro − 1.
    - Salario base promedio: promedio de salario mensual base entre empleados activos.
    - Días para cubrir vacante: promedio de `DaysToFill` solo para requisiciones con estatus `Hired`.
    - Costo de prestaciones y compensación anualizada: suma de supuestos de la hoja `Compensation` para empleados activos seleccionados.

    **Limitaciones importantes**
    - `Monthly_HR` es una tabla agregada por empresa; no permite analizar nómina mensual por departamento.
    - La tabla `Compensation` contiene supuestos sintéticos, no nómina contable.
    - No se incluye presupuesto aprobado; por tanto, no se puede calcular una variación real vs. presupuesto.
    - No se debe inferir causalidad entre desempeño, ausencias, compensación y rotación con este dataset.
    - Para análisis de rotación mensual, el primer mes del periodo no tiene headcount inicial en esta tabla; su tasa no se calcula de forma comparable.
    """)
