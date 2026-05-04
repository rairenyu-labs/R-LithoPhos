"""
LIMA Yes/No Screen (Kiosk UI — Refactored)
==========================================
Home positioning onay ekranı.
Ekranın %25'i boyutunda modal kart tasarımı.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QWidget, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QBrush, QPen, QPixmap
import sys

from StateManager import manager
from styles.theme import ThemeManager, apply_theme


# ─────────────────────────────────────────────────────────────────────────────
# YesNo Modal Card
# ─────────────────────────────────────────────────────────────────────────────

class YesNoCardWidget(QWidget):
    """Glassmorphism tasarımında YesNo onay kartı."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r = ThemeManager.RADIUS * 2

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(16, 16, 30, 245))
        grad.setColorAt(1.0, QColor(8,  8, 18, 245))
        painter.setBrush(QBrush(grad))

        pen = QPen(QColor(0, 200, 240, 50))
        pen.setWidth(1)
        painter.setPen(pen)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        painter.drawRoundedRect(rect, r, r)

        # Üst ışık şeridi
        hl = QLinearGradient(0, 0, self.width(), 0)
        hl.setColorAt(0.0, QColor(0, 200, 255, 0))
        hl.setColorAt(0.5, QColor(0, 200, 255, 18))
        hl.setColorAt(1.0, QColor(0, 200, 255, 0))
        painter.fillRect(QRectF(1, 1, self.width() - 2, 1), QBrush(hl))

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# Ui_YesNoScreen
# ─────────────────────────────────────────────────────────────────────────────

class Ui_YesNoScreen(object):

    def __init__(self):
        pass

    def setupUi(self, YesNoScreen):
        YesNoScreen.setObjectName("YesNoScreen")
        YesNoScreen.setWindowIcon(QtGui.QIcon(manager.get_image_path("mainicon")))
        YesNoScreen.setWindowTitle("LIMA — Home Positioning")

        # ── Tam ekran zemin ──
        screen = QApplication.primaryScreen().availableGeometry()
        YesNoScreen.setGeometry(screen)
        YesNoScreen.showMaximized()

        # ── Merkezi Widget ──
        self.centralwidget = QWidget(YesNoScreen)
        self.centralwidget.setStyleSheet("background-color: #07070F;")
        YesNoScreen.setCentralWidget(self.centralwidget)

        root = QVBoxLayout(self.centralwidget)
        root.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root.addWidget(content)

        outer = QVBoxLayout(content)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Modal Kart: ekranın %25'i ──
        screen_rect = ThemeManager.get_screen_rect()
        cw = int(screen_rect.width() * 0.25)
        ch = int(screen_rect.height() * 0.35)

        center_h = QHBoxLayout()
        center_h.addStretch(1)

        self.card = YesNoCardWidget()
        self.card.setFixedSize(cw, ch)

        card_inner = QVBoxLayout(self.card)
        card_inner.setContentsMargins(28, 24, 28, 24)
        card_inner.setSpacing(0)

        # Logo
        self.logoLabel = QLabel()
        pix = QPixmap(manager.get_image_path("resimLogo"))
        if not pix.isNull():
            self.logoLabel.setPixmap(pix.scaledToHeight(38, Qt.SmoothTransformation))
        self.logoLabel.setAlignment(Qt.AlignCenter)
        self.logoLabel.setStyleSheet("background: transparent; margin-bottom: 4px;")
        card_inner.addWidget(self.logoLabel)

        # Başlık
        self.titleLabel = QLabel("HOME POSITIONING")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("""
            color: rgba(0,200,240,0.85);
            font-size: 14px;
            font-weight: 700;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            letter-spacing: 3px;
            background: transparent;
        """)
        card_inner.addWidget(self.titleLabel)

        # Ayırıcı
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(0,200,240,0.12); border: none; margin: 10px 0;")
        card_inner.addWidget(line)
        card_inner.addSpacing(8)

        # Bilgilendirme metni
        self.informationlabel = QLabel("Initiate positioning sequence?")
        self.informationlabel.setAlignment(Qt.AlignCenter)
        self.informationlabel.setWordWrap(True)
        self.informationlabel.setStyleSheet("""
            color: rgba(160,160,190,0.9);
            font-size: 12px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            background: transparent;
            margin-bottom: 10px;
        """)
        card_inner.addWidget(self.informationlabel)

        card_inner.addStretch(1)

        # Butonlar
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        self.pushButtonYes = QPushButton("✔  YES — Start Positioning")
        self.pushButtonYes.setCursor(Qt.PointingHandCursor)
        self.pushButtonYes.setStyleSheet(ThemeManager.kiosk_start_button_style())
        self.pushButtonYes.clicked.connect(self.openhomebar)
        self.pushButtonYes.clicked.connect(YesNoScreen.close)

        self.pushButtonNo = QPushButton("✕  NO — Skip to Process")
        self.pushButtonNo.setCursor(Qt.PointingHandCursor)
        self.pushButtonNo.setStyleSheet(ThemeManager.kiosk_button_style())
        self.pushButtonNo.clicked.connect(self.openNewWindow)
        self.pushButtonNo.clicked.connect(YesNoScreen.close)

        btn_layout.addWidget(self.pushButtonYes)
        btn_layout.addWidget(self.pushButtonNo)
        card_inner.addLayout(btn_layout)

        center_h.addWidget(self.card)
        center_h.addStretch(1)

        outer.addStretch(1)
        outer.addLayout(center_h)
        outer.addStretch(1)

        # ── Giriş animasyonu ──
        self._fade_in_card()

        self.retranslateUi(YesNoScreen)
        QtCore.QMetaObject.connectSlotsByName(YesNoScreen)

    def _fade_in_card(self):
        effect = QGraphicsOpacityEffect(self.card)
        self.card.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        self._fade_anim = QPropertyAnimation(effect, b"opacity")
        self._fade_anim.setDuration(320)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()

    def openNewWindow(self):
        from Process import Ui_ProcessScreen
        from PyQt5.QtWidgets import QMainWindow
        self.Processwindow = QMainWindow()
        self.ui = Ui_ProcessScreen()
        self.ui.setupUi(self.Processwindow)
        manager.switch_window(self.Processwindow)

    def openhomebar(self):
        from IOtest import HomepositionBar
        self.homeposbar = HomepositionBar()
        manager.switch_window(self.homeposbar)
        self.homeposbar.show()

    def retranslateUi(self, YesNoScreen):
        _translate = QtCore.QCoreApplication.translate
        YesNoScreen.setWindowTitle(_translate("YesNoScreen", "LIMA — Home Positioning"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    YesNoScreen = QMainWindow()
    ui = Ui_YesNoScreen()
    ui.setupUi(YesNoScreen)
    YesNoScreen.show()
    sys.exit(app.exec_())