import streamlit as st
import pandas as pd
import leafmap.foliumap as leafmap
import folium
import requests
import os

from supabase import create_client
from dotenv import load_dotenv

# =====================
# PAGE SETUP
# =====================
st.set_page_config(layout="wide")
st.title("📍 Peta Rute Pickup Optimal")

load_dotenv()
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# =====================
# LOAD DATA (CACHE)
# =====================
@st.cache_data(ttl=300)
def load_data():
    res = supabase.table("pickup_locations").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()

if df.empty:
    st.warning("Data pickup masih kosong")
    st.stop()

kolom_wajib = ["nama_pickuper", "nama_mitra", "latitude", "longitude", "alamat"]
missing = [k for k in kolom_wajib if k not in df.columns]
if missing:
    st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")
    st.stop()

# =====================
# WARNA PICKUPER
# =====================
warna = [
    "red", "blue", "green", "purple", "orange",
    "darkred", "cadetblue", "darkgreen"
]

pickuper_list = sorted(df["nama_pickuper"].dropna().unique())
color_map = {p: warna[i % len(warna)] for i, p in enumerate(pickuper_list)}

# =====================
# SIDEBAR
# =====================
st.sidebar.header("Filter")

pilih_pickuper = st.sidebar.selectbox(
    "Pilih Pickuper",
    ["Semua"] + pickuper_list
)

if pilih_pickuper != "Semua":
    df = df[df["nama_pickuper"] == pilih_pickuper]

st.sidebar.markdown("### 🎨 Warna Pickuper")
for p in pickuper_list:
    st.sidebar.markdown(
        f"""
        <div style="display:flex;align-items:center;margin-bottom:4px;">
            <span style="
                width:12px;height:12px;
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

# =====================
# OSRM TRIP (CACHE)
# =====================
@st.cache_data(ttl=3600)
def osrm_trip(coords):
    """
    coords: list of (lat, lon)
    """
    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])

    url = (
        f"http://router.project-osrm.org/trip/v1/driving/"
        f"{coord_str}"
        "?overview=full&geometries=geojson&roundtrip=false"
    )

    res = requests.get(url, timeout=20)
    if res.status_code != 200:
        return None

    return res.json()

# =====================
# MAP
# =====================
m = leafmap.Map(center=[-2.5, 118], zoom=5)

for pickuper in sorted(df["nama_pickuper"].unique()):
    df_p = df[df["nama_pickuper"] == pickuper].reset_index(drop=True)

    if len(df_p) == 1:
        row = df_p.iloc[0]
        folium.Marker(
            [row.latitude, row.longitude],
            tooltip=row.nama_mitra
        ).add_to(m)
        continue

    coords = list(zip(df_p["latitude"], df_p["longitude"]))

    trip = osrm_trip(coords)
    if not trip:
        st.warning(f"Gagal hitung rute OSRM untuk {pickuper}")
        continue

    # === URUTAN OPTIMAL ===
    order = [wp["waypoint_index"] for wp in trip["waypoints"]]
    df_p = df_p.iloc[order].reset_index(drop=True)

    # === MARKER ===
    for i, row in enumerate(df_p.itertuples(), 1):
        folium.Marker(
            [row.latitude, row.longitude],
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
                    width:26px;
                    height:26px;
                    line-height:26px;
                    text-align:center;
                    font-weight:bold;
                ">{i}</div>
            """)
        ).add_to(m)

    # === RUTE JALAN ===
    geometry = trip["trips"][0]["geometry"]["coordinates"]
    folium.PolyLine(
        locations=[[lat, lon] for lon, lat in geometry],
        color=color_map[pickuper],
        weight=4,
        opacity=0.85
    ).add_to(m)

# =====================
# OUTPUT
# =====================
st.subheader("🗺️ Rute Pickup Optimal (Ngikut Jalan)")
m.to_streamlit()
