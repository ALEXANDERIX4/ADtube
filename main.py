import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineScript, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QPushButton, QVBoxLayout, QWidget

class ADtubePlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADtube")
        self.resize(1280, 720)
        self.setStyleSheet("background-color: #0f0f0f; color: #fff;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom Minimal Top Bar
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #0f0f0f; border-bottom: 1px solid #272727;")
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(10, 6, 10, 6)

        self.btn_back = QPushButton("←")
        self.btn_forward = QPushButton("→")
        self.btn_home = QPushButton("🏠 Home")

        for btn in [self.btn_back, self.btn_forward, self.btn_home]:
            btn.setStyleSheet("background: #272727; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
            bar_layout.addWidget(btn)

        bar_layout.addStretch()
        main_layout.addWidget(top_bar)

        # Web View (YouTube Engine)
        self.view = QWebEngineView()
        
        # Injected AdBlock & YouTube Auto-Skip Script
        adblock_js = QWebEngineScript()
        adblock_js.setSourceCode("""
            setInterval(() => {
                // Click skip ad buttons instantly
                const skipBtn = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern');
                if (skipBtn) skipBtn.click();

                // Hide video ad banners and overlays
                const ads = document.querySelectorAll('.ad-showing, .ad-interrupting, .ytd-ad-slot-renderer, ytd-display-ad-renderer');
                ads.forEach(ad => ad.style.display = 'none');

                // Fast-forward unskippable ads if they slip through
                const vid = document.querySelector('video');
                const adOverlay = document.querySelector('.ad-showing');
                if (adOverlay && vid && !isNaN(vid.duration)) {
                    vid.muted = true;
                    vid.playbackRate = 16.0;
                    vid.currentTime = vid.duration - 0.1;
                }
            }, 250);
        """)
        adblock_js.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        adblock_js.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        self.view.page().profile().scripts().insert(adblock_js)

        main_layout.addWidget(self.view)

        # Button Connections
        self.btn_back.clicked.connect(self.view.back)
        self.btn_forward.clicked.connect(self.view.forward)
        self.btn_home.clicked.connect(lambda: self.view.setUrl(QUrl("https://www.youtube.com")))

        # Load YouTube directly
        self.view.setUrl(QUrl("https://www.youtube.com"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = ADtubePlayer()
    player.show()
    sys.exit(app.exec())
