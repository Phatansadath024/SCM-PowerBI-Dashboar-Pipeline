"""Forecasting proof of concept for backlog trend analysis."""

import pandas as pd
from prophet import Prophet


def prepare_prophet_input(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Convert a time-series table into Prophet's ds/y format."""
    prophet_df = df[[date_col, value_col]].copy()
    prophet_df = prophet_df.rename(columns={date_col: "ds", value_col: "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"], errors="coerce")
    prophet_df["y"] = pd.to_numeric(prophet_df["y"], errors="coerce")
    prophet_df = prophet_df.dropna(subset=["ds", "y"])
    return prophet_df


def run_backlog_forecast(df: pd.DataFrame, periods: int = 12) -> pd.DataFrame:
    """
    Run a simple weekly backlog forecast.
    This was used as a proof of concept because the historical data period was short.
    """
    prophet_df = prepare_prophet_input(df, date_col="Due Date", value_col="Open Quantity")
    weekly_df = prophet_df.groupby(pd.Grouper(key="ds", freq="W"))["y"].sum().reset_index()

    model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
    model.fit(weekly_df)

    future = model.make_future_dataframe(periods=periods, freq="W")
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
