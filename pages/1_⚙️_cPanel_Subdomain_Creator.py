import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import time

# --- Fungsi Inti untuk Membuat Subdomain ---
# (Diadaptasi dari skrip Anda dengan penambahan parameter dan return value)

def create_subdomain(domain_url, subdomain, cpanel_password):
    """
    Mengirim permintaan ke cPanel UAPI untuk membuat subdomain.
    Mengembalikan pesan status berupa string.
    """
    # Menentukan username cPanel dari domain (maksimal 16 karakter)
    username = domain_url.split('.')[0]
    if len(username) > 16:
        username = username[:16]

    # Informasi otentikasi
    cpanel_user = username
    cpanel_host = f"https://{domain_url}:2083"
    uapi_url = f"{cpanel_host}/execute/SubDomain/addsubdomain"

    # Data payload untuk API
    data = {
        "domain": f"{subdomain}.{domain_url}",
        "rootdomain": domain_url,
        "dir": f"/home/{cpanel_user}/public_html/{subdomain}.{domain_url}"
    }

    try:
        # Mengirim permintaan POST dengan otentikasi
        response = requests.post(
            uapi_url,
            auth=HTTPBasicAuth(cpanel_user, cpanel_password),
            params=data,
            timeout=30  # Tambahkan timeout untuk mencegah hang
        )
        response.raise_for_status()  # Cek jika ada error HTTP (spt 401, 404, 500)

        result = response.json()
        if result.get("status") == 1:
            return f"✅ [Berhasil] {subdomain}.{domain_url} (user: {cpanel_user})"
        else:
            # Menampilkan pesan error dari cPanel jika ada
            error_message = result.get('errors', ['Unknown cPanel error.'])[0]
            return f"❌ [Gagal] {domain_url}: {error_message}"

    except requests.exceptions.RequestException as e:
        return f"🔥 [Error Koneksi] {domain_url}: {e}"
    except Exception as e:
        return f"💥 [Error Umum] {domain_url}: {e}"


# --- Antarmuka Streamlit ---

st.set_page_config(page_title="cPanel Subdomain Creator", page_icon="⚙️")

st.header("⚙️ cPanel Subdomain Creator")
st.markdown("Tool ini digunakan untuk membuat subdomain secara massal pada beberapa akun cPanel.")

st.markdown("---")

# 1. Input untuk data-data yang diperlukan
st.subheader("1. Masukkan Data")

cpanel_pass = st.text_input(
    "Password cPanel",
    type="password",
    help="Masukkan password yang sama untuk semua akun cPanel yang akan diproses."
)

uploaded_file = st.file_uploader(
    "Upload file (.txt) berisi daftar domain",
    type=["txt"],
    help="File harus berisi satu domain per baris. Contoh: domain1.com, domain2.com, dst."
)

subdomain_input = st.text_input(
    "Subdomain yang akan dibuat",
    placeholder="Contoh: blog, toko, f1",
    help="Jika lebih dari satu, pisahkan dengan koma (,). Contoh: f1, motogp, timnas"
)

st.markdown("---")

# 2. Tombol untuk eksekusi dan area untuk menampilkan log
st.subheader("2. Eksekusi dan Log")

if st.button("🚀 Mulai Proses Pembuatan!", type="primary"):
    # Validasi input sebelum memulai
    if not cpanel_pass or not uploaded_file or not subdomain_input:
        st.error("⚠️ Harap lengkapi semua isian: Password, File Domain, dan Subdomain.")
    else:
        # Memproses input
        domains = uploaded_file.getvalue().decode("utf-8").strip().splitlines()
        subdomains = [s.strip() for s in subdomain_input.split(',')]

        # Menghilangkan baris kosong jika ada di file .txt
        domains = [d for d in domains if d]

        st.info(f"Memulai proses untuk {len(domains)} domain dan {len(subdomains)} subdomain...")
        
        # Area untuk menampilkan log secara real-time
        log_placeholder = st.empty()
        full_log_text = ""

        # Looping untuk setiap domain dan subdomain
        for domain in domains:
            for subdo in subdomains:
                # Panggil fungsi inti
                status_message = create_subdomain(domain, subdo, cpanel_pass)
                
                # Update log
                full_log_text += status_message + "\n"
                log_placeholder.code(full_log_text, language="log")
                
                # Beri jeda sedikit agar tidak membebani server dan UI terlihat smooth
                time.sleep(0.5)

        st.success("🎉 Semua proses telah selesai!")
        st.balloons()