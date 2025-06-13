import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from fabric import Connection
import time

# Menonaktifkan peringatan karena sering menggunakan verify=False
requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)

# --- Kumpulan Fungsi API & SSH (Telah Direvisi) ---

# -- Fungsi Cloudflare (Tidak ada perubahan) --
def set_ssl_mode_strict(domain, cf_api_token):
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/json"
    }
    try:
        response_zone = requests.get(f"https://api.cloudflare.com/client/v4/zones", headers=headers, params={"name": domain}, timeout=10)
        response_zone.raise_for_status()
        data_zone = response_zone.json()
        if not (data_zone.get("success") and data_zone.get("result")):
            return False, f"Cloudflare: Gagal menemukan Zone ID untuk {domain}"
        zone_id = data_zone["result"][0]["id"]
        response_ssl = requests.patch(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl", headers=headers, json={"value": "strict"}, timeout=10)
        response_ssl.raise_for_status()
        data_ssl = response_ssl.json()
        if data_ssl.get("success"):
            return True, f"Cloudflare: SSL untuk {domain} berhasil diatur ke Full (Strict)."
        else:
            return False, f"Cloudflare: Gagal mengatur SSL untuk {domain}: {data_ssl.get('errors', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return False, f"Cloudflare: Error koneksi - {e}"

# -- Fungsi cPanel (Tidak ada perubahan) --
def update_db_password(domain, cpanel_pass, db_user_suffix, db_pass):
    cpanel_user = domain.split('.')[0]
    if len(cpanel_user) > 16: cpanel_user = cpanel_user[:16]
    db_user = f"{cpanel_user}_{db_user_suffix}"
    url = f'https://{domain}:2083/execute/Mysql/set_password?user={db_user}&password={db_pass}'
    try:
        response = requests.get(url, auth=HTTPBasicAuth(cpanel_user, cpanel_pass), verify=False, timeout=20)
        response.raise_for_status()
        result = response.json()
        if result.get('status') == 1:
            return True, f"DB Pass: Password DB untuk {db_user} berhasil diubah."
        else:
            return False, f"DB Pass: Gagal ubah password DB {db_user}: {result.get('errors', ['Unknown error'])[0]}"
    except requests.exceptions.RequestException as e:
        return False, f"DB Pass: Error koneksi - {e}"

def write_env_file(domain, cpanel_pass, content):
    cpanel_user = domain.split('.')[0]
    if len(cpanel_user) > 16: cpanel_user = cpanel_user[:16]
    url = f"https://{domain}:2083/execute/Fileman/save_file_content"
    params = {"dir": "public_html", "file": ".env", "content": content}
    try:
        response = requests.get(url, auth=HTTPBasicAuth(cpanel_user, cpanel_pass), params=params, verify=False, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get("status") == 1:
            return True, "ENV: File .env berhasil ditulis ke server."
        else:
            return False, f"ENV: Gagal menulis .env: {result.get('errors', ['Unknown error'])[0]}"
    except requests.exceptions.RequestException as e:
        return False, f"ENV: Error koneksi saat menulis .env - {e}"

# --- Fungsi SSH/Fabric (REVISI) ---
def deploy_via_ssh(server_ip, ssh_user, ssh_pass, git_repo_url, git_pat, backup_config):
    repo_url_with_pat = git_repo_url.replace("https://", f"https://{git_pat}@")
    try:
        with Connection(host=server_ip, user=ssh_user, connect_kwargs={"password": ssh_pass}) as conn:
            with conn.cd("public_html"):
                log = []
                # Langkah 1: Backup (Jika diaktifkan)
                if backup_config['enabled'] and backup_config['source'] and backup_config['dest']:
                    conn.run(f"mkdir -p {backup_config['dest']} && cp -r {backup_config['source']}/* {backup_config['dest']}/ 2>/dev/null", warn=True)
                    log.append(f"SSH: Backup '{backup_config['source']}' ke '{backup_config['dest']}' selesai.")
                
                # Langkah 2: Hapus semua file lama
                conn.run("find . -mindepth 1 -maxdepth 1 -not -name $(basename {backup_config['dest']}) -exec rm -rf {{}} \\;", warn=True)
                log.append("SSH: File lama (selain backup) dihapus.")
                
                # Langkah 3: Clone repo
                conn.run(f"git clone {repo_url_with_pat} .", warn=True)
                log.append("SSH: Git clone selesai.")

                # Langkah 4: Restore (Jika diaktifkan)
                if backup_config['enabled'] and backup_config['source'] and backup_config['dest']:
                    conn.run(f"mkdir -p {backup_config['source']} && cp -r {backup_config['dest']}/* {backup_config['source']}/ 2>/dev/null", warn=True)
                    conn.run(f"rm -rf {backup_config['dest']}", warn=True)
                    log.append(f"SSH: Restore dari '{backup_config['dest']}' ke '{backup_config['source']}' selesai.")

                # Langkah 5: Composer install
                conn.run("php /opt/cpanel/ea-php81/root/usr/bin/composer install --no-dev --optimize-autoloader", warn=True)
                log.append("SSH: Composer install selesai.")
        return True, "\n".join(log)
    except Exception as e:
        return False, f"SSH: Gagal total saat deployment: {e}"

def migrate_db_via_ssh(server_ip, ssh_user, ssh_pass, seeder_list):
    try:
        with Connection(host=server_ip, user=ssh_user, connect_kwargs={"password": ssh_pass}) as conn:
            with conn.cd("public_html"):
                log = []
                # Menjalankan migration
                result_migrate = conn.run("php artisan migrate --force", warn=True)
                log.append(f"SSH Migrate: `php artisan migrate --force` (Exit code: {result_migrate.exited})")
                
                # Menjalankan seeder kustom
                if seeder_list:
                    for seeder in seeder_list:
                        result_seed = conn.run(f"php artisan db:seed --class={seeder} --force", warn=True)
                        log.append(f"SSH Seed: `... --class={seeder}` (Exit code: {result_seed.exited})")
        return True, "\n".join(log)
    except Exception as e:
        return False, f"SSH: Gagal saat migrasi DB: {e}"

# --- Fungsi Helper (REVISI) ---
def edit_env_content(content, domain, cpanel_user, db_pass, db_config, custom_replaces):
    # Pola khusus
    content = content.replace('APP_URL=http://localhost', f'APP_URL=https://{domain}')
    content = content.replace(db_config['db_name_find'], f"DB_DATABASE={cpanel_user}_{db_config['db_name_suffix']}")
    content = content.replace(db_config['db_user_find'], f"DB_USERNAME={cpanel_user}_{db_config['db_user_suffix']}")
    content = content.replace('DB_PASSWORD=', f'DB_PASSWORD={db_pass}')
    
    # Penggantian kustom
    for find_text, replace_text in custom_replaces:
        content = content.replace(find_text, replace_text)
        
    return content

# --- UI STREAMLIT (DIREVISI TOTAL) ---
st.set_page_config(layout="wide", page_title="Deployment Orchestrator", page_icon="🚀")
st.header("🚀 Full Deployment Orchestrator")
st.markdown("Tool otomasi deployment dengan konfigurasi fleksibel.")

st.warning("**PERHATIAN:** Tool ini akan melakukan perubahan besar pada server. Gunakan dengan hati-hati dan pastikan semua kredensial sudah benar.", icon="⚠️")

# --- Kolom Konfigurasi ---
st.subheader("1. Konfigurasi & Kredensial")
col1, col2 = st.columns(2, gap="large")

with col1:
    st.info("Kredensial Utama", icon="🔑")
    server_ip = st.text_input("IP Address Server SSH", placeholder="123.45.67.89")
    ssh_password = st.text_input("Password cPanel / SSH", type="password")
    git_repo = st.text_input("URL Git Repository", "https://github.com/username/template_web.git")
    git_pat = st.text_input("GitHub PAT (Personal Access Token)", type="password")
    cloudflare_token = st.text_input("Cloudflare API Token", type="password")
    
    st.info("Konfigurasi Backup (Opsional)", icon="📦")
    enable_backup = st.toggle("Aktifkan Backup & Restore Folder")
    backup_source_folder = st.text_input("Folder yang di-backup/restore", "public/assets/img/article", disabled=not enable_backup)
    backup_dest_folder = st.text_input("Folder backup sementara", "../backup_images", disabled=not enable_backup)

with col2:
    st.info("File & Database", icon="📄")
    domain_list_file = st.file_uploader("Upload file .txt berisi domain", type=['txt'])
    env_file_template = st.file_uploader("Upload file .env.example", type=['txt', 'env'])
    db_password = st.text_input("Password Baru untuk Database", type="password", help="Password baru yang akan diatur untuk user DB.")

    st.info("Konfigurasi Seeder & .env", icon="⚙️")
    seeder_input = st.text_input("Jalankan Seeder (pisahkan dengan koma)", "SeoSettingSeeder,SubdomainSeeder", help="Kosongkan jika tidak ingin menjalankan seeder.")
    
    st.markdown("##### Konfigurasi `.env` Database")
    db_name_find = st.text_input("Teks `DB_DATABASE` yang dicari", "DB_DATABASE=laravel")
    db_name_suffix = st.text_input("Suffix untuk `DB_DATABASE` baru", "portal_news_laravel")
    db_user_find = st.text_input("Teks `DB_USERNAME` yang dicari", "DB_USERNAME=root")
    db_user_suffix = st.text_input("Suffix untuk `DB_USERNAME` baru", "root")

    st.markdown("##### Penggantian Tambahan `.env`")
    custom_replaces_text = st.text_area(
        "Teks lain yang ingin diganti (satu per baris)",
        "APP_ENV=local|APP_ENV=production\nAPP_DEBUG=true|APP_DEBUG=false",
        help="Gunakan format: TEKS_LAMA|TEKS_BARU"
    )

st.markdown("---")
# --- Tombol Eksekusi & Area Log ---
st.subheader("2. Eksekusi dan Log Proses")
if st.button("🚀 MULAI DEPLOYMENT MASSAL!", type="primary", use_container_width=True):
    # Validasi
    if not all([server_ip, ssh_password, git_repo, git_pat, cloudflare_token, db_password, env_file_template, domain_list_file]):
        st.error("❌ Harap lengkapi semua kredensial utama dan upload file yang diperlukan.")
    else:
        # Kumpulkan semua konfigurasi
        domains = domain_list_file.getvalue().decode("utf-8").strip().splitlines()
        domains = [d for d in domains if d]
        env_template_content = env_file_template.getvalue().decode("utf-8")
        
        backup_config = {"enabled": enable_backup, "source": backup_source_folder, "dest": backup_dest_folder}
        seeder_list = [s.strip() for s in seeder_input.split(',') if s.strip()]
        
        db_config = {
            "db_name_find": db_name_find, "db_name_suffix": db_name_suffix,
            "db_user_find": db_user_find, "db_user_suffix": db_user_suffix,
        }
        
        custom_replaces = []
        for line in custom_replaces_text.splitlines():
            if '|' in line:
                parts = line.split('|', 1)
                custom_replaces.append((parts[0], parts[1]))

        st.info(f"Memulai proses deployment untuk {len(domains)} domain...")
        log_placeholder = st.empty()
        full_log_text = ""

        # Loop utama
        for i, domain in enumerate(domains):
            cpanel_user = domain.split('.')[0]
            if len(cpanel_user) > 16: cpanel_user = cpanel_user[:16]

            log_header = f"\n{'='*50}\n[{i+1}/{len(domains)}] MEMPROSES: {domain}\n{'='*50}\n"
            full_log_text += log_header
            log_placeholder.code(full_log_text, language="log")

            edited_env = edit_env_content(env_template_content, domain, cpanel_user, db_password, db_config, custom_replaces)
            
            steps = [
                lambda: update_db_password(domain, ssh_password, db_user_suffix, db_password),
                lambda: deploy_via_ssh(server_ip, cpanel_user, ssh_password, git_repo, git_pat, backup_config),
                lambda: write_env_file(domain, ssh_password, edited_env),
                lambda: migrate_db_via_ssh(server_ip, cpanel_user, ssh_password, seeder_list),
                lambda: set_ssl_mode_strict(domain, cloudflare_token),
            ]
            
            all_steps_succeeded = True
            for step_func in steps:
                time.sleep(0.5)
                success, message = step_func()
                full_log_text += message + "\n"
                log_placeholder.code(full_log_text, language="log")
                if not success:
                    full_log_text += f"🔥🔥 PROSES UNTUK {domain} DIHENTIKAN KARENA ERROR 🔥🔥\n"
                    log_placeholder.code(full_log_text, language="log")
                    all_steps_succeeded = False
                    break
            
            if all_steps_succeeded:
                full_log_text += f"✅✅ DEPLOYMENT UNTUK {domain} SELESAI DENGAN SUKSES ✅✅\n"
                log_placeholder.code(full_log_text, language="log")

        st.success("🎉🎉 Seluruh proses deployment telah selesai! 🎉🎉")
        st.balloons()