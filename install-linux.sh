#!/usr/bin/env bash
set -euo pipefail
APP_ID="ataturk-tts"
INSTALL_DIR="${HOME}/.local/share/${APP_ID}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Atatürk TTS Linux Kurulumu ==="
if ! command -v pacman >/dev/null 2>&1; then
  echo "Bu script Arch Linux / EndeavourOS içindir."
  echo "Diğer dağıtımlar için GitHub Releases paketini kullanın."
  exit 1
fi

missing=()
for p in python python-pip ffmpeg mpv; do
  pacman -Q "$p" >/dev/null 2>&1 || missing+=("$p")
done
if [ "${#missing[@]}" -gt 0 ]; then
  sudo pacman -S --needed --noconfirm "${missing[@]}"
fi

rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR"
cp "$SRC/ataturk_tts.py" "$INSTALL_DIR/"
cp "$SRC/requirements.txt" "$INSTALL_DIR/"
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/python" -m pip install --upgrade pip
"$INSTALL_DIR/.venv/bin/python" -m pip install -r "$INSTALL_DIR/requirements.txt"

cat > "$BIN_DIR/AtaturkTTS" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/ataturk_tts.py" "\$@"
EOF
chmod +x "$BIN_DIR/AtaturkTTS"

cat > "$DESKTOP_DIR/AtaturkTTS.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Atatürk TTS
Comment=Türkçe tarih anlatımı seslendirme
Exec=$BIN_DIR/AtaturkTTS
Icon=audio-input-microphone
Terminal=false
Categories=AudioVideo;Audio;Utility;
StartupWMClass=AtaturkTTS
EOF
chmod +x "$DESKTOP_DIR/AtaturkTTS.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true

echo "Kurulum tamamlandı. Atatürk TTS başlatılıyor..."
"$BIN_DIR/AtaturkTTS"
