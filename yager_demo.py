#!/usr/bin/env python3
"""
Demo script untuk Metodologi Ronald R. Yager KMKK Kualitatif
Menjalankan analisis dan menampilkan hasil pada terminal/console
"""

from methods import YagerMethod

def main():
    """
    Fungsi utama untuk menjalankan demo Yager Method
    """
    print("Memulai analisis KMKK menggunakan Metodologi Ronald R. Yager...")
    print("=" * 60)
    
    # Jalankan analisis dan tampilkan hasil
    YagerMethod.print_results()
    
    print("\n" + "=" * 60)
    print("Analisis selesai!")

if __name__ == "__main__":
    main()