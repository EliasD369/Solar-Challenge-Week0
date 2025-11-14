import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import sys
import subprocess

st.set_page_config(page_title="Solar Dashboard", layout="wide")
st.title("Solar Data — Cross-Country Dashboard (Prototype)")


# Directories to search for CSVs (case variations)
SEARCH_DIRS = ["data", "Data", "."]

def find_csv_for(country_name):n
    for d in SEARCH_DIRS:
        pattern = os.path.join(d, "*.csv")
        for path in glob.glob(pattern):
            fn = os.path.basename(path).lower().replace("-", "").replace("_", "")
            if name_key in fn:
                return path
    return None


country_files = {
    "Benin": find_csv_for("Benin"),
    "Sierra Leone": find_csv_for("Sierra Leone"),
    "Togo": find_csv_for("Togo"),
}

countries = st.multiselect("Select countries", list(country_files.keys()),
                           default=[k for k,v in country_files.items() if v is not None][:1] or ["Benin"])
metrics = st.multiselect("Metrics", ["GHI", "DNI", "DHI", "Tamb"], default=["GHI"])

dataframes = {}
for c in countries:
    path = country_files.get(c)
    if path and os.path.exists(path):
        try:
            df = pd.read_csv(path)
        except Exception as e:
            st.warning(f"Failed to read {path}: {e}")
            continue

        # detect timestamp-like column
        timestamp_col = None
        for col in df.columns:
            low = col.lower()
            if any(k in low for k in ("time", "date", "timestamp", "datetime")):
                timestamp_col = col
                break

        if timestamp_col is not None:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
            df = df.rename(columns={timestamp_col: "Timestamp"})
        else:
            st.warning(f"No timestamp-like column found in {path}; using row index as x-axis.")
            df["Timestamp"] = pd.RangeIndex(start=0, stop=len(df))

        dataframes[c] = df
    else:
        st.info(f"No file found for {c}. Expected a CSV in {SEARCH_DIRS} with '{c.lower().replace(' ', '')}' in the filename.")

if dataframes:
    available_metrics = set().union(*(set(df.columns) for df in dataframes.values()))
    selected_metrics = [m for m in metrics if m in available_metrics]
    missing = [m for m in metrics if m not in available_metrics]
    if missing:
        st.warning(f"The following metrics were not found and will be skipped: {', '.join(missing)}")

    if not selected_metrics:
        st.error("No selected metrics are available in the loaded files. Pick other metrics or upload data with matching column names.")
    else:
        st.header(f"Time series — {', '.join(selected_metrics)}")
        ts_df = pd.concat([df.assign(country=k) for k, df in dataframes.items()], ignore_index=True)
        fig = px.line(ts_df, x="Timestamp", y=selected_metrics, color="country")
        st.plotly_chart(fig, use_container_width=True)

        st.header("Boxplot comparison")
        # Boxplot doesn't need Timestamp
        box_df = pd.concat([df[selected_metrics].assign(country=k) for k, df in dataframes.items()], ignore_index=True)
        for m in selected_metrics:
            fig2 = px.box(box_df, x="country", y=m, points="outliers", title=f"Boxplot — {m}")
            st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Place cleaned CSVs into `Data/` or `data/` with country names in the filename (e.g., 'benin-...csv').")


def _maybe_relaunch_with_streamlit():
    """If the user ran `python app/main.py`, try to re-run via `streamlit run` so they see the UI.
    If `streamlit` is not installed, print clear instructions.
    When running under Streamlit the environment contains STREAMLIT keys and we do nothing.
    """
    # If any STREAMLIT env var is present, we're already running under Streamlit.
    if any(k.startswith("STREAMLIT") for k in os.environ):
        return

    # If this file is executed directly (python app/main.py), relaunch via Streamlit.
    if __name__ == "__main__":
        script = os.path.abspath(__file__)
        cmd = ["streamlit", "run", script]
        try:
            print("Detected direct python execution — launching Streamlit UI...")
            # replace current process with streamlit where possible
            subprocess.check_call(cmd)
        except FileNotFoundError:
            print("Could not find the `streamlit` command. Install it with:\n    pip install streamlit")
            print(f"Or run the app later with:\n    streamlit run {script}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to launch Streamlit (exit {e.returncode}). You can run:\n    streamlit run {script}")
        except Exception as e:
            print(f"Unexpected error launching Streamlit: {e}\nRun with:\n    streamlit run {script}")
        finally:
            # exit so plain python doesn't continue into streamlit internals
            try:
                sys.exit(0)
            except SystemExit:
                pass


_maybe_relaunch_with_streamlit()
