import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Solar Dashboard", layout="wide")
st.title("Solar Data — Cross-Country Dashboard (Prototype)")

# let user pick local file paths (we assume cleaned CSVs in data/)
country_files = {
    "Benin": "data/benin_clean.csv",
    "Sierra Leone": "data/sierraleone_clean.csv",
    "Togo": "data/togo_clean.csv"
}

countries = st.multiselect("Select countries", list(country_files.keys()), default=["Benin"])
metrics = st.multiselect("Metrics", ["GHI", "DNI", "DHI", "Tamb"], default=["GHI"])

dataframes = {}
for c in countries:
    path = country_files[c]
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["Timestamp"])
        dataframes[c] = df
    else:
        st.warning(f"Missing file: {path}")

if dataframes:
    country = list(dataframes.keys())[0]
    df0 = dataframes[country]

    st.header(f"Time series — {', '.join(metrics)}")
    ts_df = pd.concat([df.assign(country=k) for k, df in dataframes.items()], ignore_index=True)
    fig = px.line(ts_df, x="Timestamp", y=metrics, color="country")
    st.plotly_chart(fig, use_container_width=True)

    st.header("Boxplot comparison")
    box_df = pd.concat([df[["Timestamp"]+metrics].assign(country=k) for k, df in dataframes.items()], ignore_index=True)
    for m in metrics:
        fig2 = px.box(box_df, x="country", y=m, points="outliers", title=f"Boxplot — {m}")
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Upload cleaned CSVs into data/ with names: benin_clean.csv, sierraleone_clean.csv, togo_clean.csv")
