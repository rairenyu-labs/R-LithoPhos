"""
LIMA State Manager (Refactored + KioskHost)
============================================
Application-wide singleton: pencere yönetimi + görsel yolları.
Seri port yönetimi artık SerialManager'a devredilmiştir.
KioskHost: Kiosk modunda tek QMainWindow üzerinden fade geçişli navigation.
"""

import sys
import os
from PyQt5.QtCore import QObject, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGraphicsOpacityEffect
from PyQt5.QtGui import QIcon
from serial_manager import serial_mgr


class AppManager(QObject):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self.current_window = None

    # ── Geriye uyumluluk: serialPort property ─────────────────────────────
    @property
    def serialPort(self):
        """Geriye uyumluluk: serial_mgr üzerinden port erişimi."""
        return serial_mgr.port

    # ── Port işlemleri (delege) ───────────────────────────────────────────

    def detect_ports(self):
        """Mevcut seri portları listeler."""
        return serial_mgr.available_ports()

    def connect_port(self, port_name=None, baud_rate=115200):
        """Porta bağlanır."""
        return serial_mgr.connect(port_name, baud_rate)

    def disconnect_port(self):
        """Port bağlantısını kapatır."""
        serial_mgr.disconnect()

    # ── Pencere yönetimi (eski, geriye uyumluluk) ─────────────────────────

    def switch_window(self, next_window_instance):
        """Pencere geçişlerini yönetir (eski API — geriye uyumluluk)."""
        if self.current_window:
            self.current_window.close()
        self.current_window = next_window_instance
        if next_window_instance:
            next_window_instance.show()

    # ── Kaynak yolları ────────────────────────────────────────────────────

    def get_image_path(self, filename):
        """Images klasöründen görsel yolunu döner."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "Images", filename)
        if not os.path.exists(path):
            for ext in ['.png', '.ico', '.jpg']:
                alt_path = path + ext
                if os.path.exists(alt_path):
                    return alt_path
        return path


# Global instance
manager = AppManager()


# ═══════════════════════════════════════════════════════════════════════════
# KioskHost — Tek QMainWindow, Fade Geçişli Ekran Yönetimi
# ═══════════════════════════════════════════════════════════════════════════

class KioskHost(QMainWindow):
    """
    Kiosk modu için tek, kalıcı QMainWindow.

    Tüm ekranlar (MainMenu, SetupWindow, Process…) bu pencerenin
    içine yüklenir; asıl pencere hiçbir zaman kapanmaz.
    Geçişler QPropertyAnimation + QGraphicsOpacityEffect ile fade yapılır.

    Kullanım:
        app = QApplication(sys.argv)
        host = KioskHost()
        host.show()

        # MainMenu'yü yükle
        from MainMenu import MainMenuWidget
        host.navigate_to(MainMenuWidget(host))

        sys.exit(app.exec_())
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("KioskHost")
        self.setWindowTitle("LIMA Control System")
        self.setWindowIcon(QIcon(manager.get_image_path("mainicon")))

        # Boyutları ekrana göre ayarla
        from styles.theme import ThemeManager
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)
        self.showMaximized()

        # Geçiş animasyonu için mevcut widget referansları
        self._current_widget: QWidget | None = None
        self._fade_duration = 280  # ms

        # Boş başlangıç widget'ı
        placeholder = QWidget()
        placeholder.setStyleSheet("background-color: #0A0A0F;")
        self.setCentralWidget(placeholder)

    # ── Animasyonlu ekran geçişi ──────────────────────────────────────────

    def navigate_to(self, new_widget: QWidget, fade_duration: int = None):
        """
        Yeni bir widget'a fade geçişi yapar.

        Args:
            new_widget: Gösterilecek yeni QWidget
            fade_duration: Animasyon süresi (ms); None → varsayılan 280ms
        """
        duration = fade_duration or self._fade_duration

        if self._current_widget is None:
            # İlk ekran — doğrudan göster
            self._show_widget(new_widget)
            return

        old_widget = self._current_widget

        # 1. Eskiyi fade-out et
        fade_out = self._make_opacity_anim(old_widget, start=1.0, end=0.0,
                                           duration=duration // 2)

        def _on_fade_out_done():
            # 2. Yeniyi yerleştir, sıfırdan başlat
            new_widget.setGraphicsEffect(None)  # efekti temizle
            self._show_widget(new_widget)

            # 3. Yeniyi fade-in et
            fade_in = self._make_opacity_anim(new_widget, start=0.0, end=1.0,
                                              duration=duration)
            fade_in.start()
            new_widget._fade_in_anim = fade_in  # GC'ye karşı referans tut

            # Eski widget'ı serbest bırak
            old_widget.deleteLater()

        fade_out.finished.connect(_on_fade_out_done)
        fade_out.start()
        old_widget._fade_out_anim = fade_out  # GC'ye karşı referans tut

    def _show_widget(self, widget: QWidget):
        """Widget'ı setCentralWidget ile ana pencereye yerleştirir."""
        self.setCentralWidget(widget)
        self._current_widget = widget
        widget.show()

    @staticmethod
    def _make_opacity_anim(widget: QWidget, start: float, end: float,
                            duration: int) -> QPropertyAnimation:
        """Verilen widget için opacity animasyonu oluşturur."""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(start)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        return anim

    # ── Exit ──────────────────────────────────────────────────────────────

    def fade_exit(self):
        """Uygulamayı fade-out ile kapatır."""
        if self._current_widget:
            anim = self._make_opacity_anim(self._current_widget,
                                           start=1.0, end=0.0,
                                           duration=400)
            anim.finished.connect(QApplication.quit)
            anim.start()
            self._exit_anim = anim
        else:
            QApplication.quit()
