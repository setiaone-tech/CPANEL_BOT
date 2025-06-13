import streamlit as st
import requests
import xml.etree.ElementTree as ET
import time

# --- Kumpulan Fungsi API (Direvisi untuk Streamlit) ---

def check_domain_in_namecheap(domain, nc_creds):
    """Memeriksa apakah domain ada di dalam akun Namecheap tertentu."""
    params = {
        'ApiUser': nc_creds['api_user'],
        'ApiKey': nc_creds['api_key'],
        'UserName': nc_creds['username'],
        'ClientIp': nc_creds['client_ip'],
        'Command': 'namecheap.domains.getList'
    }
    try:
        response = requests.get("https://api.namecheap.com/xml.response", params=params, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        # Cari error di response XML
        if root.attrib.get('Status') == 'ERROR':
            error_msg = root.findtext('.//{http://api.namecheap.com/xml.response}Error')
            return False, f"API Error: {error_msg}"
            
        # Cari domain di dalam daftar
        for d in root.findall('.//{http://api.namecheap.com/xml.response}Domain'):
            if d.get('Name').lower() == domain.lower():
                return True, "Domain ditemukan."
        return False, "Domain tidak ditemukan di akun ini."
    except requests.RequestException as e:
        return False, f"Error koneksi: {e}"

def create_cloudflare_zone(domain, cf_token):
    """Membuat zone baru di Cloudflare dan mengembalikan nameserver-nya."""
    url = "https://api.cloudflare.com/client/v4/zones"
    headers = {"Authorization": f"Bearer {cf_token}", "Content-Type": "application/json"}
    payload = {"name": domain, "jump_start": True}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            zone_id = data["result"]["id"]
            nameservers = data["result"]["name_servers"]
            return True, zone_id, nameservers, f"Zone berhasil dibuat, ID: {zone_id}"
        else:
            # Error jika zona sudah ada akan ditangani di sini
            error_msg = data.get("errors", [{}])[0].get("message", "Unknown error")
            return False, None, None, f"Gagal membuat zone: {error_msg}"
    except requests.RequestException as e:
        return False, None, None, f"Error koneksi: {e}"

def set_namecheap_dns(domain, nameservers, nc_creds):
    """Mengatur nameserver kustom di Namecheap."""
    sld, tld = domain.split(".", 1)
    params = {
        'ApiUser': nc_creds['api_user'], 'ApiKey': nc_creds['api_key'],
        'UserName': nc_creds['username'], 'ClientIp': nc_creds['client_ip'],
        'Command': 'namecheap.domains.dns.setCustom',
        'SLD': sld, 'TLD': tld, 'Nameservers': ",".join(nameservers),
    }
    try:
        response = requests.get("https://api.namecheap.com/xml.response", params=params, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        if root.attrib.get('Status') == 'OK':
            return True, f"Nameserver berhasil diatur ke {', '.join(nameservers)}"
        else:
            error_msg = root.findtext('.//{http://api.namecheap.com/xml.response}Error')
            return False, f"Gagal atur NS: {error_msg}"
    except requests.RequestException as e:
        return False, f"Error koneksi: {e}"

def create_cloudflare_dns_record(zone_id, cf_token, record_type, name, content):
    """Membuat satu DNS record di Cloudflare."""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {cf_token}", "Content-Type": "application/json"}
    payload = {"type": record_type, "name": name, "content": content, "proxied": True}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return True, f"Record '{name}' -> '{content}' berhasil dibuat."
        else:
            error_msg = data.get("errors", [{}])[0].get("message", "Unknown error")
            return False, f"Gagal buat record '{name}': {error_msg}"
    except requests.RequestException as e:
        return False, f"Error koneksi: {e}"

# --- UI STREAMLIT ---
st.set_page_config(layout="wide", page_title="Onboard to Cloudflare", page_icon="🌐")
st.header("🌐 Onboard Domain to Cloudflare from Namecheap")
st.markdown("Tool untuk membuat Zone di Cloudflare & mengatur Nameserver di Namecheap secara otomatis.")

col1, col2 = st.columns(2, gap="large")

with col1:
    st.info("Kredensial Cloudflare", icon="☁️")
    cf_token = st.text_input("Cloudflare API Token", type="password")
    
    st.info("Konfigurasi Namecheap", icon="🔑")
    client_ip = st.text_input("Your Public IP Address (for Namecheap API)", help="Namecheap memerlukan IP publik Anda untuk keamanan.")
    
    # Tabs untuk beberapa akun Namecheap
    nc_tabs = st.tabs(["Akun Namecheap 1", "Akun Namecheap 2", "Akun Namecheap 3"])
    nc_credentials = []
    account_names = ["SN Gen", "SPS", "SN828"]
    for i, tab in enumerate(nc_tabs):
        with tab:
            st.subheader(f"Detail Akun: {account_names[i]}")
            api_user = st.text_input(f"API User ({account_names[i]})", key=f"user_{i}")
            api_key = st.text_input(f"API Key ({account_names[i]})", type="password", key=f"key_{i}")
            username = st.text_input(f"Username ({account_names[i]})", key=f"uname_{i}")
            if api_user and api_key and username:
                nc_credentials.append({
                    "name": account_names[i], "api_user": api_user,
                    "api_key": api_key, "username": username, "client_ip": client_ip
                })

with col2:
    st.info("Konfigurasi Proses", icon="⚙️")
    domain_list_file = st.file_uploader("Upload file (.txt) berisi daftar domain", type=['txt'])
    target_ip = st.text_input("IP Address Tujuan untuk A Records", "12.34.56.78")
    a_records_to_create = st.text_area(
        "A Records yang akan dibuat (satu per baris)",
        "@\nid\nth\nvn\nkr",
        help="Gunakan '@' untuk root domain."
    )

st.markdown("---")
# Tombol Eksekusi dan Log
st.subheader("Eksekusi dan Log Proses")
if st.button("🚀 Mulai Proses Onboarding!", type="primary", use_container_width=True):
    # Validasi
    if not cf_token or not client_ip or not domain_list_file or not nc_credentials:
        st.error("❌ Harap lengkapi Token Cloudflare, IP Klien, upload file domain, dan konfigurasikan setidaknya satu akun Namecheap.")
    else:
        domains = domain_list_file.getvalue().decode("utf-8").strip().splitlines()
        domains = [d for d in domains if d]
        a_records = [r.strip() for r in a_records_to_create.splitlines() if r.strip()]

        st.info(f"Memulai proses onboarding untuk {len(domains)} domain...")
        log_placeholder = st.empty()
        full_log_text = ""

        # Loop utama
        for i, domain in enumerate(domains):
            full_log_text += f"\n--- [{i+1}/{len(domains)}] MEMPROSES: {domain} ---\n"
            log_placeholder.code(full_log_text, language="log")
            
            # 1. Cari pemilik domain di Namecheap
            owner_account = None
            for creds in nc_credentials:
                found, msg = check_domain_in_namecheap(domain, creds)
                if found:
                    owner_account = creds
                    full_log_text += f"ℹ️ Ditemukan di akun Namecheap: {creds['name']}\n"
                    log_placeholder.code(full_log_text, language="log")
                    break
            
            if not owner_account:
                full_log_text += f"❌ Gagal: Domain tidak ditemukan di akun Namecheap manapun yang dikonfigurasi.\n"
                log_placeholder.code(full_log_text, language="log")
                continue # Lanjut ke domain berikutnya
            
            # 2. Buat Zone di Cloudflare
            success, zone_id, nameservers, msg = create_cloudflare_zone(domain, cf_token)
            full_log_text += f"☁️ Cloudflare Zone: {msg}\n"
            log_placeholder.code(full_log_text, language="log")
            if not success:
                continue

            # 3. Atur DNS di Namecheap
            success, msg = set_namecheap_dns(domain, nameservers, owner_account)
            full_log_text += f"🔑 Namecheap DNS: {msg}\n"
            log_placeholder.code(full_log_text, language="log")
            if not success:
                continue # Tetap lanjut buat record di CF

            # 4. Buat DNS records di Cloudflare
            for record_name in a_records:
                # Ganti '@' dengan nama domain untuk API call
                name_for_api = domain if record_name == '@' else record_name
                success, msg = create_cloudflare_dns_record(zone_id, cf_token, "A", name_for_api, target_ip)
                full_log_text += f"  - Record A ({name_for_api}): {msg}\n"
                log_placeholder.code(full_log_text, language="log")
                time.sleep(0.5) # Jeda antar pembuatan record

        st.success("🎉🎉 Seluruh proses onboarding telah selesai! 🎉🎉")