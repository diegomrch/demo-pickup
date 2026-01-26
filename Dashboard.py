import streamlit as st
import pandas as pd
import altair as alt

from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="SIG Pickup Mitra Korporat",
    layout="wide"
)

st.title("📦 Sistem Informasi Geografis Pickup Mitra Korporat")

# Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

response = supabase.table("pickup_locations").select("*").execute()
df = pd.DataFrame(response.data)

# Sidebar filter
st.sidebar.header("Filter Data")
pickuper_list = ["Semua"] + sorted(df["nama_pickuper"].dropna().unique().tolist())
pilih_pickuper = st.sidebar.selectbox("Pilih Pickuper", pickuper_list)

if pilih_pickuper != "Semua":
    df = df[df["nama_pickuper"] == pilih_pickuper]


# ===== GRAFIK =====
st.subheader("📊 Grafik Jumlah Lokasi per Pickuper")

rekap = (
    df.groupby("nama_pickuper")
    .size()
    .reset_index(name="jumlah_lokasi")
    .sort_values("jumlah_lokasi", ascending=False)
)

chart = alt.Chart(rekap).mark_bar().encode(
    x=alt.X("nama_pickuper:N", sort="-y", title="Pickuper"),
    y=alt.Y("jumlah_lokasi:Q", title="Jumlah Lokasi Pickup"),
    color=alt.Color(
        "nama_pickuper:N",
        legend=alt.Legend(title="Pickuper")
    ),
    tooltip=["nama_pickuper", "jumlah_lokasi"]
).properties(
    height=400
)

st.altair_chart(chart, use_container_width=True)

# ===== REKAP DATA =====
st.subheader("📋 Rekap Data Lokasi Pickup")
st.dataframe(df, use_container_width=True)

