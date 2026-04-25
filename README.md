# Decision-System7
Decision Support System - Sistem Penunjang Keputusan Terintegrasi

Sistem Penunjang Keputusan multi-metode menggunakan Python Flask dengan 6 metode pengambilan keputusan yang komprehensif.

## 🎯 Fitur Utama

### Metode Pengambilan Keputusan:
1. **AHP** (Analytic Hierarchy Process) - Classic pairwise comparison
2. **MPE** (Metode Perbandingan Eksponensial) - Exponential weighting
3. **Bayes** (Teorema Bayes) - Probability-based approach
4. **CPI** (Composite Performance Index) - Multiple aggregation methods
5. **SAW** ⭐ NEW - Simple Additive Weighting (normalized)
6. **PROMETHEE II** ⭐ NEW - Preference ranking with outranking

### Fitur Dasar:
- ✅ Buat dan kelola proyek keputusan
- ✅ Tambah kriteria (Benefit/Cost) dan alternatif
- ✅ Pairwise comparisons untuk data input
- ✅ Hitung bobot dan ranking dengan multiple methods
- ✅ Bandingkan hasil antar metode
- ✅ Visualisasi ranking dan flows
- ✅ Input validasi dan error handling
- ✅ Persistence data ke database

## 📦 Instalasi

### Requirement:
- Python 3.7+
- Flask
- SQLAlchemy
- NumPy
- SciPy

### Setup:
```bash
# 1. Clone atau download project
cd "path/to/Model Keputusan Berbasis AHP"

# 2. Buat virtual environment (jika belum ada)
python -m venv .venv

# 3. Aktivasi virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Jalankan aplikasi
python app.py
```

Aplikasi akan berjalan di: **http://localhost:5000**

## 🚀 Penggunaan Cepat

### Workflow Dasar:
1. **Buka http://localhost:5000**
2. **Klik "Mulai Proyek Baru"** → Masukkan nama proyek
3. **Tambah Kriteria** → Min. 2 kriteria (misal: Harga, Kualitas)
4. **Tambah Alternatif** → Min. 2 alternatif (misal: Supplier A, B, C)
5. **Bandingkan Kriteria** → Pairwise comparison (AHP)
6. **Bandingkan Alternatif** → Untuk setiap kriteria
7. **Pilih Metode Analisis:**
   - Klik **"Hasil AHP"** untuk hasil AHP
   - Klik **"SAW"** untuk hasil SAW
   - Klik **"PROMETHEE II"** untuk hasil PROMETHEE
   - Klik **"Perbandingan"** untuk bandingkan SAW vs PROMETHEE
8. **Lihat Hasil Ranking**

### Contoh Kasus: Pemilihan Supplier

**Setup:**
- Kriteria: Harga (Cost), Kualitas (Benefit), Waktu Pengiriman (Cost), Reputasi (Benefit)
- Alternatif: Supplier A, Supplier B, Supplier C

**Langkah SAW:**
1. Dari project detail → Klik **"SAW"**
2. Tentukan tipe & bobot:
   - Harga: Cost, w=2
   - Kualitas: Benefit, w=3
   - Waktu: Cost, w=2
   - Reputasi: Benefit, w=2
3. Klik **"Lanjut ke Hasil SAW"**
4. Lihat ranking dan skor

**Langkah PROMETHEE:**
1. Dari project detail → Klik **"PROMETHEE II"**
2. Tentukan tipe, bobot, dan threshold (p, q)
3. Klik **"Hitung PROMETHEE II"**
4. Lihat ranking berdasarkan Net Flow (Φ)

**Bandingkan:**
1. Dari project detail → Klik **"Perbandingan"**
2. Lihat ranking kedua metode side-by-side
3. Analisa konsistensi hasil

## 📚 Dokumentasi

Untuk detail lengkap, lihat file dokumentasi berikut:

- **PANDUAN_SINGKAT.md** - Quick start guide (5 menit)
  - Langkah-langkah cepat
  - Tips & trik
  - FAQ

- **IMPLEMENTASI_SAW_PROMETHEE.md** - Dokumentasi teknis lengkap (600+ lines)
  - Model matematika SAW & PROMETHEE
  - Penjelasan setiap route
  - Contoh kasus lengkap
  - Troubleshooting guide

- **RINGKASAN_IMPLEMENTASI.md** - Ringkasan perubahan kode
  - File structure
  - Modifikasi detail
  - Testing checklist

- **DATABASE_SCHEMA.sql** - Query contoh database
  - Schema DDL
  - Index definitions
  - Sample queries

- **VERIFICATION_CHECKLIST.md** - Checklist instalasi & testing
  - Step-by-step verification
  - Functional testing
  - Error handling tests

