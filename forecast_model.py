import os
import pandas as pd
from prophet import Prophet

DATA_DIR = "data"

def load_series(company_name):
    path = os.path.join(DATA_DIR, f"{company_name}.csv")
    df = pd.read_csv(path)
    df = df.rename(columns={
        "date": "ds",
        "value": "y"
    })
    df["ds"] = pd.to_datetime(df["ds"], errors="coerce")
    df = df.dropna(subset=["ds", "y"])
    df = df.sort_values("ds")
    return df

def forecast_company(company_name, periods=30):
    df = load_series(company_name)
    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)
    return df, forecast
