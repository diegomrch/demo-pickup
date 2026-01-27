import streamlit as st

st.set_page_config(
    page_title="Tentang Sistem",
    layout="wide"
)

st.title("ℹ️ Tentang Sistem")

st.markdown("""
### 📦 Sistem Informasi Geografis (SIG) Pickup Mitra Korporat

Aplikasi ini merupakan **Sistem Informasi Geografis berbasis web** yang digunakan
untuk menampilkan, memantau, dan menganalisis **lokasi pickup mitra korporat**
berdasarkan data yang tersimpan pada **Supabase Database**.

---

### 🎯 Tujuan Sistem
- Menampilkan lokasi pickup secara **visual pada peta**
- Memudahkan monitoring pickup berdasarkan **pickuper**
- Menyajikan **rekap dan analisis data** lokasi pickup
- Mendukung pengambilan keputusan operasional

---

### 🧩 Fitur Utama
- 📋 Rekap data lokasi pickup
- 📊 Grafik jumlah lokasi per pickuper
- 🗺️ Peta interaktif lokasi pickup
- 🎨 Marker peta berbeda warna untuk setiap pickuper
- 🔍 Filter data berdasarkan pickuper

---

### 🛠 Teknologi yang Digunakan
- **Streamlit** – antarmuka web
- **Supabase** – database PostgreSQL
- **Leafmap & Folium** – visualisasi peta
- **Python & Pandas** – pengolahan data

---

### 👨‍🎓 Pengembang
- ARIO YUDHANTO - 714252018
- DIEGO RAUDYA TRIMEIDIANTO - 714252004
- D4 Teknik Informatika RPL  
- Universitas Logistik dan Bisnis Internasional (ULBI)
""")



