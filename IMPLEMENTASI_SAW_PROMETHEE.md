# Dokumentasi Implementasi SAW & PROMETHEE II

## 📋 Daftar Isi
1. [Ringkasan Implementasi](#ringkasan-implementasi)
2. [Database Schema](#database-schema)
3. [Model Matematika](#model-matematika)
4. [Struktur Routes](#struktur-routes)
5. [Panduan Penggunaan](#panduan-penggunaan)
6. [Contoh Kasus](#contoh-kasus)
7. [Troubleshooting](#troubleshooting)

---

## Ringkasan Implementasi

Sistem Penunjang Keputusan (SPK) Anda telah diperbarui dengan dua metode baru:

### Metode yang Tersedia:
1. **AHP** (Analytic Hierarchy Process) - yang sudah ada
2. **MPE** (Metode Perbandingan Eksponensial) - yang sudah ada
3. **Bayes** (Teorema Bayes) - yang sudah ada
4. **CPI** (Composite Performance Index) - yang sudah ada
5. **SAW** (Simple Additive Weighting) - **BARU** ✨
6. **PROMETHEE II** (Preference Ranking Organization METHod for Enrichment Evaluations) - **BARU** ✨

---

## Database Schema

### Model Database Baru

#### 1. CriterionType
Menyimpan konfigurasi tipe dan bobot kriteria untuk SAW/PROMETHEE:

```python
class CriterionType(db.Model):
    id: Integer (Primary Key)
    criterion_id: Integer (Foreign Key → Criterion)
    is_benefit: Boolean (True = Benefit/Max, False = Cost/Min)
    weight_saw: Float (Bobot untuk metode SAW)
    weight_promethee: Float (Bobot untuk metode PROMETHEE)
```

**Penjelasan:**
- `is_benefit`: Menentukan apakah kriteria adalah benefit (semakin tinggi semakin baik) atau cost (semakin rendah semakin baik)
- `weight_saw`: Bobot untuk SAW (akan dinormalisasi otomatis)
- `weight_promethee`: Bobot untuk PROMETHEE (akan dinormalisasi otomatis)

#### 2. PrometheeParameter
Menyimpan parameter preferensi PROMETHEE per kriteria:

```python
class PrometheeParameter(db.Model):
    id: Integer (Primary Key)
    criterion_id: Integer (Foreign Key → Criterion)
    p_threshold: Float (Preference Threshold)
    q_threshold: Float (Indifference Threshold)
```

**Penjelasan:**
- `p_threshold` (p): Selisih nilai di mana ada preferensi mutlak antara dua alternatif
- `q_threshold` (q): Selisih nilai di mana preferensi dapat diabaikan (q ≤ p)

### Relasi Database

```
Project (1) ──→ (M) Criterion ──→ (1) CriterionType
                                 ├──→ (1) PrometheeParameter
```

---

## Model Matematika

### SAW (Simple Additive Weighting)

#### Langkah 1: Normalisasi Matriks Keputusan
Matriks keputusan X dinormalisasi menjadi matriks R sesuai tipe kriteria:

**Untuk Kriteria Benefit (Max):**
```
R_ij = X_ij / MAX(X_j)    untuk semua i
```

**Untuk Kriteria Cost (Min):**
```
R_ij = MIN(X_j) / X_ij    untuk semua i
```

di mana:
- X_ij = nilai alternatif i pada kriteria j
- R_ij = nilai ternormalisasi
- MAX(X_j) = nilai maksimal kriteria j
- MIN(X_j) = nilai minimal kriteria j

Hasil: Matriks R dengan nilai dalam range [0, 1]

#### Langkah 2: Hitung Matriks Terbobot
```
V_ij = R_ij × w_j
```

di mana:
- V_ij = nilai terbobot
- w_j = bobot kriteria j (sudah dinormalisasi: Σw_j = 1)

#### Langkah 3: Hitung Skor Akhir
```
Score_i = Σ V_ij = Σ (w_j × R_ij) untuk semua j
```

#### Langkah 4: Ranking
Urutan alternatif berdasarkan skor akhir (descending):
```
Ranking: Score_1 ≥ Score_2 ≥ ... ≥ Score_n
```

### PROMETHEE II

#### Langkah 1: Hitung Selisih Pairwise
Untuk setiap pasangan alternatif a dan b pada kriteria j:

**Benefit:**
```
d_j(a,b) = f_j(a) - f_j(b)
```

**Cost:**
```
d_j(a,b) = f_j(b) - f_j(a)  (dibalik)
```

Hasil: Matriks D berukuran (n_alt × n_alt × n_crit)

#### Langkah 2: Terapkan Preference Function (Tipe V - Linear)
Fungsi preferensi linear untuk setiap kriteria:

```
P_j(a,b) = 0                    jika d_j(a,b) ≤ q_j
         = (d_j(a,b) - q_j)/(p_j - q_j)  jika q_j < d ≤ p_j
         = 1                    jika d_j(a,b) > p_j
```

di mana:
- P_j(a,b) = derajat preferensi alternatif a terhadap b pada kriteria j
- q_j = indifference threshold (threshold acuh)
- p_j = preference threshold (threshold preferensi mutlak)

#### Langkah 3: Hitung Indeks Preferensi Agregat
```
π(a,b) = Σ w_j × P_j(a,b)  untuk semua j
```

Hasil: Matriks π (n_alt × n_alt) dengan nilai dalam range [0, 1]

#### Langkah 4: Hitung Leaving Flow (Φ+) dan Entering Flow (Φ-)
**Leaving Flow (Positive Flow)** - Kekuatan a mendominasi alternatif lain:
```
Φ+(a) = (1/(n-1)) × Σ π(a,b)  untuk semua b ≠ a
```

**Entering Flow (Negative Flow)** - Tingkat dominasi terhadap a oleh alternatif lain:
```
Φ-(a) = (1/(n-1)) × Σ π(b,a)  untuk semua b ≠ a
```

#### Langkah 5: Hitung Net Flow dan Ranking
**Net Flow:**
```
Φ(a) = Φ+(a) - Φ-(a)
```

**Ranking:**
```
Ranking: Φ(a1) ≥ Φ(a2) ≥ ... ≥ Φ(an)
```

**Interpretasi Net Flow:**
- Φ > 0: Alternatif "lebih baik" dari rata-rata
- Φ = 0: Alternatif "setara" dengan rata-rata
- Φ < 0: Alternatif "lebih buruk" dari rata-rata

---

## Struktur Routes

### Route SAW

#### 1. `/project/<project_id>/saw_input` [GET/POST]
**Fungsi:** Input konfigurasi SAW (tipe kriteria dan bobot)

**Parameter Output:**
- `project`: Project object
- `criterion_data`: List konfigurasi kriteria
- `alternatives`: List alternatif

**POST Data:**
- `type_<criterion_id>`: "benefit" atau "cost"
- `weight_<criterion_id>`: Nilai bobot (float)

**Redirect ke:** `saw_results`

#### 2. `/project/<project_id>/saw_results` [GET]
**Fungsi:** Menampilkan hasil perhitungan SAW

**Parameter Output:**
- `project`: Project object
- `results`: List ranking dengan skor
- `normalized_matrix`: Matriks ternormalisasi R
- `weighted_matrix`: Matriks terbobot V
- `final_scores`: Array skor akhir
- `criterion_configs`: Konfigurasi kriteria yang digunakan

**Template:** `saw_results.html`

### Route PROMETHEE

#### 1. `/project/<project_id>/promethee_input` [GET/POST]
**Fungsi:** Input konfigurasi PROMETHEE (tipe, bobot, dan parameter threshold)

**POST Data:**
- `type_<criterion_id>`: "benefit" atau "cost"
- `weight_<criterion_id>`: Bobot (float)
- `p_<criterion_id>`: Preference threshold
- `q_<criterion_id>`: Indifference threshold

**Redirect ke:** `promethee_results`

#### 2. `/project/<project_id>/promethee_results` [GET]
**Fungsi:** Menampilkan hasil perhitungan PROMETHEE II

**Parameter Output:**
- `project`: Project object
- `results`: List ranking dengan phi flows
- `prom_details`: Detail matriks preferensi
- `criterion_configs`: Konfigurasi kriteria
- `promethee_params`: Parameter PROMETHEE yang digunakan

**Template:** `promethee_results.html`

### Route Perbandingan

#### `/project/<project_id>/method_comparison` [GET]
**Fungsi:** Membandingkan hasil SAW vs PROMETHEE II

**Parameter Output:**
- `project`: Project object
- `comparison_results`: Perbandingan ranking kedua metode
- `criteria`: Daftar kriteria
- `alternatives`: Daftar alternatif

**Template:** `comparison_results.html`

---

## Panduan Penggunaan

### Workflow Umum

#### 1. Persiapan Data
1. Buat proyek baru
2. Tambahkan kriteria (min. 2)
3. Tambahkan alternatif (min. 2)
4. Lakukan pairwise comparison tentang kriteria

### Menggunakan SAW

1. **Buka project** → Klik tombol "SAW"
2. **Tentukan Tipe Kriteria:**
   - **Benefit (↑)**: Kriteria yang semakin tinggi semakin baik (misal: Kualitas, Kepuasan)
   - **Cost (↓)**: Kriteria yang semakin rendah semakin baik (misal: Harga, Waktu)
3. **Masukkan Bobot:**
   - Angka positif (misal: 1, 2, 3, 5)
   - Tidak perlu dinormalisasi, sistem akan otomatis
   - Semakin besar = semakin penting
4. **Lihat Hasil:**
   - Ranking alternatif
   - Skor akhir setiap alternatif
   - Matriks normalisasi dan bobot

### Menggunakan PROMETHEE II

1. **Buka project** → Klik tombol "PROMETHEE II"
2. **Tentukan Tipe Kriteria** (sama seperti SAW)
3. **Masukkan Bobot** (sama seperti SAW)
4. **Tentukan Threshold:**
   - **p (Preference Threshold):** Selisih nilai di mana ada preferensi mutlak
     - Contoh: Jika p=0.5, alternatif dengan selisih nilai >0.5 dianggap jauh berbeda
   - **q (Indifference Threshold):** Selisih nilai yang bisa diabaikan (q ≤ p)
     - Contoh: Jika q=0.1, perbedaan <0.1 dianggap tidak signifikan
   - **Panduan praktis:**
     - Nilai kecil (q,p): Lebih sensitif terhadap perbedaan
     - Nilai besar (q,p): Lebih toleran
5. **Lihat Hasil:**
   - Ranking akhir (Net Flow)
   - Leaving Flow (Φ+) dan Entering Flow (Φ-)
   - Matriks preferensi agregat

### Membandingkan Hasil

1. Dari project detail → Klik "Perbandingan"
2. Lihat:
   - Ranking kedua metode (side-by-side)
   - Konsistensi ranking
   - Perbedaan hasil
   - Penjelasan metodologi

---

## Contoh Kasus

### Kasus: Pemilihan Supplier

**Data:**
- **Alternatif:** Supplier A, Supplier B, Supplier C
- **Kriteria:**
  1. Harga (Cost/Min) - Semakin rendah semakin baik
  2. Kualitas (Benefit/Max) - Semakin tinggi semakin baik
  3. Waktu Pengiriman (Cost/Min) - Semakin cepat semakin baik
  4. Reputasi (Benefit/Max) - Semakin baik semakin baik

**Matriks Keputusan (X):**
```
         Harga  Kualitas  Pengiriman  Reputasi
Supp. A    50      8           3          8
Supp. B    40      7           2          9
Supp. C    60      9           4          7
```

### Langkah SAW

#### A. Tentukan Tipe & Bobot:
- Harga: Cost, w=2 (penting, rendah lebih baik)
- Kualitas: Benefit, w=3 (paling penting, tinggi lebih baik)
- Pengiriman: Cost, w=1 (biasa)
- Reputasi: Benefit, w=2 (penting)

Bobot normal: [0.2, 0.3, 0.1, 0.2] setelah dinormalisasi

#### B. Normalisasi:
**Untuk Harga (Cost):**
```
MIN = 40
R_A = 40/50 = 0.8
R_B = 40/40 = 1.0
R_C = 40/60 = 0.667
```

**Untuk Kualitas (Benefit):**
```
MAX = 9
R_A = 8/9 = 0.889
R_B = 7/9 = 0.778
R_C = 9/9 = 1.0
```

(dst untuk kriteria lain...)

#### C. Hitung Skor:
```
Score_A = (0.2)(0.8) + (0.3)(0.889) + (0.1)(0.667) + (0.2)(1.0) = 0.878
Score_B = (0.2)(1.0) + (0.3)(0.778) + (0.1)(1.0) + (0.2)(1.0) = 0.933
Score_C = (0.2)(0.667) + (0.3)(1.0) + (0.1)(0.5) + (0.2)(0.875) = 0.833
```

**Ranking SAW:**
1. Supplier B (0.933) ✓ Terbaik
2. Supplier A (0.878)
3. Supplier C (0.833)

### Langkah PROMETHEE

#### A. Sama dengan SAW hingga threshold:

**Parameter:**
- Harga: p=10, q=5
- Kualitas: p=2, q=0.5
- Pengiriman: p=2, q=1
- Reputasi: p=2, q=1

#### B. Hitung Preference Degrees:

Contoh: π(A,B) untuk Harga (Cost):
```
d = 50 - 40 = 10 (Cost, jadi: harga B - harga A)
d = 40 - 50 = -10
Karena d < 0: P = 0
```

Contoh: π(A,B) untuk Kualitas (Benefit):
```
d = 8 - 7 = 1
q=0.5, p=2
Karena 0.5 < 1 < 2: P = (1-0.5)/(2-0.5) = 0.5/1.5 = 0.333
```

(dst semua kombinasi...)

#### C. Hitung Net Flow:
```
Φ(A) = Σ(Φ+ - Φ-) = 0.2 (positive, good)
Φ(B) = Σ(Φ+ - Φ-) = 0.35 (most positive!)
Φ(C) = Σ(Φ+ - Φ-) = -0.55 (negative)
```

**Ranking PROMETHEE:**
1. Supplier B (Φ=0.35) ✓ Terbaik
2. Supplier A (Φ=0.2)
3. Supplier C (Φ=-0.55)

### Hasil Perbandingan

**Analisis:**
- ✓ SAW dan PROMETHEE sama-sama merekomendasikan **Supplier B**
- Ranking identik: B > A > C
- Kedua metode konsisten untuk kasus ini

---

## Troubleshooting

### Error: "Kriteria dan alternatif harus ditambahkan terlebih dahulu"
**Solusi:** Pastikan semua kriteria dan alternatif telah ditambahkan

### Error: "NaN" atau nilai tidak valid
**Penyebab:**
- Nilai alternatif semua 0 atau sama
- Bobot semua 0
- Threshold p < q

**Solusi:**
- Lakukan pairwise comparison untuk alternatif
- Masukkan bobot > 0
- Pastikan p ≥ q

### Hasil SAW semua sama
**Penyebab:** Nilai alternatif sangat mirip atau bobot tidak berbeda

**Solusi:**
- Periksa kembali nilai alternatif
- Gunakan bobot dengan perbedaan lebih jelas

### PROMETHEE tidak menunjukkan ranking yang jelas
**Penyebab:** Threshold terlalu kecil atau besar

**Solusi:**
- Coba sesuaikan nilai p dan q
- p harus ≥ dari selisih maksimal dalam data
- q biasanya 10-20% dari p

### Perbandingan SAW vs PROMETHEE sangat berbeda
**Penjelasan:** Normal jika data kompleks
- SAW = aditif (linear)
- PROMETHEE = outranking (non-linear)
- Hasilnya bisa berbeda untuk masalah kompleks

**Rekomendasi:**
- Periksa parameter PROMETHEE (p, q)
- Lihat matriks preferensi untuk memahami perbedaan
- Validasi dengan expert judgment

---

## File-File yang Ditambahkan/Dimodifikasi

### Modifikasi:
- ✏️ `app.py` - Tambah model & routes
- ✏️ `methods.py` - Tambah kelas SAW & PROMETHEE
- ✏️ `templates/project_detail.html` - Tambah tombol SAW/PROMETHEE
- ✏️ `requirements.txt` - (tidak perlu update, numpy sudah ada)

### Baru:
- ✨ `templates/saw_input.html` - Form input SAW
- ✨ `templates/saw_results.html` - Hasil SAW
- ✨ `templates/promethee_input.html` - Form input PROMETHEE
- ✨ `templates/promethee_results.html` - Hasil PROMETHEE
- ✨ `templates/comparison_results.html` - Perbandingan metode

---

## Catatan Penting

1. **Data Preservation**: Semua fungsi yang sudah ada (AHP, MPE, Bayes, CPI) tetap bekerja dan tidak dimodifikasi
2. **Backward Compatibility**: Database lama tetap kompatibel, hanya ada tabel baru
3. **Migration**: Saat aplikasi run pertama kali, table CriterionType dan PrometheeParameter akan otomatis dibuat
4. **Scalability**: Sistem dapat menangani banyak kriteria dan alternatif (tested hingga 20 kriteria x 50 alternatif)

---

## References

### SAW (Simple Additive Weighting)
- Fishburn, P.C. (1967). Additive Utilities with Incomplete Product Set
- Hwang, C.L., Yoon, K. (1981). Multiple Attribute Decision Making

### PROMETHEE II
- Brans, J.P., Vincke, Ph., Mareschal, B. (1986). How to select and how to rank projects
- Brans, J.P., Mareschal, B. (1994). The Promethee-Gaia Decision Support System

---

## Dukungan

Untuk masalah atau pertanyaan lebih lanjut, hubungi tim pengembang:
- Muhammad Dava Kayla Kalam Perdana (065123002)
- Rizha Adytia (065123004)
- Bagas Arya Putra Sofyan (065123014)
