import streamlit as st
import pandas as pd
import altair as alt
import leafmap.foliumap as leafmap
import folium
import requests
import os

from supabase import create_client

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="Peta Rute Pickup",
    layout="wide"
)

st.title("🗺️ Peta Rute Pickup Optimal")

# =====================
# SUPABASE
# =====================
SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials belum dikonfigurasi")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# LOAD DATA
# =====================
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    res = supabase.table("pickup_locations").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()

if df.empty:
    st.warning("Data pickup masih kosong")
    st.stop()

# =====================
# VALIDASI DATA
# =====================
kolom_wajib = ["nama_pickuper", "nama_mitra", "alamat", "latitude", "longitude"]
missing = [k for k in kolom_wajib if k not in df.columns]
if missing:
    st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")
    st.stop()

df = df[
    df["latitude"].between(-90, 90) &
    df["longitude"].between(-180, 180)
].dropna(subset=["latitude", "longitude"])

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
# SIDEBAR FILTER
# =====================
st.sidebar.header("🔎 Filter")

pilih_pickuper = st.sidebar.selectbox(
    "Pilih Pickuper",
    ["Semua"] + pickuper_list
)

df_filtered = df.copy()
if pilih_pickuper != "Semua":
    df_filtered = df_filtered[df_filtered["nama_pickuper"] == pilih_pickuper]

# =====================
# OSRM TRIP
# =====================
@st.cache_data(ttl=3600, show_spinner=False)
def osrm_trip(coords):
    if len(coords) < 2:
        return None

    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = (
        "http://router.project-osrm.org/trip/v1/driving/"
        f"{coord_str}"
        "?overview=full&geometries=geojson&roundtrip=false&source=first"
    )

    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return None
        return r.json()
    except requests.RequestException:
        return None

# =====================
# POPUP CARD
# =====================
def popup_card(row):
    return f"""
    <div style="font-size:13px;width:260px">
        <b>📦 {row.nama_mitra}</b><br><br>
        <b>👤 Pickuper</b><br>{row.nama_pickuper}<br><br>
        <b>📍 Alamat</b><br>{row.alamat}<br><br>
        <b>🌐 Koordinat</b><br>
        {row.latitude:.6f}, {row.longitude:.6f}
    </div>
    """

# =========================================================
# ===================== PETA (ATAS) =======================
# =========================================================
st.subheader("🗺️ Rute Pickup Optimal")

m = leafmap.Map()
all_bounds = []
MAX_TITIK = 50

for pickuper in sorted(df_filtered["nama_pickuper"].unique()):
    df_p = df_filtered[df_filtered["nama_pickuper"] == pickuper].reset_index(drop=True)

    if len(df_p) < 2:
        continue

    if len(df_p) > MAX_TITIK:
        df_p = df_p.iloc[:MAX_TITIK]

    coords = list(zip(df_p["latitude"], df_p["longitude"]))
    trip = osrm_trip(coords)

    if not trip:
        continue

    # === URUTAN OSRM (WAJIB) ===
    order = [wp["waypoint_index"] for wp in trip["waypoints"]]
    df_p = df_p.iloc[order].reset_index(drop=True)

    for i, row in enumerate(df_p.itertuples(), 1):
        all_bounds.append([row.latitude, row.longitude])

        folium.Marker(
            location=[row.latitude, row.longitude],
            tooltip=f"{i}. {row.nama_mitra}",
            popup=folium.Popup(popup_card(row), max_width=300),
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background:{color_map[pickuper]};
                    color:white;
                    border-radius:50%;
                    width:26px;height:26px;
                    text-align:center;
                    line-height:26px;
                    font-weight:bold;
                ">{i}</div>
                """
            )
        ).add_to(m)

    geometry = trip["trips"][0]["geometry"]["coordinates"]
    folium.PolyLine(
        locations=[[lat, lon] for lon, lat in geometry],
        color=color_map[pickuper],
        weight=4,
        opacity=0.85
    ).add_to(m)

if all_bounds:
    lats = [b[0] for b in all_bounds]
    lons = [b[1] for b in all_bounds]
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

m.to_streamlit(height=520)

# =========================================================
# ===================== BAWAH =============================
# =========================================================
col_tabel, col_grafik = st.columns([1.4, 1])

# =====================
# TABEL + PAGINATION
# =====================
with col_tabel:
    st.subheader("📋 Rekap Lokasi Pickup")

    PAGE_SIZE = 8
    total = len(df_filtered)
    total_page = (total - 1) // PAGE_SIZE + 1

    page = st.number_input(
        "Halaman",
        min_value=1,
        max_value=total_page,
        step=1
    )

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE

    st.dataframe(
        df_filtered.iloc[start:end][
            ["nama_mitra", "alamat", "nama_pickuper", "latitude", "longitude"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Menampilkan {start+1}-{min(end, total)} dari {total} data")

# =====================
# GRAFIK
# =====================
with col_grafik:
    st.subheader("📊 Jumlah Lokasi per Pickuper")

    rekap = (
        df_filtered
        .groupby("nama_pickuper")
        .size()
        .reset_index(name="jumlah_lokasi")
        .sort_values("jumlah_lokasi", ascending=False)
    )

    chart = alt.Chart(rekap).mark_bar().encode(
        x=alt.X("nama_pickuper:N", sort="-y", title="Pickuper"),
        y=alt.Y("jumlah_lokasi:Q", title="Jumlah Lokasi"),
        tooltip=["nama_pickuper", "jumlah_lokasi"]
    ).properties(height=320)

    st.altair_chart(chart, use_container_width=True)
