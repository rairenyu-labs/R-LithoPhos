"""
LIMA Main Menu (Kiosk UI — Refactored)
=======================================
Glassmorphism kart tasarımı, ekranın %45'i boyutunda merkezlenmiş.
Hex-pattern arka plan (boron-grafen teması), smooth fade geçişler.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                              QWidget, QPushButton, QLabel, QSizePolicy,
                              QGraphicsOpacityEffect)
from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QLinearGradient, QPen, QBrush
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import (QIODevice, QPropertyAnimation, QUrl, Qt, QEasingCurve,
                           QTimer, QRectF, QPointF, QRect)
import sys
import math

from StateManager import manager
from styles.theme import ThemeManager, apply_theme


# ─────────────────────────────────────────────────────────────────────────────
# Hex Pattern Background Widget
# ─────────────────────────────────────────────────────────────────────────────

class HexPatternWidget(QWidget):
    """
    Düşük opaklıklı boron-grafen hex ağ yapısı arka planı.
    Sanatsal, bilimsel tema için özelleştirilmiş.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Koyu gradient arka plan
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(8, 8, 20))
        grad.setColorAt(0.5, QColor(5, 8, 18))
        grad.setColorAt(1.0, QColor(3, 4, 12))
        painter.fillRect(0, 0, w, h, QBrush(grad))

        # Hex ağ çizimi
        hex_size = 28
        pen = QPen(QColor(0, 180, 220, 22))   # düşük opaklıklı cyan
        pen.setWidth(1)
        painter.setPen(pen)

        col_step = int(hex_size * 1.732)  # √3 * size
        row_step = int(hex_size * 1.5)

        cols = w // col_step + 3
        rows = h // row_step + 3

        for row in range(-1, rows):
            for col in range(-1, cols):
                cx = col * col_step + (hex_size * 0.866 if row % 2 else 0)
                cy = row * row_step

                # Altıgen köşe noktaları
                points = []
                for i in range(6):
                    angle = math.radians(60 * i - 30)
                    px = cx + hex_size * math.cos(angle)
                    py = cy + hex_size * math.sin(angle)
                    points.append(QPointF(px, py))

                # Altıgen kenarları çiz
                for i in range(6):
                    p1 = points[i]
                    p2 = points[(i + 1) % 6]
                    painter.drawLine(p1, p2)

                # Merkez nokta (atom)
                dot_pen = QPen(QColor(0, 220, 255, 30))
                dot_pen.setWidth(3)
                painter.setPen(dot_pen)
                painter.drawPoint(QPointF(cx, cy))
                painter.setPen(pen)

        # Üst kısma hafif ışık huzmesi
        radial_grad = QtGui.QRadialGradient(w * 0.5, h * 0.1, w * 0.6)
        radial_grad.setColorAt(0.0, QColor(0, 120, 212, 18))
        radial_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, QBrush(radial_grad))

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# Main Menu Card Widget
# ─────────────────────────────────────────────────────────────────────────────

