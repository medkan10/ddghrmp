import numpy as np
try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

import os, sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread

from google_oauth_io import get_oauth_creds


def run():
    st.title("📊 Payroll Activity Dashboard")

    SHEET_ID = "1BJd1ezT7UL3ka1XGYSQ25ZBYmXpw0jUh9UxAPTZ2ngA"
    WORKSHEET = "transactions"

    EXPECTED_HEADERS = [
        "NO", "Employee ID", "First Name", "Middle Name", "Last Name",
        "Gender", "Agency Code", "Agency", "Adj. Salary", "Current Salary",
        "Difference", "Current Position", "New position", "Reason",
        "LRD BANK", "LRD BANK ACCOUNT", "USD BANK", "USD ACCOUNT",
        "DOB", "Analyst", "uploaded_by", "uploaded_at"
    ]

    @st.cache_data(ttl=300)
    def load_master(_creds):
        gc = gspread.authorize(_creds)
        ws = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET)
        data = ws.get_all_records(expected_headers=EXPECTED_HEADERS)
        return pd.DataFrame(data)

    creds = get_oauth_creds()
    # st.write("Scopes granted:", creds.scopes)

    df = load_master(creds)

    if df.empty:
        st.info("No data yet. Upload a worksheet first.")
        st.stop()

    # -----------------------------
    # Clean + type conversions
    # -----------------------------
    # Numeric cols
    for col in ["Adj. Salary", "Current Salary", "Difference"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Date cols
    # uploaded_at is best for filtering; parse safely
    if "uploaded_at" in df.columns:
        df["uploaded_at"] = pd.to_datetime(df["uploaded_at"], errors="coerce")

    # Optional: parse DOB if you later want age bands
    if "DOB" in df.columns:
        df["DOB"] = pd.to_datetime(df["DOB"], errors="coerce")

    if "uploaded_at" in df.columns:
        df["uploaded_at"] = pd.to_datetime(df["uploaded_at"], errors="coerce")

    # -----------------------------
    # Payroll Month derivation
    # -----------------------------
    # Prefer a real payroll month column if present, else derive from uploaded_at
    payroll_month_col = None
    for c in ["Payroll Month", "Payroll_month", "payroll_month", "Month", "PayrollMonth"]:
        if c in df.columns:
            payroll_month_col = c
            break

    if payroll_month_col:
        df["payroll_month"] = df[payroll_month_col].astype(str).str.strip()
    else:
        # derive from uploaded_at
        if "uploaded_at" in df.columns:
            df["payroll_month"] = df["uploaded_at"].dt.to_period("M").astype(str)
        else:
            df["payroll_month"] = np.nan

    # -----------------------------
    # Salary band derivation (Adj. Salary)
    # -----------------------------
    if "Adj. Salary" in df.columns:
        df["Adj. Salary"] = pd.to_numeric(df["Adj. Salary"], errors="coerce").fillna(0)
    
    # -----------------------------
    # Filters
    # -----------------------------
    st.subheader("Filters")

    # Row 1: core filters
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)

    agency_vals = sorted(df["Agency"].dropna().unique()) if "Agency" in df.columns else []
    agency = fcol1.selectbox("Agency", ["All"] + agency_vals)

    gender_vals = sorted(df["Gender"].dropna().unique()) if "Gender" in df.columns else []
    gender = fcol2.selectbox("Gender", ["All"] + gender_vals)

    reason_vals = sorted(df["Reason"].dropna().unique()) if "Reason" in df.columns else []
    reason = fcol3.selectbox("Reason", ["All"] + reason_vals)

    # Analyst filter (STRICTLY Analyst)
    if "Analyst" in df.columns and df["Analyst"].notna().any():
        analyst_vals = sorted(df["Analyst"].dropna().unique())
        analyst = fcol4.selectbox("Analyst", ["All"] + analyst_vals)
    else:
        analyst = "All"
        fcol4.info("No Analyst column available.")

    # Row 2: payroll month + uploaded_by
    scol1, scol2, scol3 = st.columns(3)

    # Payroll month filter
    pm_vals = sorted(df["payroll_month"].dropna().unique()) if "payroll_month" in df.columns else []
    payroll_month = scol1.selectbox("Payroll Month", ["All"] + pm_vals)

    # Uploaded By filter (separate)
    if "uploaded_by" in df.columns and df["uploaded_by"].notna().any():
        uploaded_by_vals = sorted(df["uploaded_by"].dropna().unique())
        uploaded_by = scol2.selectbox("Uploaded By", ["All"] + uploaded_by_vals)
    else:
        uploaded_by = "All"
        scol2.caption("Uploaded By unavailable.")

    # -----------------------------
    # Bank filter
    # -----------------------------
    # Currency lane selector
    bank_lane = scol3.selectbox("Bank Currency Lane", ["All", "LRD", "USD"])

    bank_name = "All"
    if bank_lane == "LRD" and "LRD BANK" in df.columns:
        lrd_banks = sorted(df["LRD BANK"].dropna().unique())
        bank_name = st.selectbox("LRD Bank", ["All"] + lrd_banks)
    elif bank_lane == "USD" and "USD BANK" in df.columns:
        usd_banks = sorted(df["USD BANK"].dropna().unique())
        bank_name = st.selectbox("USD Bank", ["All"] + usd_banks)
    elif bank_lane != "All":
        st.caption("Selected lane has no bank column in data.")

    # -----------------------------
    # Salary band filter
    # -----------------------------
    st.markdown("**Salary Band (Adj. Salary)**")

    if "Adj. Salary" in df.columns:
        band_width = st.selectbox("Band width", [250, 500, 1000, 2000, 5000], index=2)

        max_salary = float(df["Adj. Salary"].max())
        bins = np.arange(0, max_salary + band_width, band_width)
        labels = [f"{int(b)}–{int(b+band_width)}" for b in bins[:-1]]
        df["salary_band"] = pd.cut(df["Adj. Salary"], bins=bins, labels=labels, include_lowest=True)

        band_vals = ["All"] + [str(x) for x in df["salary_band"].dropna().unique()]
        salary_band = st.selectbox("Select band", band_vals)
    else:
        salary_band = "All"
        st.caption("Adj. Salary column missing — salary band filter off.")

    # -----------------------------
    # Date filter (uploaded_at)
    # -----------------------------
    date_filter_on = "uploaded_at" in df.columns and df["uploaded_at"].notna().any()
    if date_filter_on:
        min_date = df["uploaded_at"].min().date()
        max_date = df["uploaded_at"].max().date()

        dcol1, dcol2 = st.columns(2)
        date_range = dcol1.date_input(
            "Date range (uploaded_at)",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date, end_date = None, None
        st.caption("Date filter disabled — no valid uploaded_at yet.")

    # -----------------------------
    # APPLY FILTERS
    # -----------------------------
    f = df.copy()

    if agency != "All" and "Agency" in f.columns:
        f = f[f["Agency"] == agency]

    if gender != "All" and "Gender" in f.columns:
        f = f[f["Gender"] == gender]

    if reason != "All" and "Reason" in f.columns:
        f = f[f["Reason"] == reason]

    if analyst != "All" and "Analyst" in f.columns:
        f = f[f["Analyst"] == analyst]

    if uploaded_by != "All" and "uploaded_by" in f.columns:
        f = f[f["uploaded_by"] == uploaded_by]

    if payroll_month != "All" and "payroll_month" in f.columns:
        f = f[f["payroll_month"] == payroll_month]

    # Bank filter logic
    if bank_lane == "LRD" and "LRD BANK" in f.columns:
        if bank_name != "All":
            f = f[f["LRD BANK"] == bank_name]
    elif bank_lane == "USD" and "USD BANK" in f.columns:
        if bank_name != "All":
            f = f[f["USD BANK"] == bank_name]

    # Salary band filter
    if salary_band != "All" and "salary_band" in f.columns:
        f = f[f["salary_band"].astype(str) == salary_band]

    # Date filter
    if date_filter_on and start_date and end_date:
        mask = f["uploaded_at"].dt.date.between(start_date, end_date)
        f = f[mask]

    # -----------------------------
    # Metrics
    # -----------------------------
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Transactions", f"{len(f):,}")
    m2.metric("Total Adj. Salary", f"{f['Adj. Salary'].sum():,.2f}")
    m3.metric("Total Current Salary", f"{f['Current Salary'].sum():,.2f}")
    m4.metric("Total Difference", f"{f['Difference'].sum():,.2f}")

    st.divider()

    # -----------------------------
    # Tables + Charts
    # -----------------------------
    

    st.subheader("Top Adjustments")
    top = f.sort_values("Difference", ascending=False).head(15)
    st.dataframe(top, use_container_width=True)

    st.subheader("Difference by Agency")
    by_agency = (
        f.groupby("Agency", as_index=False)["Difference"]
         .sum()
         .sort_values("Difference", ascending=False)
    )

    fig, ax = plt.subplots()
    ax.bar(by_agency["Agency"], by_agency["Difference"])
    ax.set_xticklabels(by_agency["Agency"], rotation=45, ha="right")
    ax.set_ylabel("Difference")
    st.pyplot(fig)

    st.subheader("Transactions by Reason")
    by_reason = f["Reason"].value_counts()

    fig2, ax2 = plt.subplots()
    ax2.bar(by_reason.index, by_reason.values)
    ax2.set_xticklabels(by_reason.index, rotation=30, ha="right")
    ax2.set_ylabel("Count")
    st.pyplot(fig2)


    st.divider()
    st.subheader("Agency → Analyst → Reason Flow")

    flow_df = f.copy()
    needed_cols = ["Agency", "Analyst", "Reason"]
    for c in needed_cols:
        if c not in flow_df.columns:
            flow_df[c] = "Unknown"

    # aggregate counts
    flow_agg = (
        flow_df.groupby(["Agency", "Analyst", "Reason"], dropna=False)
            .size()
            .reset_index(name="count")
    )

    if flow_agg.empty:
        st.info("No flow data for current filters.")
    else:
        if PLOTLY_OK:
            # ---- Sankey ----
            agencies = flow_agg["Agency"].astype(str).unique().tolist()
            analysts = flow_agg["Analyst"].astype(str).unique().tolist()
            reasons = flow_agg["Reason"].astype(str).unique().tolist()

            nodes = agencies + analysts + reasons
            node_index = {n: i for i, n in enumerate(nodes)}

            # Links: Agency -> Analyst
            a2an = (
                flow_agg.groupby(["Agency", "Analyst"])["count"]
                        .sum()
                        .reset_index()
            )
            source_a2an = [node_index[x] for x in a2an["Agency"].astype(str)]
            target_a2an = [node_index[x] for x in a2an["Analyst"].astype(str)]
            value_a2an  = a2an["count"].tolist()

            # Links: Analyst -> Reason
            an2r = (
                flow_agg.groupby(["Analyst", "Reason"])["count"]
                        .sum()
                        .reset_index()
            )
            source_an2r = [node_index[x] for x in an2r["Analyst"].astype(str)]
            target_an2r = [node_index[x] for x in an2r["Reason"].astype(str)]
            value_an2r  = an2r["count"].tolist()

            sankey_fig = go.Figure(go.Sankey(
                node=dict(label=nodes),
                link=dict(
                    source=source_a2an + source_an2r,
                    target=target_a2an + target_an2r,
                    value=value_a2an + value_an2r
                )
            ))
            sankey_fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(sankey_fig, use_container_width=True)

        else:
            # ---- Fallback bar chart ----
            st.caption("Plotly not installed — showing grouped bar instead.")
            bar_agg = (
                flow_agg.groupby(["Agency", "Reason"])["count"]
                        .sum()
                        .reset_index()
            )
            fig3, ax3 = plt.subplots()
            for ag in bar_agg["Agency"].unique():
                sub = bar_agg[bar_agg["Agency"] == ag]
                ax3.bar(sub["Reason"].astype(str), sub["count"], label=str(ag))
            ax3.set_xticklabels(bar_agg["Reason"].astype(str).unique(), rotation=30, ha="right")
            ax3.set_ylabel("Count")
            ax3.legend()
            st.pyplot(fig3)
