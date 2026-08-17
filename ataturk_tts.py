import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import requests
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget
)

APP_NAME = "Atatürk TTS"
API_URL = "https://api.fish.audio/v1/tts"
DEFAULT_MODEL = "s2.1-pro-free"
CONFIG_DIR = Path.home() / ".config" / "ataturk-tts"
CONFIG_FILE = CONFIG_DIR / "settings.json"
DEFAULT_OUTPUT = Path.home() / "AtaturkTTS" / "outputs"
DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICES = [
    {
        "name": "Atatürk - Dramatik",
        "id": "fcaf3a5d2532428e96578a61aee13625",
        "description": "Güçlü, otoriter, enerjik ve dramatik Türkçe anlatım."
    },
    {
        "name": "Mustafa Kemal Atatürk",
        "id": "77d69ed5b73643f2b9e140a1c3c45c33",
        "description": "Derin, ciddi, ölçülü ve otoriter Türkçe anlatım."
    },
    {
        "name": "Atatürk - Tarihî",
        "id": "82f4a569aaf44bc186da3b4da9df61fb",
        "description": "Ciddi ve tarih anlatımına uygun Atatürk modeli."
    },
    {
        "name": "Atatürk - Resmî",
        "id": "5492f9e7fee14dd280893c94071cc207",
        "description": "Daha sakin ve ölçülü resmî anlatım karakteri."
    },
    {
        "name": "Atatürk - Enerjik",
        "id": "2b41ab5ba5e94ed3b86f6f5fb39ee844",
        "description": "Daha enerjik ve vurucu tarihî konuşma karakteri."
    },
    {
        "name": "Atatürk - Sinematik",
        "id": "598481af4715451390b1ca903e8f6286",
        "description": "Ciddi ve dramatik sinematik tarih anlatımı."
    },
    {
        "name": "Atatürk - KAOT",
        "id": "eca2b734c1484863aa960abdf47fe23a",
        "description": "Fish Audio'daki diğer public Atatürk ses modeli."
    },
]

COLORS = {
    "bg": "#090c10",
    "card": "#11161d",
    "card2": "#151b23",
    "input": "#0d1218",
    "border": "#252d38",
    "border2": "#394555",
    "text": "#f2f4f7",
    "muted": "#8f9aaa",
    "dim": "#657080",
    "gold": "#d9a441",
    "gold2": "#e7b452",
    "green": "#57c78a",
    "red": "#e06c75",
}

def load_settings():
    defaults = {
        "api_key": "",
        "output_dir": str(DEFAULT_OUTPUT),
        "model": "s2-pro",
        "format": "wav",
        "mp3_bitrate": 192,
        "chunk_size": 1800,
        "auto_open": False,
        "voices": DEFAULT_VOICES.copy(),
    }
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        defaults.update(data)
    except Exception:
        pass
    if not defaults.get("voices"):
        defaults["voices"] = DEFAULT_VOICES.copy()
    Path(defaults["output_dir"]).mkdir(parents=True, exist_ok=True)
    return defaults

def save_settings(settings):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def app_base_dir():
    # PyInstaller one-file apps unpack bundled files to _MEIPASS.
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

def binary(name):
    exe = name + (".exe" if sys.platform.startswith("win") else "")
    bundled = app_base_dir() / "bin" / exe
    if bundled.exists():
        return str(bundled)
    found = shutil.which(exe)
    return found or exe

