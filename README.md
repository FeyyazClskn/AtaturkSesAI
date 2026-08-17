# Atatürk TTS

Türkçe tarih anlatımı için Fish Audio API kullanan masaüstü TTS uygulaması.

## Son kullanıcı

### Windows

GitHub Releases bölümünden **AtaturkTTS-Setup.exe** indirin ve çift tıklayın.

Kurulumdan sonra Başlat menüsünde **Atatürk TTS** görünür. İsterseniz masaüstü kısayolu oluşturulur.

Son kullanıcı için Python, pip ve FFmpeg kurulması gerekmez; Windows paketi bunları uygulamayla birlikte paketler.

### Arch Linux / EndeavourOS

GitHub Releases bölümünden **AtaturkTTS-Linux.tar.gz** indirin, açın ve:

```bash
./install-linux.sh
```

çalıştırın.

Script gerekli Arch paketlerini kontrol eder, eksikleri kurar, uygulamayı kurar ve çalıştırır.

## API anahtarı

Her kullanıcı kendi Fish Audio API anahtarını kullanmalıdır.

1. Fish Audio hesabına giriş yapın.
2. Dashboard → API Keys bölümünü açın.
3. Create New Key ile anahtar oluşturun.
4. Atatürk TTS → AYARLAR → Fish Audio API anahtarı.
5. Anahtarı yapıştırın.
6. KAYDET.

Anahtar GitHub'a veya kaynak koda konulmaz.

Linux:
`~/.config/ataturk-tts/settings.json`

Windows:
`%USERPROFILE%\.config\ataturk-tts\settings.json`

Detay: `API_KEY_KURULUM.md`

## Ses modelleri

Program başlangıçta 7 public Fish Audio Atatürk voice modelini listeler:

- Atatürk - Dramatik
- Mustafa Kemal Atatürk
- Atatürk - Tarihî
- Atatürk - Resmî
- Atatürk - Enerjik
- Atatürk - Sinematik
- Atatürk - KAOT

Ayrıca AYARLAR → SES MODELLERİ → Model ekle ile başka `reference_id` değerleri eklenebilir.

## Özellikler

- Türkçe arayüz ve Unicode
- 7 hazır Atatürk modeli
- Özel voice model ekleme
- Fish Audio API
- WAV / MP3
- MP3 bitrate
- Uzun metin parçalama ve birleştirme
- Çıktı klasörü seçimi
- Gerçek dosya yöneticisi açma
- MPV ile oynatma
- Windows masaüstü kısayolu
- Linux uygulama menüsü
- GitHub Actions ile Windows/Linux release

## Geliştirici

Linux/Fish:

```fish
python -m venv .venv
source .venv/bin/activate.fish
python -m pip install -r requirements.txt
python ataturk_tts.py
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python ataturk_tts.py
```

## Release

```bash
git add .
git commit -m "Ataturk TTS v1.0.0"
git push origin main
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions iki dosya üretir:

- `AtaturkTTS-Setup.exe`
- `AtaturkTTS-Linux.tar.gz`

## Lisans

Kod MIT lisanslıdır. Fish Audio voice modelleri ve üretilen sesler bu lisansın parçası değildir. Model/voice kullanım şartlarını ve ticari kullanım haklarını Fish Audio'nun güncel koşullarına göre kontrol edin.

Bu repository Atatürk'ün gerçek ses kayıtlarını veya model eğitim ağırlıklarını içermez.

## Windows'ta EXE'yi kendin oluşturmak

Windows bilgisayarında repository klasörünü açın ve:

```bat
build-windows.bat
```

çalıştırın.

Script Python ortamını, gerekli paketleri ve FFmpeg'i hazırlayıp:

```text
dist\AtaturkTTS.exe
```

oluşturur.

Bu dosya doğrudan çalıştırılabilir.

Windows kurulum dosyası (`AtaturkTTS-Setup.exe`) üretmek için Inno Setup kurup:

```bat
iscc installer.iss
```

çalıştırabilirsiniz. GitHub Actions bunu otomatik olarak da yapar.
