import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import time

# --- Fungsi Inti untuk Membuat Akun FTP ---
# Diadaptasi dari skrip Anda untuk integrasi dengan Streamlit

def create_ftp_account(cpanel_host, cpanel_user, cpanel_admin_pass, domain_to_add_ftp, new_ftp_pass):
    """
    Menghubungi cPanel UAPI untuk membuat akun FTP baru.
    Mengembalikan pesan status berupa string.
    """
    # URL API untuk menambah akun FTP
    # Menggunakan requests.get sesuai dokumentasi cPanel UAPI untuk fungsi ini
    api_url = f"{cpanel_host}/execute/Ftp/add_ftp"

    # Username untuk akun FTP baru, diawali dengan 'ftp_'
    ftp_user = f"ftp_{cpanel_user}"
    
    # Parameter yang akan dikirim ke API
    params = {
        "user": ftp_user,
        "domain": domain_to_add_ftp,
        "pass": new_ftp_pass,
        "quota": "0",  # 0 berarti unlimited
        "homedir": ftp_user # Direktori home disamakan dengan username FTP
    }

    try:
        # Mengirim permintaan GET dengan otentikasi
        response = requests.get(
            api_url,
            auth=HTTPBasicAuth(cpanel_user, cpanel_admin_pass),
            params=params,
            timeout=30,
            verify=False # Sama seperti skrip asli, menonaktifkan verifikasi SSL
        )
        # Menonaktifkan peringatan karena verify=False
        requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)

        response.raise_for_status()  # Cek jika ada error HTTP (401, 404, 500)

        result = response.json()
        if result.get("status") == 1:
            return f"✅ [Berhasil] Akun FTP '{ftp_user}@{domain_to_add_ftp}' telah dibuat."
        else:
            # Menampilkan pesan error dari cPanel jika ada
            error_message = result.get('errors', ['Unknown cPanel error.'])[0]
            return f"❌ [Gagal] {domain_to_add_ftp}: {error_message}"

    except requests.exceptions.RequestException as e:
        return f"🔥 [Error Koneksi] {domain_to_add_ftp}: {e}"
    except Exception as e:
        return f"💥 [Error Umum] {domain_to_add_ftp}: {e}"


# --- Antarmuka Streamlit ---

st.set_page_config(page_title="FTP Account Creator", page_icon="🔑")

st.header("🔑 cPanel FTP Account Creator")
st.markdown("Gunakan tool ini untuk membuat akun FTP baru secara massal di berbagai domain.")

st.markdown("---")

# 1. Input dari pengguna
st.subheader("1. Masukkan Data Konfigurasi")

cpanel_host_url = st.text_input(
    "URL Host cPanel",
    placeholder="Contoh: https://123.45.67.89:2083",
    help="Masukkan URL lengkap (termasuk port 2083) dari server cPanel Anda."
)

cpanel_admin_password = st.text_input(
    "Password Akun cPanel",
    type="password",
    help="Password ini digunakan untuk otentikasi ke setiap akun cPanel."
)

new_account_password = st.text_input(
    "Password untuk Akun FTP Baru",
    type="password",
    help="Semua akun FTP baru yang dibuat akan menggunakan password ini."
)

uploaded_file = st.file_uploader(
    "Upload file (.txt) berisi daftar domain",
    type=["txt"],
    help="Satu domain per baris. Username cPanel akan diambil dari nama domain (misal, 'domainku' dari domainku.com)."
)

st.markdown("---")

# 2. Tombol eksekusi dan area log
st.subheader("2. Eksekusi dan Log Proses")

if st.button("🚀 Buat Akun FTP Sekarang!", type="primary"):
    # Validasi input
    if not all([cpanel_host_url, cpanel_admin_password, new_account_password, uploaded_file]):
        st.error("⚠️ Harap lengkapi semua isian sebelum memulai proses.")
    else:
        # Memproses file yang di-upload
        domains = uploaded_file.getvalue().decode("utf-8").strip().splitlines()
        domains = [d for d in domains if d] # Hapus baris kosong

        st.info(f"Memulai proses pembuatan {len(domains)} akun FTP...")
        
        # Placeholder untuk log real-time
        log_placeholder = st.empty()
        full_log_text = ""

        # Iterasi untuk setiap domain
        for domain in domains:
            # Dapatkan username cPanel dari domain (maks 16 karakter)
            cpanel_username = domain.split('.')[0]
            if len(cpanel_username) > 16:
                cpanel_username = cpanel_username[:16]

            # Panggil fungsi inti
            status_message = create_ftp_account(
                cpanel_host_url,
                cpanel_username,
                cpanel_admin_password,
                domain,
                new_account_password
            )
            
            # Update log di layar
            full_log_text += status_message + "\n"
            log_placeholder.code(full_log_text, language="log")
            
            # Jeda singkat
            time.sleep(0.5)

        st.success("🎉 Semua proses pembuatan akun FTP telah selesai!")
        st.balloons()