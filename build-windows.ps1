$ErrorActionPreference = "Stop"

Write-Host "Ataturk TTS Windows build basliyor..." -ForegroundColor Yellow

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher (py) bulunamadi. Python 3.12+ kurun."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m pip install pyinstaller

New-Item -ItemType Directory -Force -Path bin | Out-Null

if (-not (Test-Path "bin\ffmpeg.exe")) {
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile "ffmpeg.zip"
    Expand-Archive -Force "ffmpeg.zip" "ffmpeg-extract"
    $ffmpeg = Get-ChildItem "ffmpeg-extract" -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    Copy-Item $ffmpeg.FullName "bin\ffmpeg.exe"
    Remove-Item "ffmpeg.zip" -Force
    Remove-Item "ffmpeg-extract" -Recurse -Force
}

Remove-Item build, dist -Recurse -Force -ErrorAction SilentlyContinue

& ".\.venv\Scripts\python.exe" -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name AtaturkTTS `
  --add-data "README.md;." `
  --add-binary "bin\ffmpeg.exe;bin" `
  ataturk_tts.py

Write-Host ""
Write-Host "TAMAM: dist\AtaturkTTS.exe" -ForegroundColor Green
