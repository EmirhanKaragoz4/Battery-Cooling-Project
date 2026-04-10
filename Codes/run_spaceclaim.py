"""
SpaceClaim Launcher
====================
Channel_*.step dosyalarini sirayla SpaceClaim ile acar ve
/RunScript flag ile spaceclaim_automate.py scriptini calistirir.

Calistir:
    python run_spaceclaim.py
"""

import os
import glob
import subprocess
import sys

# =============================================================================
# YAPILANDIRMA
# =============================================================================

SC_EXE     = r"C:\Program Files\ANSYS Inc\v252\scdm\SpaceClaim.exe"
INPUT_DIR  = r"C:\Users\emrkr\OneDrive\Desktop\spaceclaimauto"
SC_SCRIPT  = r"C:\Users\emrkr\OneDrive\Desktop\spaceclaimauto\spaceclaim_automate.py"
PARAM_FILE = r"C:\Users\emrkr\OneDrive\Desktop\spaceclaimauto\sc_params.txt"

# =============================================================================

def main():
    print("=" * 60)
    print("  SpaceClaim Launcher")
    print("=" * 60)

    if not os.path.isfile(SC_EXE):
        print(f"HATA: SpaceClaim bulunamadi: {SC_EXE}")
        input("Enter...")
        return

    if not os.path.isfile(SC_SCRIPT):
        print(f"HATA: Script bulunamadi: {SC_SCRIPT}")
        input("Enter...")
        return

    files = sorted(glob.glob(os.path.join(INPUT_DIR, "Channel_*.step")))
    if not files:
        files = sorted(glob.glob(os.path.join(INPUT_DIR, "Channel_*.SLDPRT")))
    if not files:
        print(f"Dosya bulunamadi: {INPUT_DIR}")
        input("Enter...")
        return

    print(f"  {len(files)} dosya bulundu.\n")

    for i, filepath in enumerate(files, start=1):
        filename = os.path.basename(filepath)
        radius   = os.path.splitext(filename)[0].replace("Channel_", "")

        print(f"[{i}/{len(files)}] {filename}  (radius={radius})")

        # Parametre dosyasini yaz
        with open(PARAM_FILE, "w", encoding="utf-8") as pf:
            pf.write(f"INPUT_FILE={filepath}\n")
            pf.write(f"RADIUS={radius}\n")
            pf.write(f"OUTPUT_DIR={INPUT_DIR}\n")

        # SpaceClaim'i dosya + script ile calistir
        # Dosya ilk arguman olarak verilince SpaceClaim onu acar,
        # /RunScript ile script dosya acildiktan sonra calisir
        cmd = [SC_EXE, filepath, f"/RunScript={SC_SCRIPT}"]
        print(f"       Komut: {' '.join(cmd)}")
        print(f"       Bekleniyor (SpaceClaim kapanana kadar)...")

        result = subprocess.run(cmd, timeout=600)

        if result.returncode == 0:
            print(f"       OK - Channel_{radius}.scdoc kaydedildi.")
        else:
            print(f"       UYARI: Hata kodu {result.returncode}")
        print()

    if os.path.isfile(PARAM_FILE):
        os.remove(PARAM_FILE)

    print("=" * 60)
    print("  Tamamlandi.")
    print(f"  Cikti: {INPUT_DIR}")
    print("=" * 60)
    input("Enter...")


if __name__ == "__main__":
    main()