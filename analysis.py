from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
FILE = ROOT / "hr_analytics_synthetic_sample.xlsx"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

employees = pd.read_excel(FILE, sheet_name="Employees", parse_dates=["HireDate", "TerminationDate"])
monthly = pd.read_excel(FILE, sheet_name="Monthly_HR", parse_dates=["Month"])
comp = pd.read_excel(FILE, sheet_name="Compensation")
absences = pd.read_excel(FILE, sheet_name="Absences", parse_dates=["AbsenceDate"])
recruitment = pd.read_excel(FILE, sheet_name="Recruitment", parse_dates=["RequisitionOpenDate", "RequisitionCloseDate"])

# Data quality checks
checks = {
    "employee_rows": len(employees),
    "unique_employee_ids": employees["EmployeeID"].nunique(),
    "duplicate_employee_ids": int(employees["EmployeeID"].duplicated().sum()),
    "monthly_rows": len(monthly),
    "duplicate_months": int(monthly["Month"].duplicated().sum()),
    "missing_employee_salary": int(employees["BaseMonthlySalary_MXN"].isna().sum()),
    "negative_salary_rows": int((employees["BaseMonthlySalary_MXN"] < 0).sum()),
    "absence_rows": len(absences),
    "recruitment_rows": len(recruitment),
}
pd.DataFrame([checks]).to_csv(OUT / "data_quality_checks.csv", index=False)

# Summary by month
monthly = monthly.sort_values("Month")
monthly["PayrollChangePct"] = monthly["MonthlyPayroll_MXN"].pct_change()
monthly["HeadcountChangePct"] = monthly["Headcount_EOM"].pct_change()
monthly["PayrollPerEmployee_MXN"] = monthly["MonthlyPayroll_MXN"] / monthly["Headcount_EOM"]
monthly.to_csv(OUT / "monthly_kpis.csv", index=False)

# Snapshot at last reporting month
as_of = monthly["Month"].max() + pd.offsets.MonthEnd(0)
active = employees[
    (employees["HireDate"] <= as_of) &
    (employees["TerminationDate"].isna() | (employees["TerminationDate"] > as_of))
]
dept = active.groupby("Department", as_index=False).agg(
    Headcount=("EmployeeID", "nunique"),
    BaseMonthlyPayroll_MXN=("BaseMonthlySalary_MXN", "sum"),
    AverageBaseSalary_MXN=("BaseMonthlySalary_MXN", "mean"),
)
dept["PayrollSharePct"] = dept["BaseMonthlyPayroll_MXN"] / dept["BaseMonthlyPayroll_MXN"].sum()
dept.to_csv(OUT / "department_costs.csv", index=False)

# Data-quality note: monthly table is company-level aggregated, so not joined to department.
print("Created output tables in", OUT)
print("Monthly headcount change:", int(monthly.iloc[-1]["Headcount_EOM"] - monthly.iloc[0]["Headcount_EOM"]))
print("Monthly payroll change (%):", round((monthly.iloc[-1]["MonthlyPayroll_MXN"] / monthly.iloc[0]["MonthlyPayroll_MXN"] - 1) * 100, 2))
print("Active employees at snapshot:", len(active))