class MainMenuCardWidget(QWidget):
    """
    Glassmorphism tasarımıyla ana menü kartı.
    Ekranın %45'i boyutunda, ortalanmış.
    """

    def paintEvent(self, event):
        """Kartın arka planını ve kenarlığını çizer."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r = ThemeManager.RADIUS * 2  # 24px

        # Kart arka planı
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(14, 14, 28, 235))
        grad.setColorAt(1.0, QColor(8,  8, 18, 235))
        painter.setBrush(QBrush(grad))

        # İnce parlak kenarlık
        pen = QPen(QColor(0, 200, 240, 60))
        pen.setWidth(1)
        painter.setPen(pen)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        painter.drawRoundedRect(rect, r, r)

        # Üst kısma parlak şerit (glass highlight)
        highlight_grad = QLinearGradient(0, 0, self.width(), 0)
        highlight_grad.setColorAt(0.0, QColor(0, 200, 255, 0))
        highlight_grad.setColorAt(0.5, QColor(0, 200, 255, 25))
        highlight_grad.setColorAt(1.0, QColor(0, 200, 255, 0))
        painter.fillRect(QRectF(0, 0, self.width(), 2), QBrush(highlight_grad))

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# Ui_MainWindow
# ─────────────────────────────────────────────────────────────────────────────

class Ui_MainWindow(object):

    def __init__(self):
        self.clickSound = QSoundEffect()
        self.clickSound.setSource(QUrl.fromLocalFile("click.wav"))
        self.clickSound.setVolume(0)
        self.clickSound.play()

    def MainscreenUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowIcon(QtGui.QIcon(manager.get_image_path("mainicon")))
        MainWindow.setWindowTitle("LIMA Control System")

        # ── Ekran boyutuna göre pencere boyutlandır ──
        screen = QApplication.primaryScreen().availableGeometry()
        MainWindow.setGeometry(screen)
        MainWindow.showMaximized()

        # ── Merkezi Widget ──
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        # ── Root Layout (tam ekran, stack) ──
        root_layout = QVBoxLayout(self.centralwidget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Hex Pattern Arka Plan ──
        self.bg_widget = HexPatternWidget(self.centralwidget)
        self.bg_widget.setGeometry(self.centralwidget.rect())

        # ── İçerik Katmanı (arka planın üstünde) ──
        self.content_widget = QWidget(self.centralwidget)
        self.content_widget.setStyleSheet("background: transparent;")
        root_layout.addWidget(self.content_widget)

        content_outer = QVBoxLayout(self.content_widget)
        content_outer.setContentsMargins(0, 0, 0, 0)
        content_outer.setSpacing(0)

        # Arka planı içerik üstüne yayıyoruz
        self.bg_widget.lower()

        # ── Üst Bar: sadece EXIT ──
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 14, 20, 0)
        top_bar.addStretch(1)

        self.Exitbutton = QPushButton("✕  EXIT")
        self.Exitbutton.setObjectName("ExitMainBtn")
        self.Exitbutton.setFixedSize(90, 32)
        self.Exitbutton.setCursor(Qt.PointingHandCursor)
        self.Exitbutton.setStyleSheet(ThemeManager.kiosk_exit_button_style())
        self.Exitbutton.clicked.connect(lambda: self.Exitwindow(MainWindow))
        top_bar.addWidget(self.Exitbutton)
        content_outer.addLayout(top_bar)

        # ── Merkez: Kart ──
        center_h = QHBoxLayout()
        center_h.addStretch(1)

        # Kart widget
        cw, ch = ThemeManager.main_card_size()
        self.card = MainMenuCardWidget()
        self.card.setFixedSize(cw, ch)

        card_inner = QVBoxLayout(self.card)
        card_inner.setContentsMargins(40, 32, 40, 32)
        card_inner.setSpacing(0)

        # Logo
        self.logoLabel = QLabel()
        pix = QPixmap(manager.get_image_path("Main_Logo"))
        if not pix.isNull():
            scaled = pix.scaledToHeight(256, Qt.SmoothTransformation)
            self.logoLabel.setPixmap(scaled)
        self.logoLabel.setAlignment(Qt.AlignCenter)
        self.logoLabel.setStyleSheet("background: transparent; margin-bottom: 4px;")
        card_inner.addWidget(self.logoLabel)

        # Başlık
        self.titleLabel = QLabel("LIMA")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("""
            color: #00f2ff;
            font-size: 28px;
            font-weight: 700;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            letter-spacing: 8px;
            background: transparent;
            margin-bottom: 2px;
        """)
        card_inner.addWidget(self.titleLabel)

        # Alt başlık
        self.subTitleLabel = QLabel("Lithography Interface & Motion Automation")
        self.subTitleLabel.setAlignment(Qt.AlignCenter)
        self.subTitleLabel.setStyleSheet("""
            color: rgba(0,180,200,0.6);
            font-size: 10px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            letter-spacing: 2px;
            background: transparent;
            margin-bottom: 20px;
        """)
        card_inner.addWidget(self.subTitleLabel)

        # Ayırıcı çizgi
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(0,200,240,0.15); border: none; margin-bottom: 20px;")
        card_inner.addWidget(line)
        card_inner.addSpacing(12)

        # About içeriği (başlangıçta gizli)
        self.aboutWidget = QWidget()
        self.aboutWidget.setStyleSheet("background: transparent;")
        about_layout = QVBoxLayout(self.aboutWidget)
        about_layout.setContentsMargins(0, 0, 0, 0)

        self.aboutTextLabel = QLabel(
            ""
        )
        self.aboutTextLabel.setWordWrap(True)
        self.aboutTextLabel.setAlignment(Qt.AlignCenter)
        self.aboutTextLabel.setStyleSheet("""
            color: rgba(160,160,180,0.9);
            font-size: 12px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            line-height: 1.6;
            background: transparent;
            padding: 10px;
        """)
        about_layout.addWidget(self.aboutTextLabel)
        self.aboutWidget.setVisible(False)
        card_inner.addWidget(self.aboutWidget)

        # Stack widget (logo ↔ about) — gerekli değil, sadece aboutWidget toggle
        card_inner.addStretch(1)

        # Butonlar
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        self.pushButtonStart = QPushButton("▶  START")
        self.pushButtonStart.setCursor(Qt.PointingHandCursor)
        self.pushButtonStart.setStyleSheet(ThemeManager.kiosk_start_button_style())
        self.pushButtonStart.clicked.connect(
            lambda: self.fadeOutAndOpen(MainWindow, self.openNewWindow))
        self.pushButtonStart.clicked.connect(self.add_click_sound)

        self.pushButtonService = QPushButton("⚙  SETTINGS")
        self.pushButtonService.setCursor(Qt.PointingHandCursor)
        self.pushButtonService.setStyleSheet(ThemeManager.kiosk_button_style())
        self.pushButtonService.clicked.connect(
            lambda: self.fadeOutAndOpen(MainWindow, self.openServiceMenu))
        self.pushButtonService.clicked.connect(self.add_click_sound)

        self.aboutbutton = QPushButton("ℹ  ABOUT")
        self.aboutbutton.setCursor(Qt.PointingHandCursor)
        self.aboutbutton.setStyleSheet(ThemeManager.kiosk_button_style())
        self.aboutbutton.clicked.connect(self.showAboutInformation)
        self.aboutbutton.clicked.connect(self.add_click_sound)

        for btn in [self.pushButtonStart, self.pushButtonService, self.aboutbutton]:
            btn_layout.addWidget(btn)

        card_inner.addLayout(btn_layout)
        card_inner.addSpacing(14)

        # Alt bilgi: "Poke to Select"
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignCenter)

        touch_icon = QLabel()
        touch_pix = QPixmap(manager.get_image_path("touch"))
        if not touch_pix.isNull():
            touch_icon.setPixmap(touch_pix.scaledToHeight(24, Qt.SmoothTransformation))
        touch_icon.setStyleSheet("background: transparent;")
        footer_layout.addWidget(touch_icon)

        poke_label = QLabel("Poke to Select")
        poke_label.setStyleSheet("color: rgba(100,100,130,0.8); font-size: 10px; "
                                  "background: transparent; margin-left: 6px;")
        footer_layout.addWidget(poke_label)
        card_inner.addLayout(footer_layout)

        center_h.addWidget(self.card)
        center_h.addStretch(1)

        content_outer.addStretch(1)
        content_outer.addLayout(center_h)
        content_outer.addStretch(1)

        # ── Giriş fade-in animasyonu ──
        self._card_fade_in()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    # ── Arka plan boyut senkronizasyonu ──────────────────────────────────

    def _resize_bg(self, size):
        if hasattr(self, 'bg_widget'):
            self.bg_widget.setGeometry(0, 0, size.width(), size.height())

    # ── Card Fade-In ─────────────────────────────────────────────────────

    def _card_fade_in(self):
        effect = QGraphicsOpacityEffect(self.card)
        self.card.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        self._entry_anim = QPropertyAnimation(effect, b"opacity")
        self._entry_anim.setDuration(600)
        self._entry_anim.setStartValue(0.0)
        self._entry_anim.setEndValue(1.0)
        self._entry_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._entry_anim.start()

    # ── Fade Out & Open ───────────────────────────────────────────────────

    def fadeOutAndOpen(self, MainWindow, nextFunction):
        self.fadeWidget = QWidget(MainWindow)
        self.fadeWidget.setStyleSheet("background-color: #0A0A0F;")
        self.fadeWidget.setGeometry(0, 0, MainWindow.width(), MainWindow.height())
        self.fadeEffect = QGraphicsOpacityEffect(self.fadeWidget)
        self.fadeWidget.setGraphicsEffect(self.fadeEffect)
        self.fadeEffect.setOpacity(0)
        self.fadeWidget.show()
        self.fadeWidget.raise_()

        self.animation = QPropertyAnimation(self.fadeEffect, b"opacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InQuad)
        self.animation.finished.connect(lambda: self.finishFadeOut(MainWindow, nextFunction))
        self.animation.start()

    def finishFadeOut(self, MainWindow, nextFunction):
        MainWindow.hide()
        nextFunction()
        if hasattr(self, 'fadeWidget'):
            self.fadeWidget.deleteLater()

    def Exitwindow(self, MainWindow):
        self.fadeWidget = QWidget(MainWindow)
        self.fadeWidget.setStyleSheet("background-color: #0A0A0F;")
        self.fadeWidget.setGeometry(0, 0, MainWindow.width(), MainWindow.height())
        self.fadeEffect = QGraphicsOpacityEffect(self.fadeWidget)
        self.fadeWidget.setGraphicsEffect(self.fadeEffect)
        self.fadeEffect.setOpacity(0)
        self.fadeWidget.show()
        self.fadeWidget.raise_()

        self.animation = QPropertyAnimation(self.fadeEffect, b"opacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InQuad)
        self.animation.finished.connect(MainWindow.close)
        self.animation.start()

    # ── Ses ──────────────────────────────────────────────────────────────

    def add_click_sound(self):
        self.clickSound = QSoundEffect()
        self.clickSound.setSource(QUrl.fromLocalFile("click.wav"))
        self.clickSound.setVolume(1.0)
        self.clickSound.play()

    # ── Navigation ───────────────────────────────────────────────────────

    def openNewWindow(self):
        from YesNo import Ui_YesNoScreen
        self.YesNoScreen = QMainWindow()
        self.ui = Ui_YesNoScreen()
        self.ui.setupUi(self.YesNoScreen)
        manager.switch_window(self.YesNoScreen)

    def showAboutInformation(self):
        visible = self.aboutWidget.isVisible()
        self.aboutWidget.setVisible(not visible)
        if not visible:
            self.aboutbutton.setText("ℹ  ABOUT  ▲")
        else:
            self.aboutbutton.setText("ℹ  ABOUT")

    def openServiceMenu(self):
        from SetupWindow import Ui_setupwindow
        self.setupwindow = QMainWindow()
        self.ui = Ui_setupwindow()
        self.ui.setupscreenUi(self.setupwindow)
        manager.switch_window(self.setupwindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "LIMA Control System"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.MainscreenUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())