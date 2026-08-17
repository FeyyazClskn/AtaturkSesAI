$ErrorActionPreference = "Stop"
$InstallDir = Join-Path $env:LOCALAPPDATA "AtaturkTTS"
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }

if (-not $py) {
  Write-Host "Python bulunamadı. Son kullanıcı için GitHub Releases içindeki AtaturkTTS-Setup.exe dosyasını kullanın." -ForegroundColor Red
  exit 1
}
if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item "$Source\ataturk_tts.py" $InstallDir
Copy-Item "$Source\requirements.txt" $InstallDir
& $py.Source -m venv "$InstallDir\.venv"
& "$InstallDir\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$InstallDir\.venv\Scripts\python.exe" -m pip install -r "$InstallDir\requirements.txt"

$launcher = Join-Path $InstallDir "AtaturkTTS.cmd"
"@echo off`r`n`"$InstallDir\.venv\Scripts\python.exe`" `"$InstallDir\ataturk_tts.py`"" | Set-Content $launcher -Encoding ASCII

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcut = Join-Path $desktop "Atatürk TTS.lnk"
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($shortcut)
$s.TargetPath = $launcher
$s.WorkingDirectory = $InstallDir
$s.Save()
Start-Process $launcher
