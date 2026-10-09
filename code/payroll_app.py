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

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.


import streamlit as st
import pandas as pd

from payroll.clean import add_hourly_rate
from payroll.compute import (
    add_hourly_rate as compute_add_hourly_rate,
    add_hours_worked,
    build_payroll,
    payroll_export
)
from payroll.extract import load_employees, load_timesheet

st.title("Salt City Coffee — Weekly Payroll")

st.write("Upload this week's timesheet export. The roster is loaded automatically.\
         Check the totals, fix anything flagged, then download the file for payroll provider")

upload = st.file_uploader("Upload weekly timesheet (CSV)", type="csv", key="timesheet")
roster = load_employees()

if upload is not None:
    timesheet = load_timesheet(upload)
    payroll = build_payroll(timesheet, roster)

    st.subheader(f"Pay period ending {payroll['payroll_date'].iloc[0]}")    

    employee_count = payroll_export(payroll)
    total_hours = payroll['hours_worked'].sum()
    total_pay = employee_count['total'].sum()
    overtime_weeks = len(employee_count[employee_count['hours'] > 40])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Employees paid", employee_count['employeeid'].nunique())
    col2.metric("Total hours", total_hours)
    col3.metric("Total gross pay", f"${total_pay:,.2f}")
    col4.metric("Overtime weeks", overtime_weeks)

    unmatched_count= len(payroll[payroll['pay_type'] == 'unmatched'])
    if unmatched_count > 0:
        unmatched_ids = payroll[payroll['pay_type'] == 'unmatched']['employee_id'].unique()
        st.warning(f"{unmatched_count} timesheet row(s) have an employee_id that is not on the roster: {', '.join(map(str, unmatched_ids))}. They are NOT in the\
                   the export - add them to HR's roster and re-upload")

    st.dataframe(payroll)
    export_data = employee_count.to_csv(index=False)
    st.download_button(
        "Download Payroll CSV for the provider",
        key="download",
        data= export_data,
        file_name=f"payroll_{payroll['payroll_date'].iloc[0]}.csv",
        mime="text/csv"
    )
