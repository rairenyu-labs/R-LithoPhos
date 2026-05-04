"""
LIMA NavBar Widget
==================
Her tam ekran penceresinde üstte görünen sabit navigation çubuğu.
40px yüksekliğinde, frameless kiosk modunda bile sabit kalır.

Kullanım:
    from nav_bar import NavBar
    nav = NavBar(parent=self, breadcrumb="Main Menu > Motor Control",
                 show_back=True, back_callback=self.go_back)
    # Pencere layoutunun en üstüne ekle
    main_layout.insertWidget(0, nav)
"""

from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                              QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QColor

import sys
import os
from styles.theme import ThemeManager


class NavBar(QFrame):
    """
    Sabit üst navigasyon çubuğu.

    Sinyaller:
        exit_requested: EXIT butonuna basıldığında yayınlanır.
        back_requested: BACK butonuna basıldığında yayınlanır.
    """

    exit_requested = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, parent=None, breadcrumb: str = "LIMA Control System",
                 show_back: bool = False, back_callback=None,
                 on_exit=None):
        """
        Args:
            parent: Üst widget
            breadcrumb: Ekranın konumunu gösteren metin, örn: "Main Menu > Motor Control"
            show_back: True ise BACK butonu gösterilir
            back_callback: BACK butonuna basıldığında çağrılacak fonksiyon
            on_exit: EXIT butonuna basıldığında çağrılacak fonksiyon
        """
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(ThemeManager.nav_bar_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # ── Sol: BACK butonu (opsiyonel) ──
        if show_back:
            self.back_btn = QPushButton("◀  BACK")
            self.back_btn.setObjectName("NavBackBtn")
            self.back_btn.setFixedWidth(90)
            self.back_btn.setCursor(Qt.PointingHandCursor)
            if back_callback:
                self.back_btn.clicked.connect(back_callback)
            self.back_btn.clicked.connect(self.back_requested.emit)
            layout.addWidget(self.back_btn)
        else:
            layout.addSpacing(4)

        # ── Ortа: Başlık ve breadcrumb ──
        title_layout = QHBoxLayout()
        title_layout.setSpacing(6)

        # LIMA yazısı (vurgulu)
        self.title_label = QLabel("LIMA")
        self.title_label.setObjectName("NavTitle")
        title_layout.addWidget(self.title_label)

        # Breadcrumb ayırıcı
        separator = QLabel("›")
        separator.setObjectName("NavBreadcrumb")
        separator.setStyleSheet("color: rgba(0,242,255,0.4); font-size: 14px; background: transparent;")
        title_layout.addWidget(separator)

        # Breadcrumb metni
        self.breadcrumb_label = QLabel(breadcrumb)
        self.breadcrumb_label.setObjectName("NavBreadcrumb")
        title_layout.addWidget(self.breadcrumb_label)

        layout.addLayout(title_layout)
        layout.addStretch(1)

        # ── Sağ: EXIT butonu ──
        self.exit_btn = QPushButton("✕  EXIT")
        self.exit_btn.setObjectName("NavExitBtn")
        self.exit_btn.setFixedWidth(80)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        if on_exit:
            self.exit_btn.clicked.connect(on_exit)
        self.exit_btn.clicked.connect(self.exit_requested.emit)
        layout.addWidget(self.exit_btn)

    def set_breadcrumb(self, text: str):
        """Breadcrumb metnini günceller."""
        self.breadcrumb_label.setText(text)


class ModalOverlay(QFrame):
    """
    Modal pencereler için arka plan overlay'i.
    Ana pencere üzerine şeffaf karartma efekti uygular.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(0,0,0,0.65);")
        self.hide()

    def show_over(self, parent_widget):
        """Parent'ın tüm alanını kapla."""
        self.setGeometry(parent_widget.rect())
        self.raise_()
        self.show()


def make_fade_animation(widget, start=0.0, end=1.0, duration=280):
    """
    Widget için opacity fade animasyonu döner.

    Args:
        widget: Animasyon uygulanacak QWidget
        start: Başlangıç opacity (0.0-1.0)
        end: Bitiş opacity (0.0-1.0)
        duration: Animasyon süresi (ms)

    Returns:
        QPropertyAnimation nesnesi (henüz başlamadı)
    """
    from PyQt5.QtWidgets import QGraphicsOpacityEffect
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(start)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    return anim


if __name__ == "__main__":
    # Standalone test
    app = QApplication(sys.argv)
    from styles.theme import apply_theme
    apply_theme(app)

    from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
    win = QMainWindow()
    win.resize(800, 100)
    central = QWidget()
    vbox = QVBoxLayout(central)
    vbox.setContentsMargins(0, 0, 0, 0)
    vbox.setSpacing(0)

    nav = NavBar(breadcrumb="Motor Control", show_back=True,
                 on_exit=app.quit)
    vbox.addWidget(nav)

    info = QLabel("NavBar test — LIMA Kiosk System")
    info.setAlignment(Qt.AlignCenter)
    info.setStyleSheet("color: #00f2ff; font-size: 16px; margin: 20px;")
    vbox.addWidget(info)

    win.setCentralWidget(central)
    win.show()
    sys.exit(app.exec_())
