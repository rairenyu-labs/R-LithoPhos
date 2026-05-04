"""
LIMA Setup Window (Kiosk UI — Refactored)
==========================================
Ekranın %28'i boyutunda modal kart tasarımı.
Slide-up animasyonla açılır, koyu glassmorphism arka plan.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                              QWidget, QPushButton, QLabel, QGraphicsOpacityEffect,
                              QSizePolicy)
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import (QIODevice, QPropertyAnimation, QUrl, Qt, QEasingCurve,
                           QRectF, QTimer)
from PyQt5.QtGui import (QColor, QLinearGradient, QPainter, QBrush, QPen, QPixmap)
from PyQt5.QtMultimedia import QSoundEffect
import sys

from StateManager import manager
from MotorControl import Ui_MotorControl
from IO import CHOMCHECK
from styles.theme import ThemeManager, apply_theme


# ─────────────────────────────────────────────────────────────────────────────
# Modal Card Widget
# ─────────────────────────────────────────────────────────────────────────────

class ModalCardWidget(QWidget):
    """Glassmorphism tasarımında modal kart."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r = ThemeManager.RADIUS * 2  # 24px

        # Kart gradyanı
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(16, 16, 30, 242))
        grad.setColorAt(1.0, QColor(8,  8, 18, 242))
        painter.setBrush(QBrush(grad))

        pen = QPen(QColor(0, 200, 240, 55))
        pen.setWidth(1)
        painter.setPen(pen)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        painter.drawRoundedRect(rect, r, r)

        # Üst ışık şeridi
        highlight_grad = QLinearGradient(0, 0, self.width(), 0)
        highlight_grad.setColorAt(0.0, QColor(0, 200, 255, 0))
        highlight_grad.setColorAt(0.5, QColor(0, 200, 255, 20))
        highlight_grad.setColorAt(1.0, QColor(0, 200, 255, 0))
        painter.fillRect(QRectF(1, 1, self.width() - 2, 1), QBrush(highlight_grad))

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# Ui_setupwindow
# ─────────────────────────────────────────────────────────────────────────────

