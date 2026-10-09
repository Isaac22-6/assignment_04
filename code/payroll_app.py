"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

import streamlit as st

from payroll.compute import build_payroll, payroll_export
from payroll.extract import load_employees, load_timesheet

st.title("Salt City Coffee — Weekly Payroll")

st.write(
    "Upload this week's timesheet export. The roster is loaded automatically. "
    "Check the totals, fix anything flagged, then download the file for the "
    "payroll provider."
)

upload = st.file_uploader(
    "Upload weekly timesheet (CSV)", type="csv", key="timesheet"
)
roster = load_employees()

if upload is not None:
    timesheet = load_timesheet(upload)
    payroll = build_payroll(timesheet, roster)
    pay_date = payroll["payroll_date"].iloc[0]

    st.subheader(f"Pay period ending {pay_date}")

    employee_count = payroll_export(payroll)
    total_hours = payroll["hours_worked"].sum()
    total_pay = employee_count["total"].sum()
    overtime_weeks = len(employee_count[employee_count["hours"] > 40])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Employees paid", employee_count["employeeid"].nunique())
    col2.metric("Total hours", total_hours)
    col3.metric("Total gross pay", f"${total_pay:,.2f}")
    col4.metric("Overtime weeks", overtime_weeks)

    unmatched = payroll[payroll["pay_type"] == "unmatched"]
    unmatched_count = len(unmatched)
    if unmatched_count > 0:
        unmatched_ids = ", ".join(map(str, unmatched["employee_id"].unique()))
        st.warning(
            f"{unmatched_count} timesheet row(s) have an employee_id that is "
            f"not on the roster: {unmatched_ids}. They are NOT in the export - "
            "add them to HR's roster and re-upload."
        )

    st.dataframe(payroll)
    export_data = employee_count.to_csv(index=False)
    st.download_button(
        "Download Payroll CSV for the provider",
        key="download",
        data=export_data,
        file_name=f"payroll_{pay_date}.csv",
        mime="text/csv",
    )