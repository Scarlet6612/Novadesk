import os
import sys
import subprocess
import shutil
from pathlib import Path

def build():
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)

    print("=== NovaDesk PyInstaller Build Başlıyor ===")
    
    # Clean previous builds
    for d in ["build", "dist"]:
        p = script_dir / d
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=NovaDesk",
        "--onefile",
        "--windowed",  # No console window
        "--icon=novadesk.ico",
        "--clean",
        "main.py"
    ]

    print("Çalıştırılan komut:", " ".join(cmd))
    result = subprocess.run(cmd, check=True)

    dist_exe = script_dir / "dist" / "NovaDesk.exe"
    if dist_exe.exists():
        size_mb = dist_exe.stat().st_size / (1024 * 1024)
        print(f"\n[OK] NovaDesk.exe basariyla olusturuldu!")
        print(f"Konum: {dist_exe}")
        print(f"Boyut: {size_mb:.2f} MB")
        return dist_exe
    else:
        print("\n[HATA] Build basarisiz oldu, EXE bulunamadi.")
        sys.exit(1)

if __name__ == "__main__":
    build()
