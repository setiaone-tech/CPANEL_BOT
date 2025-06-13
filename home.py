import streamlit as st

# Konfigurasi halaman - ini harus menjadi perintah streamlit pertama yang dijalankan
st.set_page_config(
    page_title="CPANEL BOT Home",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.google.com', # Ganti dengan link bantuan Anda
        'Report a bug': "https://www.google.com", # Ganti dengan link report bug Anda
        'About': "# Ini adalah CPANEL BOT. Kumpulan tools otomatis!"
    }
)

# --- Halaman Utama ---

# Judul utama dengan gaya
st.markdown(
    """
    <style>
    .main-title {
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        color: #2a9df4;
    }
    .sub-header {
        text-align: center;
        font-size: 1.2rem;
        color: #6c757d;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<p class="main-title">🤖 CPANEL BOT</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Pusat Kendali untuk Tools Otomatis Anda</p>', unsafe_allow_html=True)

st.markdown("---")

# Kolom untuk penjelasan dan gambar/ikon
col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.header("Selamat Datang!")
    st.markdown(
        """
        CPANEL BOT adalah kumpulan alat (tools) yang dirancang untuk membantu dan mengotomatiskan
        berbagai tugas rutin Anda. Setiap alat di panel ini memiliki fungsi spesifik.

        #### Bagaimana Cara Menggunakannya?
        1.  **Pilih Tool**: Gunakan menu navigasi di **sidebar sebelah kiri** untuk memilih alat yang ingin Anda jalankan.
        2.  **Ikuti Instruksi**: Setiap alat akan menyediakan formulir atau tombol untuk memulai proses.
        3.  **Lihat Hasil**: Hasil atau log dari proses akan ditampilkan langsung di halaman alat tersebut.

        Silakan mulai dengan memilih salah satu tool yang tersedia.
        """
    )
    st.info("👈 **Mulai dari sini!** Pilih tool yang Anda butuhkan di sidebar.", icon="💡")

with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/8490/8490048.png", caption="Automate Your World")


st.markdown("---")
st.write("Dibuat dengan Streamlit untuk efisiensi kerja.")