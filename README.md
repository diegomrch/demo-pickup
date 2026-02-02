# demo-pickup.github.io
Sistem Pemetaan Layanan Pick Up Pelanggan Korporat - SIG

Dibuat oleh
--------------------
1. Ario Yudhanto 714252018
2. Diego Raudya Trimeidianto 714252004

Latar Belakang
--------------------
Kondisi Eksisting, sebaran lokasi pelanggan korporat di Kantor Pos yang mendapat layanan pick up masih dicatat dalam google sheet dan pengaturan masih ditugaskan secara manual.
Jika ada perubahan petugas pickup maupun pengganti sementara, Supervisor terkait harus melakukan rekayasa manual dan belum berdasarkan perhitungan lokasi dan volume paket. Hal ini menimbulkan inefficiency baik segi operasional maupun biaya karena rute tidak optimal.

Solusi yang Diharapkan
--------------------
Menghubungkan data yang tersedia pada excel/google sheet dengan geolokasi / peta sehingga dapat memudahkan Supervisor terkait untuk melakukan rekayasa rute jika ada penambahan maupun perubahan sementara yang diharapkan dapat lebih efisien.

Milestone
--------------------
1. Melengkapi data longlat pada data pickup yang sudah ada
2. Melakukan penyimpanan data ke dalam database
3. Melakukan pengembangan sistem aplikasi berbasis geografis dengan teknologi Streamlit – antarmuka web, Supabase – database PostgreSQL, Leafmap & Folium – visualisasi peta, dan Python & Pandas – pengolahan data
4. Membuat fitur antara lain Rekap data lokasi pickup, Grafik jumlah lokasi per pickuper, Peta interaktif lokasi pickup, Marker peta berbeda warna untuk setiap pickuper, dan Filter data berdasarkan pickuper
5. Deploy aplikasi secara live
