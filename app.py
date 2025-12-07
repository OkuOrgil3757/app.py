import streamlit as st
from audio_recorder_streamlit import audio_recorder
import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from forecast_model import forecast_company
from voice import recognize_and_parse

st.set_page_config(layout="wide")
st.title("🇲🇳 Mongolian Stock Price Forecast")

# COMPANY LIST
company_ids = {
    "APU": 90,
    "AIC": 54,
    "ADB": 550,
    "AARD": 326,
    "BDS": 522,
    "GLMT": 562,
    "GOV": 354,
    "INV": 553,
    "LEND": 545,
    "NEH": 71
}

ticker_to_name = {
    "APU": "APU",
    "AIC": "ARD DAATGAL",
    "ADB": "ARD CREDIT BBSB",
    "AARD": "ARD",
    "BDS": "BDSEC",
    "GLMT": "GOLOMT BANK",
    "GOV": "GOVI",
    "NEH": "DARKHAN NEKHII",
    "INV": "INVESCORE",
    "LEND": "LENDMN"
}

companies = list(ticker_to_name.keys())

# SESSION STATE
if "selected_company" not in st.session_state:
    st.session_state.selected_company = companies[0]
if "periods_slider" not in st.session_state:
    st.session_state.periods_slider = 30
if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None
if "last_recognized_text" not in st.session_state:
    st.session_state.last_recognized_text = ""

# VOICE COMMAND
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("""
    <div style="padding-top: 12px;">
    <strong>🎤 Speak your command</strong><br>
    <small style="color:#888">e.g. "Golomt Bank next 5 years", "APU 90 days"</small>
    </div>
    """, unsafe_allow_html=True)
with col2:
    audio_bytes = audio_recorder(text="", icon_name="microphone", icon_size="4x",
                                recording_color="#ff0066", neutral_color="#00d4ff")

# VOICE
if audio_bytes and audio_bytes != st.session_state.last_audio_bytes:
    st.session_state.last_audio_bytes = audio_bytes
    parsed_company, parsed_periods, recognized_text = recognize_and_parse(audio_bytes)
    
    if recognized_text:
        st.session_state.last_recognized_text = recognized_text
    
    if parsed_company:
        st.session_state.selected_company = parsed_company
    if parsed_periods:
        st.session_state.periods_slider = parsed_periods
    
    st.rerun()

# DISPLAY TEXT
if st.session_state.last_recognized_text:
    st.info(f"🎤 You said: **{st.session_state.last_recognized_text}**")

# SIDEBAR
with st.sidebar:
    st.markdown("###Stocks")

    name_df = pd.DataFrame({
        "Ticker": ticker_to_name.keys(),
        "Company": [ticker_to_name[t] for t in ticker_to_name.keys()]
    })
    st.table(name_df)

    selected_company = st.selectbox(
        "Select a Company",
        companies,
        index=companies.index(st.session_state.selected_company),
        format_func=lambda x: f"{x} - {ticker_to_name[x]}"
    )
    
    if selected_company != st.session_state.selected_company:
        st.session_state.selected_company = selected_company

# INPUTS
periods = st.number_input(
    "Forecast days:",
    min_value=1, max_value=3650, step=1,
    value=st.session_state.periods_slider
)

if periods != st.session_state.periods_slider:
    st.session_state.periods_slider = periods

company = st.session_state.selected_company
full_name = ticker_to_name[company]

# LOGO
logo_path = f"logos/{company}.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=180)

# FORECAST
df, forecast = forecast_company(company, periods=periods)
forecast_only = forecast.tail(periods)

# BUY / SELL SIGNAL
current_price = df['y'].iloc[-1]
future_price = forecast_only['yhat'].iloc[-1]
change_pct = ((future_price - current_price) / current_price) * 100

st.markdown("---")
if change_pct > 15:
    st.success(f"🚀 **STRONG BUY** – Expected **+{change_pct:.1f}%** in {periods} days")
elif change_pct > 5:
    st.info(f"🟢 **BUY** – Expected **+{change_pct:.1f}%** in {periods} days")
elif change_pct > -5:
    st.warning(f"🟡 **HOLD** – Expected **{change_pct:.1f}%** in {periods} days")
elif change_pct > -15:
    st.error(f"🔴 **SELL** – Expected **{change_pct:.1f}%** in {periods} days")
else:
    st.error(f"🔴 **STRONG SELL** – Expected **{change_pct:.1f}%** in {periods} days")

# CHART
st.markdown("---")
st.subheader(f"{full_name} — Historical Data + Forecast")

import plotly.graph_objects as go

fig = go.Figure()

# Historical data
fig.add_trace(go.Scatter(
    x=df["ds"],
    y=df["y"],
    mode='lines',
    name='Historical',
    line=dict(color='#1f77b4', width=2)
))

# Forecast
fig.add_trace(go.Scatter(
    x=forecast_only["ds"],
    y=forecast_only["yhat"],
    mode='lines',
    name='Forecast',
    line=dict(color='#ff7f0e', width=2, dash='dash')
))

# Confidence interval upper
fig.add_trace(go.Scatter(
    x=forecast_only["ds"],
    y=forecast_only["yhat_upper"],
    mode='lines',
    name='Upper Bound',
    line=dict(width=0),
    showlegend=False
))

# Confidence interval lower (with fill)
fig.add_trace(go.Scatter(
    x=forecast_only["ds"],
    y=forecast_only["yhat_lower"],
    mode='lines',
    name='95% Confidence',
    line=dict(width=0),
    fillcolor='rgba(255, 127, 14, 0.2)',
    fill='tonexty'
))

fig.update_layout(
    height=600,
    xaxis_title="Date",
    yaxis_title="Price",
    hovermode='x unified',
    template='plotly_white'
)

st.plotly_chart(fig, use_container_width=True)

# SCRAPE
def scrape_financial_table(company_id):
    url = f"https://mse.mn/mn/company/{company_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", class_="table table-bordered table-striped table-hover table-condensed")
    if table is None:
        return None

    df = pd.read_html(str(table))[0]
    return df

# FINANCIAL REPORTS TABLE
st.markdown("---")
st.subheader("Official Financial Reports (MSE.mn)")

company_id = company_ids[company]
table_df = scrape_financial_table(company_id)

if table_df is not None:
    st.dataframe(table_df, use_container_width=True)
else:
    st.error("No table found on MSE.mn")

# DOWNLOAD CSV
st.download_button(
    label="Download Forecast as CSV",
    data=forecast_only.to_csv(index=False).encode(),
    file_name=f"{company}_{full_name}_{periods}_days_forecast.csv",
)