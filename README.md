# 📅 Kalender Kelas XI RPL

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](#lisensi)
[![Live Demo](https://img.shields.io/badge/demo-Netlify-00C7B7.svg)](https://kalender-rpl.netlify.app/)

Kalender Kelas XI RPL adalah aplikasi web responsif untuk membantu siswa memantau kalender, tugas pribadi, jadwal pelajaran, acara mendatang, dan pengingat kelas dalam satu halaman. Data bersama disinkronkan secara real-time melalui Firebase, sedangkan tugas pribadi tersimpan secara lokal pada browser pengguna.

🌐 **Live Demo:** [kalender-rpl.netlify.app](https://kalender-rpl.netlify.app/)

![Tampilan Kalender Kelas](assets/jadwal_kelas.png)

## ✨ Fitur Utama

- Kalender bulanan interaktif dengan navigasi bulan.
- Penanda hari libur nasional dan cuti bersama Indonesia tahun 2026.
- Penambahan dan penghapusan tugas pribadi berdasarkan tanggal.
- Penyimpanan lokal yang terisolasi per akun dan sinkronisasi data pribadi ke Firestore.
- Rundown harian berbasis waktu, detail aktivitas, dan checklist penyelesaian.
- Progress harian, poin, streak hari sempurna, dan animasi apresiasi saat rundown tuntas.
- Daftar acara mendatang yang diperbarui secara real-time.
- Jadwal pelajaran harian berdasarkan hari aktif.
- Pengingat umum untuk seluruh siswa.
- Autentikasi admin untuk mengelola acara, jadwal, dan pengingat.
- Antarmuka responsif untuk desktop dan perangkat mobile.

## 🛠️ Tech Stack

| Teknologi | Kegunaan |
| --- | --- |
| HTML5 | Struktur aplikasi |
| Tailwind CSS (CDN) | Styling dan desain responsif |
| JavaScript ES Modules | Logika aplikasi dan interaksi UI |
| Firebase Authentication | Autentikasi admin |
| Cloud Firestore | Penyimpanan dan sinkronisasi data bersama |
| Google Fonts | Font antarmuka (`Inter`) |
| Browser Local Storage | Penyimpanan tugas pribadi dan rundown harian |

## 📋 Prasyarat

Pastikan perangkat telah memiliki:

- Browser modern, seperti Chrome, Edge, atau Firefox.
- Koneksi internet untuk memuat Tailwind CSS, Google Fonts, dan Firebase SDK dari CDN.
- Salah satu server HTTP lokal:
  - Python 3.9+; atau
  - ekstensi **Live Server** untuk Visual Studio Code.
- Project Firebase dengan **Authentication** dan **Cloud Firestore** aktif jika menggunakan backend sendiri.

Tidak diperlukan Node.js maupun proses instalasi dependency karena seluruh dependency frontend dimuat melalui CDN.

## 🚀 Instalasi & Setup

1. Clone repository dan masuk ke direktori proyek:

   ```bash
   git clone https://github.com/Psr354/kalender-kelas-xi-rpl.git
   cd kalender-kelas-xi-rpl
   ```

2. Konfigurasikan Firebase pada objek `firebaseConfig` di `index.html`:

   ```js
   const firebaseConfig = {
     apiKey: "YOUR_API_KEY",
     authDomain: "YOUR_PROJECT.firebaseapp.com",
     projectId: "YOUR_PROJECT_ID",
     storageBucket: "YOUR_PROJECT.firebasestorage.app",
     messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
     appId: "YOUR_APP_ID",
   };
   ```

3. Aktifkan provider **Email/Password** melalui Firebase Console:

   ```text
   Firebase Console → Authentication → Sign-in method → Email/Password
   ```

4. Buat database **Cloud Firestore** dan siapkan koleksi berikut:

   ```text
   events
   schedule
   announcements
   userData
   ```

5. Buat dokumen allowlist `admins/{uid}` untuk setiap akun pengelola dari Firebase Console atau lingkungan server tepercaya. Isi dokumen boleh berupa metadata sederhana, misalnya:

   ```json
   { "role": "admin" }
   ```

   Security Rules menolak perubahan koleksi `admins` dari aplikasi, sehingga pengguna tidak dapat menjadikan dirinya sendiri sebagai admin.

6. Terapkan [firestore.rules](firestore.rules) ke project Firebase:

   ```bash
   firebase deploy --only firestore:rules
   ```

7. Jalankan aplikasi menggunakan server HTTP lokal:

   ```bash
   python -m http.server 8000
   ```

8. Buka `http://localhost:8000` pada browser.

> [!IMPORTANT]
> Terapkan Firestore Security Rules yang hanya mengizinkan pengguna terautentikasi untuk menulis data. Konfigurasi Firebase pada frontend bukan secret; keamanan data tetap bergantung pada Authentication dan Security Rules.

## 💡 Cara Penggunaan

### Pengguna

1. Gunakan tombol `<` dan `>` untuk berpindah bulan.
2. Klik **Tambah Tugas** atau **+ tugas** pada tanggal tertentu.
3. Isi tanggal dan nama tugas, lalu klik **Simpan Tugas**.
4. Pilih tanggal pada bagian **Rundown satu hari penuh**.
5. Isi jam mulai, jam selesai, aktivitas, dan detailnya, lalu tambahkan ke rundown.
6. Centang aktivitas yang selesai untuk memperoleh poin dan membangun streak.
7. Lihat acara, jadwal hari ini, hari libur, dan pengingat kelas pada halaman utama.

Tanpa login, tugas, rundown, dan catatan tersimpan dalam ruang lokal tamu. Setelah login, data disimpan dalam ruang lokal khusus UID pengguna dan disinkronkan ke dokumen `userData/{uid}`. Saat akun masih kosong, data lokal tamu yang sudah ada otomatis dipindahkan ke akun agar dapat muncul di perangkat lain. Data akun berbeda tidak digabungkan satu sama lain.

### Admin

1. Pastikan UID akun telah terdaftar sebagai dokumen dalam koleksi `admins`.
2. Klik tombol login di kanan bawah halaman dan masuk menggunakan akun Firebase Authentication.
3. Gunakan tombol **Edit** untuk mengelola acara, jadwal pelajaran, dan pengingat umum.

## 📁 Struktur Folder

```text
kalender-kelas-xi-rpl/
├── assets/
│   ├── jadwal_kelas.png
│   └── logo_patpul.png
├── index.html
└── README.md
```

## 🤝 Cara Berkontribusi

1. Fork repository ini.
2. Buat branch fitur baru:

   ```bash
   git checkout -b feature/nama-fitur
   ```

3. Lakukan perubahan dan pastikan aplikasi berjalan dengan baik.
4. Commit perubahan menggunakan pesan yang jelas:

   ```bash
   git commit -m "feat: tambahkan nama fitur"
   ```

5. Push branch dan buka Pull Request:

   ```bash
   git push origin feature/nama-fitur
   ```

Saat berkontribusi, pertahankan tampilan responsif, hindari memasukkan kredensial admin, dan uji perubahan pada browser desktop serta mobile.

## 📄 Lisensi

Proyek ini tersedia di bawah [MIT License](LICENSE). Tambahkan file `LICENSE` sebelum mendistribusikan proyek.

## 📬 Kontak

Untuk pertanyaan, laporan bug, atau usulan fitur, silakan:

- Mengunjungi profil GitHub [Psr354](https://github.com/Psr354).
- Membuka [GitHub Issue](https://github.com/Psr354/kalender-kelas-xi-rpl/issues).
- Mengakses aplikasi melalui [kalender-rpl.netlify.app](https://kalender-rpl.netlify.app/).
- Menghubungi maintainer melalui email: `azzamazhimmuntazhar@gmail.com`.

---

<p align="center">Dibuat untuk mendukung kegiatan belajar Kelas XI RPL SMKN 40 Jakarta.</p>
