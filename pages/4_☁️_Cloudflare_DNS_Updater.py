import streamlit as st
import requests
import time

# --- Fungsi Inti (Direvisi untuk Fleksibilitas & Pelaporan) ---

def update_cloudflare_dns(domain, api_token, records_to_update, new_content, proxied_status):
    """
    Memperbarui satu atau lebih DNS record untuk sebuah domain di Cloudflare.
    Mengembalikan list berisi pesan status.
    """
    log_messages = []
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # 1. Dapatkan Zone ID untuk domain
    try:
        zone_url = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
        response = requests.get(zone_url, headers=headers, timeout=10)
        response.raise_for_status()
        zone_data = response.json()

        if not zone_data.get("success") or not zone_data.get("result"):
            log_messages.append(f"❌ [{domain}] Gagal menemukan Zone di Cloudflare.")
            return log_messages
        
        zone_id = zone_data["result"][0]["id"]
        log_messages.append(f"ℹ️ [{domain}] Ditemukan Zone ID: {zone_id}")

    except requests.exceptions.RequestException as e:
        log_messages.append(f"🔥 [{domain}] Error koneksi saat mencari Zone ID: {e}")
        return log_messages

    # 2. Loop untuk setiap record yang ingin diupdate (misal: '@', 'www')
    for record_name in records_to_update:
        full_record_name = domain if record_name == '@' else f"{record_name}.{domain}"
        
        try:
            # Cari record yang spesifik untuk diupdate
            dns_records_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            params = {"type": "A", "name": full_record_name}
            dns_response = requests.get(dns_records_url, headers=headers, params=params, timeout=10)
            dns_response.raise_for_status()
            dns_data = dns_response.json()

            if not dns_data.get("success") or not dns_data.get("result"):
                log_messages.append(f"❓ [{domain}] Record 'A' untuk '{full_record_name}' tidak ditemukan, dilewati.")
                continue

            record_id = dns_data["result"][0]["id"]
            
            # 3. Update record yang ditemukan
            update_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
            update_payload = {
                "type": "A",
                "name": full_record_name,
                "content": new_content,
                "ttl": 1,  # 1 berarti TTL otomatis
                "proxied": proxied_status
            }

            update_response = requests.put(update_url, headers=headers, json=update_payload, timeout=15)
            update_response.raise_for_status()
            update_result = update_response.json()

            if update_result.get("success"):
                proxy_text = "DIPROXY" if proxied_status else "DNS ONLY"
                log_messages.append(f"✅ [{domain}] Record '{full_record_name}' berhasil diupdate ke '{new_content}' ({proxy_text}).")
            else:
                log_messages.append(f"❌ [{domain}] Gagal update '{full_record_name}': {update_result.get('errors', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            log_messages.append(f"🔥 [{domain}] Error koneksi saat memproses '{full_record_name}': {e}")
            continue # Lanjut ke record berikutnya jika satu gagal

    return log_messages

# --- Antarmuka Streamlit ---
st.set_page_config(page_title="Cloudflare DNS Updater", page_icon="☁️")
st.header("☁️ Cloudflare Mass DNS Updater")
st.markdown("Tool untuk memperbarui IP Address pada A Record secara massal untuk banyak domain.")

st.markdown("---")

# Kolom Konfigurasi
col1, col2 = st.columns(2)

with col1:
    st.info("Kredensial & Domain", icon="🔑")
    cloudflare_token = st.text_input("Cloudflare API Token", type="password")
    domain_list_file = st.file_uploader(
        "Upload file (.txt) berisi daftar domain",
        type=['txt'],
        help="Satu domain per baris."
    )

with col2:
    st.info("Konfigurasi DNS Record", icon="⚙️")
    records_to_update_input = st.text_input(
        "Nama Record yang Diupdate (pisahkan koma)", 
        value="@,www",
        help="Gunakan '@' untuk root domain (contoh.com) dan 'www' untuk subdomain www (www.contoh.com)."
    )
    new_ip_address = st.text_input(
        "IP Address Baru untuk A Record", 
        placeholder="Contoh: 12.34.56.78"
    )
    is_proxied = st.toggle("Status Proxy (Orange Cloud)", value=True, help="Aktifkan untuk menyalakan proxy Cloudflare, nonaktifkan untuk mode DNS Only.")

st.markdown("---")

# Tombol Eksekusi dan Area Log
st.subheader("Eksekusi dan Log Proses")
if st.button("🚀 Mulai Update DNS Massal!", type="primary", use_container_width=True):
    # Validasi input
    if not all([cloudflare_token, domain_list_file, records_to_update_input, new_ip_address]):
        st.error("❌ Harap lengkapi semua isian: Token, File Domain, Nama Record, dan IP Address Baru.")
    else:
        # Memproses input
        domains = domain_list_file.getvalue().decode("utf-8").strip().splitlines()
        domains = [d for d in domains if d] # Hapus baris kosong
        records_to_update = [r.strip() for r in records_to_update_input.split(',') if r.strip()]

        st.info(f"Memulai proses update untuk {len(domains)} domain...")
        log_placeholder = st.empty()
        full_log_text = ""

        # Loop utama untuk setiap domain
        for i, domain in enumerate(domains):
            log_header = f"\n--- [{i+1}/{len(domains)}] Memproses: {domain} ---"
            full_log_text += log_header + "\n"
            log_placeholder.code(full_log_text, language="log")
            
            # Panggil fungsi inti
            status_messages = update_cloudflare_dns(
                domain,
                cloudflare_token,
                records_to_update,
                new_ip_address,
                is_proxied
            )
            
            # Update log dengan semua pesan dari fungsi
            full_log_text += "\n".join(status_messages) + "\n"
            log_placeholder.code(full_log_text, language="log")
            
            # Beri jeda agar tidak overload API
            time.sleep(1) 

        st.success("🎉🎉 Seluruh proses update DNS telah selesai! 🎉🎉")
        st.balloons()