## 🔧 Teknologi Stack

```
Frontend:  Flask + Jinja2 + Bootstrap 5 + JavaScript
Backend:   Python + SQLAlchemy ORM
Database:  SQLite (ahp.db)
Math:      NumPy + SciPy
```

## 📊 Perbandingan Metode

| Aspek | SAW | PROMETHEE II |
|-------|-----|--------------|
| Kompleksitas | Sederhana | Kompleks |
| Kecepatan | Sangat cepat | Cepat |
| Normalisasi | Benefit/Cost | Linear preference function |
| Output | Single score | Flows + ranking |
| Cocok untuk | Simple decisions | Complex decisions |
| Threshold | Tidak ada | p, q parameters |

## 🌐 Deploy Online

Project ini dapat di-deploy ke platform seperti Render.com atau Railway.app.

### Deploy ke Render.com:
1. Push code ke GitHub
2. Buat akun di https://render.com
3. Click "New+" → "Web Service"
4. Connect GitHub repository
5. Set Environment:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
6. Click "Create Web Service"
7. Tunggu deployment selesai

### Deploy ke Railway:
1. Push code ke GitHub
2. Buat akun di https://railway.app
3. Import GitHub repository
4. Railway otomatis detect Python & setup
5. Deploy selesai!

## 🧪 Testing

Semua fitur telah ditest dengan:
- ✅ Unit testing untuk kalkulasi SAW & PROMETHEE
- ✅ Integration testing untuk database & routes
- ✅ UI/UX testing untuk responsiveness
- ✅ Performance testing (sampai 100 criteria × 50 alternatives)
- ✅ Backward compatibility testing dengan existing data

## 🐛 Troubleshooting

### Error: "couldn't connect to server"
- Pastikan virtual environment activated
- Pastikan port 5000 tidak digunakan aplikasi lain

### Error: "table doesn't exist"
- Delete `instance/ahp.db`
- Run `python app.py` (akan auto-recreate database)

### SAW/PROMETHEE button tidak muncul
- Pastikan ada minimal 2 kriteria dan 2 alternatif

Untuk detail troubleshooting lengkap, lihat IMPLEMENTASI_SAW_PROMETHEE.md section Troubleshooting.

## 📦 Struktur File Penting

```
├── app.py                           - Main Flask application + models
├── methods.py                        - SAW, PROMETHEE, MPE, Bayes, CPI classes
├── requirements.txt                  - Python dependencies
├── README.md                         - File ini
├── PANDUAN_SINGKAT.md               - Quick start guide
├── IMPLEMENTASI_SAW_PROMETHEE.md    - Complete documentation
├── RINGKASAN_IMPLEMENTASI.md        - Implementation summary
├── DATABASE_SCHEMA.sql              - Database schema docs
├── VERIFICATION_CHECKLIST.md        - Installation verification
├── templates/
│   ├── base.html                    - Base template
│   ├── project_detail.html          - Project management (NEW: SAW/PROMETHEE buttons)
│   ├── saw_input.html               - SAW input form (NEW)
│   ├── saw_results.html             - SAW results (NEW)
│   ├── promethee_input.html         - PROMETHEE input form (NEW)
│   ├── promethee_results.html       - PROMETHEE results (NEW)
│   ├── comparison_results.html      - Method comparison (NEW)
│   └── ... (other templates)
└── instance/
    └── ahp.db                       - SQLite database
```

## 👨‍💻 Tim Pengembang

**Group 7 - Decision Support System**
- Muhammad Dava Kayla Kalam Perdana (065123002)
- Rizha Adytia (065123004)
- Bagas Arya Putra Sofyan (065123014)

**Institusi:** Universitas Pakuan
**Program Studi:** Ilmu Komputer (Computer Science)
**Mata Kuliah:** Sistem Penunjang Keputusan

## 📝 Changelog

### Version 1.0 (Current)
- ✅ Added SAW (Simple Additive Weighting) method
- ✅ Added PROMETHEE II (Preference Ranking method)
- ✅ Added CriterionType & PrometheeParameter models
- ✅ Added 5 new routes
- ✅ Added 5 new template files
- ✅ Added comprehensive documentation
- ✅ Full backward compatibility
- ✅ Production ready

## 📄 License

Educational Project - Universitas Pakuan

## 🔗 Links

- **GitHub**: [Repo Link if available]
- **Documentation**: See markdown files in project root
- **Demo**: Run `python app.py` and visit http://localhost:5000

---

**Version:** 5.0  
**Last Updated:** 2026  
**Status:** ✅ Production Ready  
**Next Version:** Features optimization & UI enhancements planned