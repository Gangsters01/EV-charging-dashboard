import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="EV Dashboard", layout="wide")

st.title("⚡ EV Charging Analytics Dashboard")

# -------------------------------
# SNOWFLAKE CONNECTION
# -------------------------------
@st.cache_resource
def connect():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )

conn = connect()

# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data
def load_data(query):
    return pd.read_sql(query, conn)

fact = load_data("SELECT * FROM FACT_SESSIONS")
anomalies = load_data("SELECT * FROM ANOMALIES")
stations = load_data("SELECT * FROM DIM_STATIONS")

# -------------------------------
# FILTERS
# -------------------------------
st.subheader("🔎 Filters")

col1, col2 = st.columns(2)

with col1:
    charger_filter = st.multiselect(
        "Select Charger",
        fact["CHARGER_ID"].dropna().unique()
    )

with col2:
    tariff_filter = st.multiselect(
        "Select Tariff",
        fact["TARIFF_TYPE"].dropna().unique()
    )

# Apply filters
df = fact.copy()

if charger_filter:
    df = df[df["CHARGER_ID"].isin(charger_filter)]

if tariff_filter:
    df = df[df["TARIFF_TYPE"].isin(tariff_filter)]

# -------------------------------
# KPIs
# -------------------------------
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Sessions", len(df))
col2.metric("Revenue", f"${df['PRICE'].sum():,.0f}")
col3.metric("Energy", f"{df['ENERGY_KWH'].sum():,.0f}")
col4.metric("Anomalies", len(anomalies))

st.divider()

# -------------------------------
# TREND CHART
# -------------------------------
df["START_TIME_UTC"] = pd.to_datetime(df["START_TIME_UTC"])

trend = df.groupby(df["START_TIME_UTC"].dt.date).size().reset_index(name="count")

fig1 = px.line(trend, x="START_TIME_UTC", y="count", title="Daily Sessions")

st.plotly_chart(fig1, use_container_width=True)

# -------------------------------
# ENERGY BY CHARGER
# -------------------------------
energy = df.groupby("CHARGER_ID")["ENERGY_KWH"].sum().reset_index()

fig2 = px.bar(energy, x="CHARGER_ID", y="ENERGY_KWH", title="Energy by Charger")

st.plotly_chart(fig2, use_container_width=True)

# -------------------------------
# TARIFF DISTRIBUTION
# -------------------------------
tariff = df.groupby("TARIFF_TYPE")["PRICE"].sum().reset_index()

fig3 = px.pie(tariff, names="TARIFF_TYPE", values="PRICE", title="Revenue Distribution")

st.plotly_chart(fig3, use_container_width=True)

# -------------------------------
# ANOMALY ANALYSIS
# -------------------------------
st.subheader("🚨 Anomaly Analysis")

if not anomalies.empty:
    fig4 = px.scatter(
        anomalies,
        x="DURATION_SEC",
        y="ENERGY_KWH",
        color="ANOMALY_TYPE",
        title="Anomaly Detection"
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.dataframe(anomalies.head(20))

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.caption("⚡ Built using Snowflake + Streamlit + Plotly")