def open_folder(path):
    path = Path(path).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    managers = ["thunar", "dolphin", "nemo", "nautilus", "pcmanfm", "caja"]
    for manager in managers:
        exe = shutil.which(manager)
        if exe:
            subprocess.Popen([exe, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

def split_text(text, max_chars):
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks, current = [], ""
    paragraphs = re.split(r"\n\s*\n", text)
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > max_chars:
                for word in sentence.split():
                    if len(current) + len(word) + 1 <= max_chars:
                        current += (" " if current else "") + word
                    else:
                        if current:
                            chunks.append(current.strip())
                        current = word
                continue
            if len(current) + len(sentence) + 1 <= max_chars:
                current += (" " if current else "") + sentence
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence
    if current:
        chunks.append(current.strip())
    return chunks

def api_headers(api_key, model):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model,
    }

def generate_audio(text, output_file, reference_id, api_key, model):
    response = requests.post(
        API_URL,
        headers=api_headers(api_key, model),
        json={"text": text, "reference_id": reference_id, "format": "wav"},
        timeout=180,
    )
    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"Fish Audio API hatası ({response.status_code}):\n\n{detail}")
    if not response.content:
        raise RuntimeError("Fish Audio boş ses döndürdü.")
    output_file.write_bytes(response.content)