class Ui_setupwindow(object):

    def __init__(self):
        self.clickSound = QSoundEffect()
        self.clickSound.setSource(QUrl.fromLocalFile("click.wav"))
        self.clickSound.setVolume(0)
        self.clickSound.play()

    def setupscreenUi(self, setupscreen):
        setupscreen.setObjectName("setupscreen")
        setupscreen.setWindowIcon(QtGui.QIcon(manager.get_image_path("mainicon")))
        setupscreen.setWindowTitle("LIMA — Settings")

        # ── Ekran boyutuna göre boyutlandır (tam ekran kaplayan zemin) ──
        screen = QApplication.primaryScreen().availableGeometry()
        setupscreen.setGeometry(screen)
        setupscreen.showMaximized()

        # ── Merkezi Widget ──
        self.centralwidget = QWidget(setupscreen)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet("background-color: #080810;")
        setupscreen.setCentralWidget(self.centralwidget)

        root_layout = QVBoxLayout(self.centralwidget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── İçerik Katmanı ──
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root_layout.addWidget(content)

        outer = QVBoxLayout(content)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Modal Kartı : Ekranın %28'i ──
        cw, ch = ThemeManager.modal_card_size()

        center_h = QHBoxLayout()
        center_h.addStretch(1)

        self.card = ModalCardWidget()
        self.card.setFixedSize(cw, ch)

        card_inner = QVBoxLayout(self.card)
        card_inner.setContentsMargins(32, 28, 32, 28)
        card_inner.setSpacing(0)

        # Logo
        self.logoLabel = QLabel()
        pix = QPixmap(manager.get_image_path("resimLogo"))
        if not pix.isNull():
            self.logoLabel.setPixmap(pix.scaledToHeight(42, Qt.SmoothTransformation))
        self.logoLabel.setAlignment(Qt.AlignCenter)
        self.logoLabel.setStyleSheet("background: transparent; margin-bottom: 6px;")
        card_inner.addWidget(self.logoLabel)

        # Başlık
        title = QLabel("SETTINGS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: rgba(0,200,240,0.85);
            font-size: 16px;
            font-weight: 700;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            letter-spacing: 4px;
            background: transparent;
            margin-bottom: 6px;
        """)
        card_inner.addWidget(title)

        # Ayırıcı
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(0,200,240,0.12); border: none;")
        card_inner.addWidget(line)
        card_inner.addSpacing(16)

        # Butonlar
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        self.pushButtonMotorControl = QPushButton("⚙  Motor Control")
        self.pushButtonMotorControl.setCursor(Qt.PointingHandCursor)
        self.pushButtonMotorControl.setStyleSheet(ThemeManager.kiosk_button_style())
        self.pushButtonMotorControl.clicked.connect(self.openNewWindow)
        self.pushButtonMotorControl.clicked.connect(setupscreen.hide)
        self.pushButtonMotorControl.clicked.connect(self.add_click_sound)

        self.pushButtonopenCOMCHECK = QPushButton("🔌  COM CHECK")
        self.pushButtonopenCOMCHECK.setCursor(Qt.PointingHandCursor)
        self.pushButtonopenCOMCHECK.setStyleSheet(ThemeManager.kiosk_button_style())
        self.pushButtonopenCOMCHECK.clicked.connect(self.openCOMCHECK)
        self.pushButtonopenCOMCHECK.clicked.connect(setupscreen.hide)
        self.pushButtonopenCOMCHECK.clicked.connect(self.add_click_sound)

        self.backbuttonMainMenu = QPushButton("◀  Back")
        self.backbuttonMainMenu.setCursor(Qt.PointingHandCursor)
        self.backbuttonMainMenu.setStyleSheet(ThemeManager.kiosk_exit_button_style())
        self.backbuttonMainMenu.clicked.connect(setupscreen.close)
        self.backbuttonMainMenu.clicked.connect(self.back_button_Main)
        self.backbuttonMainMenu.clicked.connect(self.add_click_sound)

        for btn in [self.pushButtonMotorControl,
                    self.pushButtonopenCOMCHECK,
                    self.backbuttonMainMenu]:
            btn_layout.addWidget(btn)

        card_inner.addLayout(btn_layout)
        card_inner.addStretch(1)

        center_h.addWidget(self.card)
        center_h.addStretch(1)

        outer.addStretch(1)
        outer.addLayout(center_h)
        outer.addStretch(1)

        # ── Giriş animasyonu (slide-up + fade-in) ──
        self._animate_card_in()

        self.retranslateUi(setupscreen)
        QtCore.QMetaObject.connectSlotsByName(setupscreen)

    # ── Animasyon ────────────────────────────────────────────────────────

    def _animate_card_in(self):
        """Kart slide-up + fade-in animasyonu."""
        # Fade-in
        effect = QGraphicsOpacityEffect(self.card)
        self.card.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        self._fade_anim = QPropertyAnimation(effect, b"opacity")
        self._fade_anim.setDuration(320)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()

    # ── Ses ──────────────────────────────────────────────────────────────

    def add_click_sound(self):
        self.clickSound = QSoundEffect()
        self.clickSound.setSource(QUrl.fromLocalFile("click.wav"))
        self.clickSound.setVolume(1.0)
        self.clickSound.play()

    # ── Navigation ───────────────────────────────────────────────────────

    def openNewWindow(self):
        self.newWindow = Ui_MotorControl()
        manager.switch_window(self.newWindow)

    def openCOMCHECK(self):
        self.CheckHome = CHOMCHECK()
        manager.switch_window(self.CheckHome)

    def back_button_Main(self):
        from MainMenu import Ui_MainWindow
        self.MainWindow = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.MainscreenUi(self.MainWindow)
        manager.switch_window(self.MainWindow)

    def retranslateUi(self, setupscreen):
        _translate = QtCore.QCoreApplication.translate
        setupscreen.setWindowTitle(_translate("setupscreen", "LIMA — Settings"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    setupscreen = QMainWindow()
    ui = Ui_setupwindow()
    ui.setupscreenUi(setupscreen)
    setupscreen.show()
    sys.exit(app.exec_())