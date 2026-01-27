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

# =====================
# SUPABASE
# =====================
load_dotenv()
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# =====================
# LOAD DATA
# =====================
@st.cache_data(ttl=300)
def load_data():
    res = supabase.table("pickup_locations").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()

if df.empty:
    st.warning("Data pickup masih kosong")
    st.stop()

# =====================
# VALIDASI KOLOM & KOORDINAT
# =====================
kolom_wajib = ["nama_pickuper", "nama_mitra", "latitude", "longitude", "alamat"]
missing = [k for k in kolom_wajib if k not in df.columns]
if missing:
    st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")
    st.stop()

df = df[
    df["latitude"].between(-90, 90) &
    df["longitude"].between(-180, 180)
].dropna(subset=["latitude", "longitude"])

if df.empty:
    st.error("Semua data koordinat tidak valid")
    st.stop()

# =====================
# WARNA PICKUPER
# =====================
WARNA = [
    "red", "blue", "green", "purple", "orange",
    "darkred", "cadetblue", "darkgreen"
]

pickuper_list = sorted(df["nama_pickuper"].unique())
color_map = {p: WARNA[i % len(WARNA)] for i, p in enumerate(pickuper_list)}

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
# OSRM TRIP
# =====================
@st.cache_data(ttl=3600)
def osrm_trip(coords):
    if len(coords) < 2:
        return None

    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = (
        f"http://router.project-osrm.org/trip/v1/driving/"
        f"{coord_str}"
        "?overview=full&geometries=geojson&roundtrip=false&source=first"
    )

    try:
        res = requests.get(url, timeout=20)
        if res.status_code != 200:
            return None
        return res.json()
    except requests.RequestException:
        return None

# =====================
# POPUP CARD
# =====================
def popup_card(row):
    return f"""
    <div style="
        font-family:Arial, sans-serif;
        font-size:13px;
        line-height:1.5;
        width:260px;
    ">
        <div style="
            font-weight:bold;
            font-size:15px;
            margin-bottom:6px;
        ">
            📦 {row.nama_mitra}
        </div>

        <div style="
            border-top:1px solid #ddd;
            margin:6px 0 8px 0;
        "></div>

        <div style="margin-bottom:6px;">
            <b>👤 Petugas Pickup</b><br>
            {row.nama_pickuper}
        </div>

        <div style="margin-bottom:6px;">
            <b>📍 Alamat</b><br>
            {row.alamat}
        </div>

        <div>
            <b>🌐 Koordinat</b><br>
            Lat: {row.latitude:.6f}<br>
            Lon: {row.longitude:.6f}
        </div>
    </div>
    """

# =====================
# MAP INIT
# =====================
m = leafmap.Map()
MAX_TITIK = 50
all_bounds = []

# =====================
# DRAW MAP
# =====================
for pickuper in sorted(df["nama_pickuper"].unique()):
    df_p = df[df["nama_pickuper"] == pickuper].reset_index(drop=True)

    if len(df_p) < 2:
        continue

    if len(df_p) > MAX_TITIK:
        st.warning(
            f"{pickuper}: titik terlalu banyak ({len(df_p)}), dipotong {MAX_TITIK}"
        )
        df_p = df_p.iloc[:MAX_TITIK]

    coords = list(zip(df_p["latitude"], df_p["longitude"]))
    trip = osrm_trip(coords)

    if not trip:
        st.error(f"{pickuper}: gagal hitung rute OSRM")
        continue

    # === URUTAN OPTIMAL (PENTING, TIDAK DIHILANGKAN) ===
    order = [wp["waypoint_index"] for wp in trip["waypoints"]]
    df_p = df_p.iloc[order].reset_index(drop=True)

    # === MARKER ===
    for i, row in enumerate(df_p.itertuples(), 1):
        lat, lon = row.latitude, row.longitude
        all_bounds.append([lat, lon])

        folium.Marker(
            location=[lat, lon],
            tooltip=f"{i}. {row.nama_mitra}",
            popup=folium.Popup(popup_card(row), max_width=300),
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background:{color_map[pickuper]};
                    color:white;
                    border-radius:50%;
                    width:26px;
                    height:26px;
                    line-height:26px;
                    text-align:center;
                    font-weight:bold;
                ">
                    {i}
                </div>
                """
            )
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
# AUTO ZOOM KE DATA
# =====================
if all_bounds:
    lats = [b[0] for b in all_bounds]
    lons = [b[1] for b in all_bounds]
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

# =====================
# OUTPUT
# =====================
st.subheader("🗺️ Rute Pickup Optimal (Urutan & Popup Lengkap)")
m.to_streamlit()
