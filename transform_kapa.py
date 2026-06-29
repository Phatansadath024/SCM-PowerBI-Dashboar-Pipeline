"""Transformation and KPI logic for production planning reporting."""

import numpy as np
import pandas as pd

SHIFT_PER_DAY = 3
NET_HOURS_PER_SHIFT = 7.25
PB1_OEE_FALLBACK = 0.807


def clean_wayrts_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw WayRTS export data."""
    df = df.copy()

    date_cols = ["Start Date", "Due Date"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    numeric_cols = ["Planned Quantity", "Actual Quantity"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    text_cols = ["Customer", "Production Area", "Work Center", "Status"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    df = df.drop_duplicates(subset=["Task ID"])
    df = df[df["Planned Quantity"] > 0]

    return df


def apply_95_percent_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the business rule agreed during validation:
    tasks where actual quantity is already at least 95 percent of planned quantity
    are treated as almost finished and excluded from open backlog.
    """
    df = df.copy()
    df["Completion Ratio"] = np.where(
        df["Planned Quantity"] > 0,
        df["Actual Quantity"] / df["Planned Quantity"],
        0,
    )
    return df[df["Completion Ratio"] < 0.95].copy()


def add_calendar_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar week, month, and year fields for Power BI slicing."""
    df = df.copy()
    df["Due Year"] = df["Due Date"].dt.year
    df["Due Month"] = df["Due Date"].dt.to_period("M").astype(str)
    df["Due CW"] = df["Due Date"].dt.isocalendar().week.astype("Int64")
    return df


def calculate_backlog_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate open quantity and simple backlog indicators."""
    df = df.copy()
    df["Open Quantity"] = df["Planned Quantity"] - df["Actual Quantity"]
    df["Open Quantity"] = df["Open Quantity"].clip(lower=0)
    df["Is Overdue"] = df["Due Date"] < pd.Timestamp.today().normalize()
    return df


def calculate_capacity_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add simplified capacity fields used for reporting.
    The real company model can replace these assumptions with values from master data.
    """
    df = df.copy()
    df["OEE Assumption"] = np.where(
        df["Production Area"].str.upper().eq("PB1"),
        PB1_OEE_FALLBACK,
        0.85,
    )
    df["Required Net Hours"] = df["Open Quantity"] / df["OEE Assumption"].replace(0, np.nan)
    df["Required Shifts"] = df["Required Net Hours"] / NET_HOURS_PER_SHIFT
    df["Required Employee Days"] = df["Required Shifts"] / SHIFT_PER_DAY
    return df


def create_backlog_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a Power BI-friendly backlog summary by area and calendar week."""
    return (
        df.groupby(["Production Area", "Due Year", "Due CW"], dropna=False)
        .agg(
            Open_Tasks=("Task ID", "count"),
            Open_Quantity=("Open Quantity", "sum"),
            Required_Net_Hours=("Required Net Hours", "sum"),
            Overdue_Tasks=("Is Overdue", "sum"),
        )
        .reset_index()
    )


def create_customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a customer-level backlog view."""
    return (
        df.groupby(["Customer", "Production Area"], dropna=False)
        .agg(
            Open_Tasks=("Task ID", "count"),
            Open_Quantity=("Open Quantity", "sum"),
            Earliest_Due_Date=("Due Date", "min"),
        )
        .reset_index()
    )


def prepare_powerbi_tables(raw_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Complete transformation flow and return output tables for Power BI."""
    df = clean_wayrts_data(raw_df)
    df = apply_95_percent_filter(df)
    df = add_calendar_fields(df)
    df = calculate_backlog_fields(df)
    df = calculate_capacity_fields(df)

    return {
        "fact_production_backlog": df,
        "summary_backlog_by_area_week": create_backlog_summary(df),
        "summary_customer_backlog": create_customer_summary(df),
    }
