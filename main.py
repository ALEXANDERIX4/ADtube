import os
import sys
import threading
import yt_dlp
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineScript
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):

  def __init__(self, current_speed, parent=None):
    super().__init__(parent)
    self.setWindowTitle("ADtube Settings")
    self.setFixedSize(300, 150)
    self.setStyleSheet("background-color: #1f1f1f; color: #fff;")

    layout = QFormLayout(self)

    self.speed_combo = QComboBox()
    self.speed_combo.addItems(["8x", "16x", "32x"])
    self.speed_combo.setCurrentText(f"{current_speed}x")
    self.speed_combo.setStyleSheet(
        "background: #272727; color: #fff; padding: 4px; border-radius: 4px;"
    )

    layout.addRow(QLabel("Ad Fast-Forward Speed:"), self.speed_combo)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok
        | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(self.accept)
    buttons.rejected.connect(self.reject)
    buttons.setStyleSheet(
        "QPushButton { background: #3ea6ff; color: #000; font-weight: bold;"
        " padding: 6px 12px; border-radius: 4px; }"
    )
    layout.addRow(buttons)

  def get_speed(self):
    text = self.speed_combo.currentText().replace("x", "")
    return int(text)


class ADtubePlayer(QMainWindow):

  def __init__(self):
    super().__init__()
    self.setWindowTitle("ADtube")
    self.resize(1280, 720)
    self.setStyleSheet("background-color: #0f0f0f; color: #fff;")

    self.ad_speed = 16  # Default ad speed

    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Custom Minimal Top Bar (Locked Height)
    top_bar = QWidget()
    top_bar.setFixedHeight(46)
    top_bar.setStyleSheet(
        "background-color: #0f0f0f; border-bottom: 1px solid #272727;"
    )
    bar_layout = QHBoxLayout(top_bar)
    bar_layout.setContentsMargins(10, 6, 10, 6)

    self.btn_back = QPushButton("←")
    self.btn_forward = QPushButton("→")
    self.btn_home = QPushButton("🏠 Home")
    self.btn_download = QPushButton("📥 Download Video")
    self.btn_settings = QPushButton("⚙ Settings")

    for btn in [
        self.btn_back,
        self.btn_forward,
        self.btn_home,
        self.btn_download,
        self.btn_settings,
    ]:
      btn.setStyleSheet(
          "background: #272727; color: #fff; border: none; padding: 6px 12px;"
          " border-radius: 4px; font-weight: bold;"
      )
      bar_layout.addWidget(btn)

    # Highlight download button slightly so it stands out
    self.btn_download.setStyleSheet(
        "background: #cc0000; color: #fff; border: none; padding: 6px 12px;"
        " border-radius: 4px; font-weight: bold;"
    )

    bar_layout.addStretch()
    main_layout.addWidget(top_bar, 0)

    # Web View (YouTube Engine)
    self.view = QWebEngineView()
    self.inject_adblock_script()
    main_layout.addWidget(self.view, 1)

    # Button Connections
    self.btn_back.clicked.connect(self.view.back)
    self.btn_forward.clicked.connect(self.view.forward)
    self.btn_home.clicked.connect(
        lambda: self.view.setUrl(QUrl("https://www.youtube.com"))
    )
    self.btn_download.clicked.connect(self.start_download)
    self.btn_settings.clicked.connect(self.open_settings)

    # Load YouTube directly
    self.view.setUrl(QUrl("https://www.youtube.com"))

  def inject_adblock_script(self):
    script_code = f"""
            window.adSkipSpeed = {self.ad_speed};
            setInterval(() => {{
                const skipBtn = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern');
                if (skipBtn) skipBtn.click();

                const ads = document.querySelectorAll('.ad-showing, .ad-interrupting, .ytd-ad-slot-renderer, ytd-display-ad-renderer');
                ads.forEach(ad => ad.style.display = 'none');

                const vid = document.querySelector('video');
                const adOverlay = document.querySelector('.ad-showing');
                if (adOverlay && vid && !isNaN(vid.duration)) {{
                    vid.muted = true;
                    vid.playbackRate = window.adSkipSpeed;
                    vid.currentTime = vid.duration - 0.1;
                }}
            }}, 250);
        """
    adblock_js = QWebEngineScript()
    adblock_js.setSourceCode(script_code)
    adblock_js.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    adblock_js.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)

    profile = self.view.page().profile()
    profile.scripts().clear()
    profile.scripts().insert(adblock_js)

  def start_download(self):
    current_url = self.view.url().toString()
    if "watch?v=" in current_url or "youtu.be/" in current_url:
      self.btn_download.setText("📥 Downloading...")
      self.btn_download.setEnabled(False)
      # Run in background thread so UI doesn't freeze
      threading.Thread(
          target=self.download_worker, args=(current_url,), daemon=True
      ).start()
    else:
      self.btn_download.setText("⚠️ Open a Video First!")
      # Reset text after 2 seconds
      threading.Timer(
          2.0, lambda: self.btn_download.setText("📥 Download Video")
      ).start()

  def download_worker(self, url):
    try:
      downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
      ydl_opts = {
          "outtmpl": os.path.join(downloads_path, "%(title)s.%(ext)s"),
          "format": "best",
      }
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
      self.download_complete_ui(success=True)
    except Exception as e:
      print("Download failed:", e)
      self.download_complete_ui(success=False)

  def download_complete_ui(self, success):
    if success:
      self.btn_download.setText("✅ Downloaded!")
    else:
      self.btn_download.setText("❌ Failed")
    # Reset button text back after 3 seconds
    threading.Timer(
        3.0,
        lambda: (
            self.btn_download.setText("📥 Download Video"),
            self.btn_download.setEnabled(True),
        ),
    ).start()

  def open_settings(self):
    dialog = SettingsDialog(self.ad_speed, self)
    if dialog.exec() == QDialog.DialogCode.Accepted:
      self.ad_speed = dialog.get_speed()
      self.view.page().runJavaScript(f"window.adSkipSpeed = {self.ad_speed};")


if __name__ == "__main__":
  app = QApplication(sys.argv)
  player = ADtubePlayer()
  player.show()
  sys.exit(app.exec())
