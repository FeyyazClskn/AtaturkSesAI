@echo off
setlocal EnableExtensions
title Ataturk TTS - Windows Build

echo ==========================================
echo        ATATURK TTS WINDOWS BUILD
echo ==========================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo Python launcher ^(py^) bulunamadi.
    echo Python 3.12+ kurun ve tekrar deneyin.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Python sanal ortami olusturuluyor...
    py -3 -m venv .venv
)

echo [2/5] Python paketleri kuruluyor...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 goto :fail

echo [3/5] FFmpeg indiriliyor...
if not exist "bin\ffmpeg.exe" (
    if not exist "bin" mkdir bin
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'"
    if errorlevel 1 goto :fail
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "Expand-Archive -Force 'ffmpeg.zip' 'ffmpeg-extract'; $f=Get-ChildItem 'ffmpeg-extract' -Filter 'ffmpeg.exe' -Recurse | Select-Object -First 1; Copy-Item $f.FullName 'bin\ffmpeg.exe'"
    if errorlevel 1 goto :fail
    del /q ffmpeg.zip >nul 2>nul
    rmdir /s /q ffmpeg-extract >nul 2>nul
)

echo [4/5] EXE olusturuluyor...
rmdir /s /q build >nul 2>nul
rmdir /s /q dist >nul 2>nul

".venv\Scripts\python.exe" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name AtaturkTTS ^
  --add-data "README.md;." ^
  --add-binary "bin\ffmpeg.exe;bin" ^
  ataturk_tts.py

if errorlevel 1 goto :fail

echo [5/5] TAMAMLANDI
echo.
echo EXE:
echo   %CD%\dist\AtaturkTTS.exe
echo.
echo Bu dosyaya cift tiklayarak programi acabilirsiniz.
echo.
echo Not: Windows kurulumu ^(Setup.exe^) icin Inno Setup kuruluysa:
echo   iscc installer.iss
echo.
pause
exit /b 0

:fail
echo.
echo ==========================================
echo BUILD BASARISIZ
echo ==========================================
echo Yukaridaki hata mesajini kontrol edin.
pause
exit /b 1
