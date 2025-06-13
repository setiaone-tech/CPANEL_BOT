# 🤖 CPANEL BOT - Layanan Otomatisasi untuk Developer

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-ff4b4b.svg?logo=streamlit)
![Vercel](https://img.shields.io/badge/Vercel-Deployed-black.svg?logo=vercel)

CPANEL BOT adalah sebuah aplikasi web publik yang dibangun dengan Streamlit, dirancang untuk membantu siapa saja mengotomatiskan tugas-tugas repetitif yang berhubungan dengan manajemen cPanel, Cloudflare, dan Namecheap.

Aplikasi ini menyediakan antarmuka yang ramah pengguna untuk menjalankan proses-proses kompleks, memungkinkan Anda menggunakan kredensial Anda sendiri dengan aman untuk setiap sesi.

## ✨ Fitur Utama

Aplikasi ini berisi kumpulan _tools_ yang siap pakai untuk umum:

- **⚙️ cPanel Subdomain Creator**: Membuat subdomain secara massal di akun cPanel Anda.
- **🔑 cPanel FTP Account Creator**: Membuat akun FTP baru untuk setiap domain dalam daftar Anda.
- **🚀 Full Deployment Orchestrator**: Alur kerja deployment lengkap, mulai dari `git clone`, update file `.env`, migrasi database, hingga pengaturan SSL.
- **☁️ Cloudflare Mass DNS Updater**: Memperbarui A Record untuk banyak domain di akun Cloudflare Anda.
- **✍️ cPanel Specific File Updater**: Meng-upload atau menimpa file spesifik di akun cPanel Anda.
- **🌐 Onboard to Cloudflare**: Mengotomatiskan proses penambahan domain dari Namecheap ke Cloudflare.

## 📸 Tampilan Aplikasi

_(**Tips**: Ganti gambar di bawah dengan screenshot aplikasi Anda yang sudah berjalan!)_

![Screenshot Aplikasi CPANEL BOT](https://i.imgur.com/8aVJHjH.png)

## 🛡️ Arsitektur & Keamanan

Proyek ini dirancang sebagai **layanan publik** dengan prioritas pada keamanan dan privasi pengguna.

- **Tanpa Penyimpanan Kredensial**: Aplikasi ini **TIDAK MENYIMPAN** kredensial Anda di database atau server kami.
- **Memori Sesi**: Kredensial yang Anda masukkan hanya disimpan sementara di memori sesi browser Anda (`st.session_state`). Data ini akan **otomatis terhapus** saat Anda menutup tab atau me-refresh halaman.
- **Transparansi Open Source**: Seluruh kode sumber aplikasi ini terbuka (open source) di GitHub. Anda bisa memeriksa dan mengaudit kode kami untuk memastikan tidak ada penyalahgunaan data.

## 🛠️ Teknologi yang Digunakan

- **Python**: Bahasa pemrograman utama.
- **Streamlit**: Framework untuk membangun antarmuka web interaktif.
- **Requests**: Library untuk melakukan panggilan API ke cPanel, Cloudflare, dll.
- **Fabric**: Library untuk menjalankan perintah SSH secara terprogram.
- **Vercel**: Platform untuk men-deploy aplikasi.

---

## 🚀 Instalasi & Setup

Ikuti langkah-langkah ini jika Anda ingin menjalankan salinan aplikasi ini sendiri, baik secara lokal maupun di Vercel.

### 1. Setup Lokal

1.  **Clone Repository Ini**

    ```bash
    git clone [https://github.com/setiaone-tech/CPANEL_BOT.git](https://github.com/setiaone-tech/CPANEL_BOT.git)
    cd CPANEL_BOT
    ```

2.  **Buat dan Aktifkan Virtual Environment**

    ```bash
    # Untuk MacOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # Untuk Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Semua Kebutuhan**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Jalankan Aplikasi**
    ```bash
    streamlit run 🤖_Home.py
    ```
    Aplikasi akan terbuka di browser Anda. Tidak ada konfigurasi kredensial yang diperlukan sebelum menjalankan. Semua input akan diminta melalui antarmuka web.

### 2. Deploy ke Vercel

1.  Upload proyek ini ke repository **PRIVATE** atau **PUBLIC** di GitHub Anda.
2.  Login ke [Vercel](https://vercel.com/) menggunakan akun GitHub.
3.  Klik "Add New..." -> "Project", lalu import repository Anda.
4.  Vercel akan otomatis mendeteksi ini sebagai aplikasi Streamlit.
5.  **Tidak Perlu Konfigurasi**: Anda **tidak perlu** mengatur Environment Variables apa pun untuk kredensial. Cukup klik **"Deploy"**.

---

## 👨‍💻 Cara Penggunaan (Untuk Pengguna Web)

1.  **Buka Aplikasi**: Akses URL web aplikasi CPANEL BOT.
2.  **Pilih Tool**: Gunakan menu navigasi di sidebar untuk memilih tool yang Anda butuhkan.
3.  **Masukkan Kredensial Anda**: Di halaman tool, akan ada formulir untuk Anda memasukkan kredensial Anda sendiri (misal: API Token Cloudflare, password cPanel, dll).
4.  **Konfigurasi & Jalankan**: Isi parameter lain yang diperlukan (seperti daftar domain) dan klik tombol eksekusi.
5.  **Selesai**: Proses akan berjalan menggunakan kredensial yang Anda berikan. Setelah selesai, Anda bisa menutup halaman. Kredensial Anda akan otomatis hilang dari sesi.

## Disclaimer

Aplikasi ini disediakan "sebagaimana adanya". Anda bertanggung jawab penuh atas kredensial yang Anda masukkan dan tindakan yang dilakukan oleh tool ini pada akun Anda. Kami mendorong Anda untuk meninjau kode sumber untuk memverifikasi keamanannya.
