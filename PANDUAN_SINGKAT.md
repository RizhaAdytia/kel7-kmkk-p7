# 🚀 Panduan Singkat: Menggunakan SAW & PROMETHEE II

## ⚡ Quick Start (5 Menit)

### 1. Setup Awal
```bash
# Aktivakan virtual environment
source .venv/bin/activate  # Linux/Mac
# atau
.venv\Scripts\activate  # Windows

# Jalankan aplikasi
python app.py
```

Buka browser: `http://localhost:5000`

### 2. Buat Proyek Baru
- Klik **"Mulai Proyek Baru"**
- Masukkan nama proyek: "Pemilihan Supplier"
- Klik **"Buat Proyek"**

### 3. Tambah Kriteria (Contoh)
- Klik **"Tambah Kriteria"**
- Masukkan:
  - Harga
  - Kualitas
  - Waktu Pengiriman
  - Reputasi
- Klik **"Simpan"**

### 4. Tambah Alternatif (Contoh)
- Klik **"Tambah Alternatif"**
- Masukkan:
  - Supplier A
  - Supplier B
  - Supplier C
- Klik **"Simpan"**

### 5. Input Perbandingan
- Klik **"Bandingkan Kriteria"**
- Bandingkan setiap pasang kriteria (1-9 scale)
- Lakukan **"Bandingkan Alternatif"** untuk setiap kriteria

---

## 📊 Menggunakan SAW

### Langkah 1: Buka SAW Input
Dari detail proyek, klik tombol **"SAW"** (warna cyan)

### Langkah 2: Tentukan Tipe & Bobot
Untuk setiap kriteria:

| Kriteria | Tipe | Bobot | Penjelasan |
|----------|------|-------|-----------|
| Harga | **Cost (↓)** | 3 | Semakin rendah semakin baik |
| Kualitas | **Benefit (↑)** | 4 | Semakin tinggi semakin baik |
| Pengiriman | **Cost (↓)** | 2 | Cepat lebih baik |
| Reputasi | **Benefit (↑)** | 3 | Bagus lebih baik |

### Langkah 3: Lihat Hasil
- **Ranking:** Urutan alternatif terbaik
- **Skor:** Nilai 0-1 untuk setiap alternatif
- **Matriks:** Lihat detail kalkulasi

---

## 📋 Menggunakan PROMETHEE II

### Langkah 1: Buka PROMETHEE Input
Dari detail proyek, klik tombol **"PROMETHEE II"** (warna orange)

### Langkah 2: Tentukan Parameter

| Kriteria | Tipe | Bobot | p (Pref) | q (Acuh) |
|----------|------|-------|----------|----------|
| Harga | Cost | 3 | 10 | 5 |
| Kualitas | Benefit | 4 | 2 | 0.5 |
| Pengiriman | Cost | 2 | 2 | 1 |
| Reputasi | Benefit | 3 | 2 | 0.5 |

**Panduan Threshold:**
- **p:** Tingkat pada mana perbedaan dianggap signifikan
- **q:** Tingkat di mana perbedaan dianggap tidak penting
- **Aturan:** q ≤ p (harus!)

### Langkah 3: Lihat Hasil
- **Φ+ (Leaving Flow):** Kekuatan (naik = baik)
- **Φ- (Entering Flow):** Kelemahan (turun = baik)
- **Φ Net (Net Flow):** Skor akhir

---

## 🔄 Bandingkan SAW vs PROMETHEE

Dari detail proyek, klik **"Perbandingan"** untuk:
- Lihat ranking kedua metode
- Cek konsistensi hasil
- Analisis perbedaan

---

## 💡 Tips & Trik

### Untuk SAW:
✅ **Tipe Kriteria penting!**
- Benefit: Harga, Kualitas, Kepuasan
- Cost: Biaya, Waktu, Risiko

✅ **Bobot lebih besar = lebih penting**
- Jangan gunakan 0 atau nilai negatif
- Gunakan: 1, 2, 3, 4, 5

### Untuk PROMETHEE:
✅ **Parameter threshold kritis!**
- Terlalu kecil → terlalu sensitif
- Terlalu besar → hasil tidak jelas
- Mulai dengan p=range/3, q=range/6

✅ **Gunakan data yang masuk akal**
- Jangan semua nilai sama
- Pastikan ada perbedaan antar alternatif

---

## 📱 Navigasi Cepat

```
Beranda (/)
    ↓
Buat Proyek Baru
    ↓
Detail Proyek
├─ Tambah Kriteria
├─ Tambah Alternatif
├─ Bandingkan Kriteria (AHP)
├─ Bandingkan Alternatif (AHP)
└─ Metode Analisis:
    ├─ AHP (Hasil)
    ├─ MPE (Hasil)
    ├─ Bayes (Hasil)
    ├─ CPI (Hasil)
    ├─ SAW ★ NEW
    ├─ PROMETHEE II ★ NEW
    └─ Perbandingan ★ NEW
```

---

## ❓ FAQ

**Q: Apa bedanya SAW dan PROMETHEE?**
A: SAW lebih sederhana (linear), PROMETHEE lebih kompleks (outranking). Gunakan keduanya untuk validasi.

**Q: Hasil berbeda, mana yang benar?**
A: Keduanya bisa benar! Diskusikan dengan stakeholder. PROMETHEE lebih sophisticated untuk masalah kompleks.

**Q: Berapa minimal kriteria/alternatif?**
A: Minimum 2 kriteria dan 2 alternatif. Optimal: 3-5 kriteria dan 3-10 alternatif.

**Q: Bisa ganti bobot tanpa ulang dari awal?**
A: Ya! Klik SAW/PROMETHEE lagi, ubah bobot, langsung lihat hasil baru.

**Q: Gimana cara export hasil?**
A: Untuk saat ini silakan screenshot atau copy-paste. Export feature akan ditambah di versi berikutnya.

---

## 🐛 Troubleshooting Cepat

| Masalah | Solusi |
|---------|--------|
| Tombol SAW/PROMETHEE tidak muncul | Tambah kriteria dan alternatif dulu |
| Error "nilai NaN" | Lakukan pairwise comparison untuk alternatif |
| Hasil semua sama | Ubah bobot dengan perbedaan lebih besar |
| p < q di PROMETHEE | Auto-fix: sistem akan samakan q dengan p |

---

## 📚 Dokumentasi Lengkap

Lihat file: **IMPLEMENTASI_SAW_PROMETHEE.md** untuk:
- Detail model matematika
- Penjelasan parameter
- Contoh kasus lengkap
- Troubleshooting mendalam

---

## ✈️ Selamat Mencoba!

Jika ada pertanyaan atau masalah, hubungi tim pengembang atau buka issue di system tracker.

**Versi:** 1.0 ✓
**Last Updated:** 2024
**Status:** Ready for Production ✓
