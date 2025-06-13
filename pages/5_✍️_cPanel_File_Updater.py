import streamlit as st
import requests
import base64
import time

# --- Fungsi Inti ---

def edit_file_content(original_content, domain, cpanel_user, custom_replacements):
    """
    Melakukan find-and-replace pada konten file dengan placeholder dinamis.
    """
    content = original_content
    for find_text, replace_text in custom_replacements:
        # Ganti placeholder di dalam teks pengganti
        processed_replace_text = replace_text.replace("{domain}", domain).replace("{user}", cpanel_user)
        content = content.replace(find_text, processed_replace_text)
    return content

def upload_file_to_cpanel(domain, cpanel_password, dest_path, dest_filename, content):
    """
    Menggunakan cPanel API (Fileman::savefile) untuk menulis konten ke file.
    """
    cpanel_user = domain.split('.')[0]
    if len(cpanel_user) > 16:
        cpanel_user = cpanel_user[:16]

    cpanel_host = f"https://{domain}:2083"
    api_url = f"{cpanel_host}/json-api/cpanel"

    # Otentikasi menggunakan Basic Auth
    credentials = f"{cpanel_user}:{cpanel_password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    # Payload untuk API Fileman
    params = {
        "cpanel_jsonapi_user": cpanel_user,
        "cpanel_jsonapi_apiversion": "2",
        "cpanel_jsonapi_module": "Fileman",
        "cpanel_jsonapi_func": "savefile",
        "dir": dest_path,
        "filename": dest_filename,
        "content": content
    }

    try:
        response = requests.post(api_url, headers=headers, data=params, verify=False, timeout=30)
        requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)
        response.raise_for_status()
        
        result = response.json()
        if result.get('cpanelresult') and result['cpanelresult']['event']['result'] == 1:
            return True, f"✅ [{domain}] File '{dest_path}/{dest_filename}' berhasil diupdate."
        else:
            reason = result.get('cpanelresult', {}).get('data', [{}])[0].get('reason', 'Unknown cPanel error')
            return False, f"❌ [{domain}] Gagal update file: {reason}"

    except requests.exceptions.RequestException as e:
        return False, f"🔥 [{domain}] Error koneksi: {e}"
    except Exception as e:
        return False, f"💥 [{domain}] Error tidak terduga: {e}"

# --- Antarmuka Streamlit ---
st.set_page_config(page_title="cPanel File Updater", page_icon="✍️")
st.header("✍️ cPanel Specific File Updater")
st.markdown("Tool untuk meng-upload atau menimpa file spesifik di banyak akun cPanel secara massal.")

st.markdown("---")

# Kolom Konfigurasi
col1, col2 = st.columns(2, gap="large")

with col1:
    st.info("Kredensial & Sumber", icon="🔑")
    cpanel_password = st.text_input("Password cPanel", type="password", help="Password yang sama untuk semua akun.")
    domain_list_file = st.file_uploader("Upload file (.txt) berisi daftar domain", type=['txt'])
    source_file = st.file_uploader("Upload File yang Akan Dikirim", help="Ini adalah file dari komputer Anda yang akan di-upload.")

with col2:
    st.info("Tujuan & Pemrosesan", icon="⚙️")
    destination_path = st.text_input(
        "Path Folder Tujuan di Server",
        value="public_html/app/Http/Controllers/Frontend/",
        help="Path di dalam home direktori cPanel, contoh: `public_html/folder/`"
    )
    destination_filename = st.text_input(
        "Nama File Tujuan di Server",
        placeholder="Otomatis dari nama file upload",
        help="Nama file saat disimpan di server. Kosongkan untuk menggunakan nama asli file."
    )
    
    enable_replace = st.toggle("Aktifkan Penggantian Teks Dinamis?")
    custom_replaces_text = st.text_area(
        "Teks yang ingin diganti (satu per baris)",
        "DEFAULT_DOMAIN|{domain}\nADMIN_USER|{user}",
        help="Gunakan format: TEKS_LAMA|TEKS_BARU. Placeholder yang tersedia: {domain} dan {user}.",
        disabled=not enable_replace
    )

st.markdown("---")
# Tombol Eksekusi dan Log
st.subheader("Eksekusi dan Log Proses")
if st.button("🚀 Mulai Proses Update File!", type="primary", use_container_width=True):
    # Validasi input
    if not all([cpanel_password, domain_list_file, source_file, destination_path]):
        st.error("❌ Harap lengkapi semua isian: Password, File Domain, File Sumber, dan Path Tujuan.")
    else:
        # Memproses input
        domains = domain_list_file.getvalue().decode("utf-8").strip().splitlines()
        domains = [d for d in domains if d]
        source_content = source_file.getvalue().decode("utf-8")
        
        # Tentukan nama file tujuan
        final_dest_filename = destination_filename if destination_filename else source_file.name

        # Proses aturan penggantian teks
        custom_replacements = []
        if enable_replace:
            for line in custom_replaces_text.splitlines():
                if '|' in line:
                    parts = line.split('|', 1)
                    custom_replacements.append((parts[0], parts[1]))

        st.info(f"Memulai proses update file '{final_dest_filename}' untuk {len(domains)} domain...")
        log_placeholder = st.empty()
        full_log_text = ""

        # Loop utama
        for i, domain in enumerate(domains):
            log_header = f"\n--- [{i+1}/{len(domains)}] Memproses: {domain} ---"
            full_log_text += log_header + "\n"
            log_placeholder.code(full_log_text, language="log")

            content_to_upload = source_content
            # Edit konten jika diaktifkan
            if enable_replace:
                cpanel_user = domain.split('.')[0]
                if len(cpanel_user) > 16: cpanel_user = cpanel_user[:16]
                content_to_upload = edit_file_content(source_content, domain, cpanel_user, custom_replacements)
                full_log_text += f"ℹ️ Melakukan penggantian teks untuk {domain}\n"
                log_placeholder.code(full_log_text, language="log")
            
            # Panggil fungsi inti untuk upload
            success, message = upload_file_to_cpanel(domain, cpanel_password, destination_path, final_dest_filename, content_to_upload)
            
            full_log_text += message + "\n"
            log_placeholder.code(full_log_text, language="log")
            
            time.sleep(0.5)

        st.success("🎉🎉 Seluruh proses update file telah selesai! 🎉🎉")