def merge_wav(files, output_file):
    if len(files) == 1:
        shutil.copy2(files[0], output_file)
        return
    list_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            list_file = f.name
            for item in files:
                p = str(Path(item).resolve()).replace("'", "'\\''")
                f.write(f"file '{p}'\n")
        result = subprocess.run(
            [binary("ffmpeg"), "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", str(output_file)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode:
            raise RuntimeError("FFmpeg WAV birleştirme hatası:\n\n" + result.stderr)
    finally:
        if list_file:
            try:
                os.remove(list_file)
            except OSError:
                pass

def convert_mp3(wav_file, bitrate):
    wav_file = Path(wav_file)
    mp3 = wav_file.with_suffix(".mp3")
    result = subprocess.run(
        [binary("ffmpeg"), "-y", "-i", str(wav_file), "-codec:a", "libmp3lame", "-b:a", f"{bitrate}k", str(mp3)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode:
        raise RuntimeError("FFmpeg MP3 dönüştürme hatası:\n\n" + result.stderr)
    return mp3

class VoiceWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, text, voice_id, voice_name, settings):
        super().__init__()
        self.text = text
        self.voice_id = voice_id
        self.voice_name = voice_name
        self.settings = settings

    @Slot()
    def run(self):
        try:
            api_key = self.settings["api_key"].strip()
            if not api_key:
                raise RuntimeError("Fish Audio API anahtarı ayarlanmamış.")
            chunks = split_text(self.text, int(self.settings["chunk_size"]))
            if not chunks:
                raise RuntimeError("Okunacak metin bulunamadı.")

            output_dir = Path(self.settings["output_dir"]).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.TemporaryDirectory() as temp:
                temp = Path(temp)
                parts = []
                total = len(chunks)

                for i, chunk in enumerate(chunks):
                    self.status.emit(f"Ses oluşturuluyor: {i + 1} / {total}")
                    part = temp / f"part_{i:04d}.wav"
                    generate_audio(
                        chunk, part, self.voice_id, api_key, self.settings["model"]
                    )
                    parts.append(part)
                    self.progress.emit(int(((i + 1) / total) * 85))

                self.status.emit("Ses parçaları birleştiriliyor...")
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe = re.sub(r"[^A-Za-z0-9_-]+", "_", self.voice_name).strip("_")
                wav = output_dir / f"{safe}_{stamp}.wav"
                merge_wav(parts, wav)
                self.progress.emit(92)

                if self.settings["format"].lower() == "mp3":
                    self.status.emit("MP3 oluşturuluyor...")
                    final = convert_mp3(wav, int(self.settings["mp3_bitrate"]))
                    try:
                        wav.unlink()
                    except OSError:
                        pass
                else:
                    final = wav

                self.progress.emit(100)
                self.status.emit("Ses başarıyla oluşturuldu.")
                self.finished.emit(str(final))
        except Exception as e:
            self.failed.emit(str(e))

class SettingsDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = json.loads(json.dumps(settings, ensure_ascii=False))
        self.setWindowTitle("Ayarlar")
        self.resize(620, 520)

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        general = QWidget()
        form = QFormLayout(general)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(14)

        self.api_key = QLineEdit(self.settings["api_key"])
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setPlaceholderText("sk-fish-...")
        form.addRow("Fish Audio API anahtarı:", self.api_key)

        key_hint = QLabel(
            "Anahtar yalnızca bu bilgisayardaki ayar dosyasına kaydedilir; GitHub'a yüklenmez."
        )
        key_hint.setWordWrap(True)
        key_hint.setObjectName("small")
        form.addRow("", key_hint)

        self.model = QComboBox()
        self.model.addItems(["s2-pro", "s2.1-pro-free", "s1"])
        self.model.setCurrentText(self.settings["model"])
        form.addRow("Fish modeli:", self.model)

        self.output = QLineEdit(self.settings["output_dir"])
        output_row = QHBoxLayout()
        output_row.addWidget(self.output)
        browse = QPushButton("Gözat")
        browse.clicked.connect(self.choose_output)
        output_row.addWidget(browse)
        form.addRow("Çıktı klasörü:", output_row)

        self.format = QComboBox()
        self.format.addItems(["WAV", "MP3"])
        self.format.setCurrentText(self.settings["format"].upper())
        form.addRow("Varsayılan çıktı:", self.format)

        self.bitrate = QComboBox()
        self.bitrate.addItems(["128", "192", "256", "320"])
        self.bitrate.setCurrentText(str(self.settings["mp3_bitrate"]))
        form.addRow("MP3 bitrate (kbps):", self.bitrate)

        self.chunk = QSpinBox()
        self.chunk.setRange(500, 4000)
        self.chunk.setSingleStep(100)
        self.chunk.setValue(int(self.settings["chunk_size"]))
        form.addRow("Parça uzunluğu:", self.chunk)

        self.auto_open = QCheckBox("Ses oluşturulduğunda çıktı klasörünü otomatik aç")
        self.auto_open.setChecked(bool(self.settings["auto_open"]))
        form.addRow("", self.auto_open)

        tabs.addTab(general, "Genel")

        voices_tab = QWidget()
        voices_layout = QVBoxLayout(voices_tab)
        voices_layout.setContentsMargins(20, 20, 20, 20)

        self.voice_list = QComboBox()
        for v in self.settings["voices"]:
            self.voice_list.addItem(v["name"], v["id"])
        voices_layout.addWidget(QLabel("Kayıtlı ses modelleri"))
        voices_layout.addWidget(self.voice_list)

        add_box = QFrame()
        add_form = QFormLayout(add_box)
        self.voice_name = QLineEdit()
        self.voice_id = QLineEdit()
        self.voice_desc = QLineEdit()
        add_form.addRow("Ad:", self.voice_name)
        add_form.addRow("Reference ID:", self.voice_id)
        add_form.addRow("Açıklama:", self.voice_desc)
        voices_layout.addWidget(add_box)

        voice_buttons = QHBoxLayout()
        add_voice = QPushButton("Model ekle")
        remove_voice = QPushButton("Seçileni kaldır")
        add_voice.clicked.connect(self.add_voice)
        remove_voice.clicked.connect(self.remove_voice)
        voice_buttons.addWidget(add_voice)
        voice_buttons.addWidget(remove_voice)
        voice_buttons.addStretch()
        voices_layout.addLayout(voice_buttons)
        voices_layout.addStretch()

        tabs.addTab(voices_tab, "Ses Modelleri")

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Çıktı klasörünü seç", self.output.text())
        if folder:
            self.output.setText(folder)

    def add_voice(self):
        name = self.voice_name.text().strip()
        vid = self.voice_id.text().strip()
        desc = self.voice_desc.text().strip() or "Özel Fish Audio ses modeli."
        if not name or not vid:
            QMessageBox.warning(self, "Eksik bilgi", "Model adı ve Reference ID gerekli.")
            return
        self.settings["voices"].append({"name": name, "id": vid, "description": desc})
        self.voice_list.addItem(name, vid)
        self.voice_name.clear()
        self.voice_id.clear()
        self.voice_desc.clear()

    def remove_voice(self):
        index = self.voice_list.currentIndex()
        if index < 0:
            return
        if len(self.settings["voices"]) <= 1:
            QMessageBox.warning(self, "Silinemiyor", "En az bir ses modeli kalmalı.")
            return
        self.settings["voices"].pop(index)
        self.voice_list.removeItem(index)

    def get_settings(self):
        self.settings["api_key"] = self.api_key.text().strip()
        self.settings["model"] = self.model.currentText()
        self.settings["output_dir"] = self.output.text().strip()
        self.settings["format"] = self.format.currentText().lower()
        self.settings["mp3_bitrate"] = int(self.bitrate.currentText())
        self.settings["chunk_size"] = self.chunk.value()
        self.settings["auto_open"] = self.auto_open.isChecked()
        return self.settings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.thread = None
        self.worker = None
        self.last_audio = None

        self.setWindowTitle(APP_NAME)
        self.resize(1120, 820)
        self.setMinimumSize(900, 680)
        self.build_ui()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(38, 30, 38, 30)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("ATATÜRK TTS")
        title.setObjectName("title")
        subtitle = QLabel("Tarih anlatımı için yapay zekâ seslendirme stüdyosu")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        settings_btn = QPushButton("⚙  AYARLAR")
        settings_btn.clicked.connect(self.open_settings)
        header.addWidget(settings_btn, alignment=Qt.AlignTop)

        ready = QLabel("●  HAZIR")
        ready.setObjectName("online")
        header.addWidget(ready, alignment=Qt.AlignTop)
        root.addLayout(header)

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(12)
        root.addWidget(card, 1)

        voice_head = QHBoxLayout()
        voice_label = QLabel("SES MODELİ")
        voice_label.setObjectName("section")
        voice_head.addWidget(voice_label)
        voice_head.addStretch()
        self.voice_count = QLabel()
        self.voice_count.setObjectName("small")
        voice_head.addWidget(self.voice_count)
        layout.addLayout(voice_head)

        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumHeight(48)
        self.voice_combo.currentIndexChanged.connect(self.voice_changed)
        layout.addWidget(self.voice_combo)

        self.description = QLabel()
        self.description.setObjectName("description")
        self.description.setWordWrap(True)
        desc_box = QFrame()
        desc_box.setObjectName("descriptionBox")
        dl = QHBoxLayout(desc_box)
        dl.setContentsMargins(14, 10, 14, 10)
        dl.addWidget(self.description)
        layout.addWidget(desc_box)

        text_head = QHBoxLayout()
        text_label = QLabel("ANLATIM METNİ")
        text_label.setObjectName("section")
        text_head.addWidget(text_label)
        text_head.addStretch()
        self.counter = QLabel("0 karakter")
        self.counter.setObjectName("small")
        text_head.addWidget(self.counter)
        layout.addLayout(text_head)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("")
        self.editor.setMinimumHeight(340)
        self.editor.textChanged.connect(
            lambda: self.counter.setText(f"{len(self.editor.toPlainText()):,} karakter")
        )
        layout.addWidget(self.editor, 1)

        action = QHBoxLayout()
        clear = QPushButton("TEMİZLE")
        clear.setObjectName("secondary")
        clear.clicked.connect(self.editor.clear)
        action.addWidget(clear)
        action.addStretch()
        self.generate = QPushButton("SESİ OLUŞTUR")
        self.generate.setObjectName("primary")
        self.generate.setMinimumSize(210, 50)
        self.generate.clicked.connect(self.start)
        action.addWidget(self.generate)
        layout.addLayout(action)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(7)
        layout.addWidget(self.progress)

        status = QHBoxLayout()
        self.status = QLabel("Hazır")
        self.status.setObjectName("status")
        status.addWidget(self.status)
        status.addStretch()
        self.output_info = QLabel()
        self.output_info.setObjectName("small")
        status.addWidget(self.output_info)
        layout.addLayout(status)

        footer = QHBoxLayout()
        play = QPushButton("▶  OYNAT")
        play.clicked.connect(self.play)
        footer.addWidget(play)
        mp3 = QPushButton("♫  MP3 OLUŞTUR")
        mp3.clicked.connect(self.make_mp3)
        footer.addWidget(mp3)
        folder = QPushButton("📁  ÇIKTI KLASÖRÜ")
        folder.clicked.connect(self.open_output)
        footer.addWidget(folder)
        layout.addLayout(footer)

        self.refresh_voice_list()
        self.refresh_output_label()

    def refresh_voice_list(self):
        current = self.voice_combo.currentText()
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        for v in self.settings["voices"]:
            self.voice_combo.addItem(v["name"], v["id"])
        if current:
            idx = self.voice_combo.findText(current)
            if idx >= 0:
                self.voice_combo.setCurrentIndex(idx)
        self.voice_combo.blockSignals(False)
        self.voice_count.setText(f"{len(self.settings['voices'])} model")
        self.voice_changed()

    def refresh_output_label(self):
        self.output_info.setText(
            "Çıktı: " + str(Path(self.settings["output_dir"]).expanduser())
        )

    def voice_changed(self, _=None):
        idx = self.voice_combo.currentIndex()
        if idx < 0:
            return
        self.description.setText(
            self.settings["voices"][idx]["description"]
        )

    def open_settings(self):
        dlg = SettingsDialog(self, self.settings)
        if dlg.exec() == QDialog.Accepted:
            self.settings = dlg.get_settings()
            Path(self.settings["output_dir"]).expanduser().mkdir(parents=True, exist_ok=True)
            save_settings(self.settings)
            self.refresh_voice_list()
            self.refresh_output_label()
            self.status.setText("Ayarlar kaydedildi.")

    def start(self):
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Metin yok", "Lütfen önce okunacak metni yaz.")
            return
        if not self.settings["api_key"]:
            QMessageBox.warning(
                self, "API anahtarı yok",
                "Önce AYARLAR bölümünden Fish Audio API anahtarını gir."
            )
            return

        idx = self.voice_combo.currentIndex()
        voice = self.settings["voices"][idx]

        self.generate.setEnabled(False)
        self.voice_combo.setEnabled(False)
        self.progress.setValue(0)
        self.status.setText("Ses oluşturma başlatılıyor...")

        self.thread = QThread()
        self.worker = VoiceWorker(
            text, voice["id"], voice["name"], self.settings
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.status.setText)
        self.worker.finished.connect(self.done)
        self.worker.failed.connect(self.error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.thread_done)
        self.thread.start()

    @Slot(str)
    def done(self, filename):
        self.last_audio = filename
        self.status.setText("Ses başarıyla oluşturuldu.")
        if self.settings.get("auto_open"):
            open_folder(Path(filename).parent)
        QMessageBox.information(
            self, "Tamamlandı",
            f"Ses başarıyla oluşturuldu.\n\n{filename}"
        )

    @Slot(str)
    def error(self, message):
        self.progress.setValue(0)
        self.status.setText("Ses oluşturulamadı.")
        QMessageBox.critical(self, "Hata", message)

    def thread_done(self):
        self.generate.setEnabled(True)
        self.voice_combo.setEnabled(True)
        self.worker = None
        self.thread = None

    def play(self):
        if not self.last_audio:
            QMessageBox.warning(self, "Ses yok", "Önce bir ses oluştur.")
            return
        if not (shutil.which("mpv") or (app_base_dir() / "bin" / ("mpv.exe" if sys.platform.startswith("win") else "mpv")).exists()):
            QMessageBox.warning(
                self, "MPV yok",
                "MPV kurulu değil. Arch Linux: sudo pacman -S mpv"
            )
            return
        subprocess.Popen(
            [binary("mpv"), "--no-video", self.last_audio],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def make_mp3(self):
        if not self.last_audio:
            QMessageBox.warning(self, "Ses yok", "Önce bir ses oluştur.")
            return
        try:
            self.status.setText("MP3 oluşturuluyor...")
            mp3 = convert_mp3(self.last_audio, int(self.settings["mp3_bitrate"]))
            self.status.setText("MP3 hazır.")
            QMessageBox.information(self, "Tamamlandı", f"MP3 oluşturuldu:\n\n{mp3}")
        except Exception as e:
            QMessageBox.critical(self, "MP3 hatası", str(e))

    def open_output(self):
        open_folder(self.settings["output_dir"])

def apply_style(app):
    c = COLORS
    app.setStyle("Fusion")
    app.setStyleSheet(f"""
        QWidget {{ background:{c['bg']}; color:{c['text']}; font-family:"Noto Sans","DejaVu Sans"; font-size:14px; }}
        QMainWindow {{ background:{c['bg']}; }}
        QLabel {{ background:transparent; }}
        QLabel#title {{ font-size:30px; font-weight:900; color:{c['text']}; }}
        QLabel#subtitle {{ font-size:13px; color:{c['muted']}; }}
        QLabel#online {{ font-size:12px; font-weight:800; color:{c['green']}; }}
        QLabel#section {{ font-size:11px; font-weight:900; color:{c['text']}; }}
        QLabel#small {{ font-size:11px; color:{c['dim']}; }}
        QLabel#status {{ font-size:12px; color:{c['muted']}; }}
        QFrame#card {{ background:{c['card']}; border:1px solid {c['border']}; border-radius:18px; }}
        QFrame#descriptionBox {{ background:{c['card2']}; border:1px solid {c['border']}; border-radius:9px; }}
        QLabel#description {{ font-size:12px; color:{c['muted']}; }}
        QComboBox, QLineEdit, QSpinBox {{
            background:{c['input']}; color:{c['text']}; border:1px solid {c['border']};
            border-radius:10px; padding:8px 12px; min-height:28px;
        }}
        QComboBox:hover, QLineEdit:hover, QSpinBox:hover {{ border-color:{c['border2']}; }}
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{ border-color:{c['gold']}; }}
        QComboBox QAbstractItemView {{ background:{c['card2']}; color:{c['text']}; selection-background-color:{c['gold']}; selection-color:#111; }}
        QPlainTextEdit {{
            background:{c['input']}; color:{c['text']}; border:1px solid {c['border']};
            border-radius:12px; padding:15px; font-size:15px;
            selection-background-color:{c['gold']}; selection-color:#111;
        }}
        QPlainTextEdit:focus {{ border-color:{c['gold']}; }}
        QPushButton {{
            background:{c['card2']}; color:{c['text']}; border:1px solid {c['border']};
            border-radius:10px; padding:10px 18px; font-weight:800; font-size:12px;
        }}
        QPushButton:hover {{ background:#1b222c; border-color:{c['border2']}; }}
        QPushButton:disabled {{ color:#555f6d; background:#101419; }}
        QPushButton#primary {{ background:{c['gold']}; color:#111; border:none; font-size:13px; font-weight:900; }}
        QPushButton#primary:hover {{ background:{c['gold2']}; }}
        QPushButton#secondary {{ background:transparent; color:{c['muted']}; }}
        QProgressBar {{ background:#0d1116; border:none; border-radius:3px; min-height:7px; max-height:7px; }}
        QProgressBar::chunk {{ background:{c['gold']}; border-radius:3px; }}
        QCheckBox {{ color:{c['text']}; spacing:8px; }}
        QTabWidget::pane {{ border:1px solid {c['border']}; border-radius:10px; }}
        QTabBar::tab {{ background:{c['card2']}; color:{c['muted']}; padding:10px 18px; border:none; }}
        QTabBar::tab:selected {{ color:{c['text']}; background:{c['gold']}; }}
    """)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    apply_style(app)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
