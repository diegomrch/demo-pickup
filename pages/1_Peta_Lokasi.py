import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap
import folium
import requests
import os

from supabase import create_client
from dotenv import load_dotenv
from math import radians, cos, sin, asin, sqrt

# =====================
# PAGE SETUP
# =====================
st.set_page_config(layout="wide")
st.title("📍 Peta Lokasi Pickup")

load_dotenv()
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# =====================
# AMBIL DATA
# =====================
response = supabase.table("pickup_locations").select("*").execute()
df = pd.DataFrame(response.data)

if df.empty:
    st.warning("Data pickup masih kosong")
    st.stop()

kolom_wajib = ["nama_pickuper", "nama_mitra", "latitude", "longitude", "alamat"]
missing = [k for k in kolom_wajib if k not in df.columns]
if missing:
    st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")
    st.stop()

df_asli = df.copy()

# =====================
# FUNGSI UTIL
# =====================
def jarak(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * (2 * asin(sqrt(a)))

def rute_jalan(lat1, lon1, lat2, lon2):
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
        "?overview=full&geometries=geojson"
    )
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        return None
    return res.json()["routes"][0]["geometry"]["coordinates"]

def urutkan_rute(df):
    if len(df) <= 1:
        return df

    df = df.copy()
    hasil = [df.iloc[0]]
    sisa = df.iloc[1:]

    while not sisa.empty:
        terakhir = hasil[-1]
        sisa["jarak"] = sisa.apply(
            lambda x: jarak(
                terakhir["latitude"], terakhir["longitude"],
                x["latitude"], x["longitude"]
            ),
            axis=1
        )
        terdekat = sisa.loc[sisa["jarak"].idxmin()]
        hasil.append(terdekat)
        sisa = sisa.drop(terdekat.name)

    return pd.DataFrame(hasil)

# =====================
# WARNA PICKUPER
# =====================
warna = [
    "red", "blue", "green", "purple", "orange",
    "darkred", "cadetblue", "darkgreen"
]

pickuper_semua = sorted(df_asli["nama_pickuper"].dropna().unique())

color_map = {
    p: warna[i % len(warna)]
    for i, p in enumerate(pickuper_semua)
}

# =====================
# FILTER SIDEBAR
# =====================
st.sidebar.header("Filter")

# === LEGEND WARNA PICKUPER ===
st.sidebar.markdown("### 🎨 Warna Pickuper")

for p in pickuper_semua:
    st.sidebar.markdown(
        f"""
        <div style="display:flex; align-items:center; margin-bottom:4px;">
            <span style="
                width:12px;
                height:12px;
                background:{color_map[p]};
                border-radius:50%;
                display:inline-block;
                margin-right:8px;
            "></span>
            <span>{p}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# === DROPDOWN FILTER ===
pilih_pickuper = st.sidebar.selectbox(
    "Pilih Pickuper",
    ["Semua"] + pickuper_semua
)

if pilih_pickuper != "Semua":
    df = df[df["nama_pickuper"] == pilih_pickuper]

# =====================
# PETA
# =====================
m = leafmap.Map(center=[-2.5, 118], zoom=5)

for pickuper in sorted(df["nama_pickuper"].dropna().unique()):
    df_p = urutkan_rute(df[df["nama_pickuper"] == pickuper])
    coords = []

    for i, row in enumerate(df_p.itertuples(), start=1):
        lat, lon = row.latitude, row.longitude
        coords.append([lat, lon])

        folium.Marker(
            [lat, lon],
            tooltip=f"{i}. {row.nama_mitra}",
            popup=f"""
                <b>{pickuper}</b><br>
                <b>Mitra:</b> {row.nama_mitra}<br>
                <b>Alamat:</b> {row.alamat}
            """,
            icon=folium.DivIcon(html=f"""
                <div style="
                    background:{color_map[pickuper]};
                    color:white;
                    border-radius:50%;
                    width:28px;
                    height:28px;
                    line-height:28px;
                    text-align:center;
                    font-weight:bold;
                ">{i}</div>
            """)
        ).add_to(m)

    for i in range(len(coords) - 1):
        jalan = rute_jalan(*coords[i], *coords[i + 1])
        if not jalan:
            continue

        folium.PolyLine(
            locations=[[lat, lon] for lon, lat in jalan],
            color=color_map[pickuper],
            weight=4,
            opacity=0.8
        ).add_to(m)

# =====================
# TAMPILKAN
# =====================
st.subheader("🗺️ Peta Rute Pickup per Pickuper")
m.to_streamlit()
