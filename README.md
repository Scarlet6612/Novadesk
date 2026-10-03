# 🚀 NovaDesk

> **Windows için Ultra Hafif, Modern ve Sanal Masaüstü Düzenleyici (CooDesker / Fences Alternatifi)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078d7.svg)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NovaDesk**, Windows masaüstünüzdeki tüm simgeleri ve dosyaları fiziksel konumlarını değiştirmeden (sıfır disk manipülasyonu) akıllıca kategorilere ayıran, arka planda sıfır kaynak tüketen modern bir masaüstü düzenleyicisidir.

---

## ✨ Öne Çıkan Özellikler

- **📁 Sıfır Disk Manipülasyonu (Virtual Organization):** Dosyalarınız fiziksel diskte taşınmaz veya yolları bozulmaz. Masaüstünüz taranır ve sanal kutuda kategorize edilir.
- **⚡ Ultra Düşük Kaynak Tüketimi:**
  - **Boşta CPU:** Kesinlikle **%0.0** (Polling / sürekli tarama yoktur, olay güdümlü Win32 & Watchdog kullanılır).
  - **Boşta RAM:** ~25 - 35 MB arası hafif bellek ayak izi.
  - **Açılış Hızı:** < 300 milisaniye (Bellek eşlemeli pre-extracted DLL mimarisi).
- **🗂️ 2 Satırlı Kompakt Izgara & Akıcı Kaydırma:** Masaüstünüzü kaplamayan 2 satırlı düzen; çok sayıda dosya olduğunda pürüzsüz dikey kaydırma.
- **🔘 Sol Üst "Applications" Küçülme Modu (Roll-up):** Alta alma simgesine (—) basıldığında sol üstte minimal, şık bir hap çubuğa dönüşür; tıklandığında anında eski boyutuna açılır.
- **🎨 Saydamlık & Akrilik Bulanıklık Kontrolü:** Koyu akrilik tema ve sağ tık menüsünden seçilebilir saydamlık ayarı (%35, %50, %70, %85, %100).
- **🔒 Konum & Boyut Sabitleme:** Masaüstünde yanlışlıkla sürüklenmeyi engellemek için tek tıkla kilitleme (`🔒 / 🔓`).
- **🧹 Masaüstü Simgelerini Gizleme:** Windows yerel masaüstü simgelerini gizleyerek tüm dosyaların yalnızca NovaDesk içerisinde düzenli durmasını sağlar.
- **🔍 Canlı Arama & Akıllı Filtreleme:** Arama çubuğu ile dosyaları anında filtreleme; Uygulamalar, Belgeler, Medya, Geliştirme ve Klasörler sekmeleri.
- **📂 Klasör Portalı (Folder Portal):** İstenen herhangi bir klasörü (ör. *İndirilenler* veya *Projeler*) masaüstünde canlı bir portal olarak görüntüleyebilme.
- **🚀 Windows ile Otomatik Başlatma:** Sistem başlangıcına otomatik entegrasyon.

---

## 📥 İndirme ve Kolay Kurulum (Kullanıcılar İçin)

Hiçbir Python veya kütüphane kurulumu yapmadan doğrudan kullanmak için:

1. [Releases](../../releases) sayfasından en son **`NovaDesk-v2.0-Windows-x64.zip`** dosyasını indirin.
2. Zip arşivini istediğiniz bir klasöre çıkartın.
3. **`NovaDesk.exe`** dosyasına çift tıklayarak çalıştırın!

---

## 🛠️ Kaynak Koddan Çalıştırma (Geliştiriciler İçin)

### Gereksinimler
- Python 3.10 veya üzeri
- Windows 10 / 11 (64-bit)

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/KULLANICI_ADINIZ/novadesk.git
cd novadesk
```

### 2. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Uygulamayı Başlatın
```bash
python main.py
```

### 4. Tek Dosya/Klasör Olarak Derleme (Build)
```bash
python -m PyInstaller --name=NovaDesk --onedir --windowed --icon=novadesk.ico --clean --noconfirm main.py
```
Çıktı `dist/NovaDesk/NovaDesk.exe` yolunda oluşacaktır.

---

## 🏗️ Proje Mimarisi

```
novadesk/
├── main.py            # Uygulama başlangıcı, sistem tepsisi (Tray) ve başlangıç kaydı
├── box_window.py      # Ana arayüz, 2 satırlı görünüm, sekmeler ve küçülme modu
├── file_scanner.py    # Win32 os.scandir, Watchdog dosya izleme, LRU ikon önbelleği
├── win32_helper.py    # Win32 API çağrıları, masaüstü simge gizleme, araç penceresi kancaları
├── styles.py          # Modern koyu akrilik QSS tema ve saydamlık hesaplamaları
├── config.py          # Kullanıcı tercihleri ve boyut/konum yönetimi (config.json)
├── novadesk.ico       # Uygulama simgesi
└── requirements.txt   # Bağımlılıklar
```

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
