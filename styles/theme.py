"""
LIMA Theme Engine
==================
Merkezi QSS (Qt Style Sheet) tema yönetimi.
Tüm widget stilleri bu modülden yönetilir.
Kiosk boyut hiyerarşisi ve NavBar stilleri dahil.
"""

from PyQt5.QtWidgets import QApplication


class ThemeManager:
    """Merkezi tema yöneticisi."""

    # ── Ortak corner radius sabiti ──────────────────────────────────────────
    RADIUS = 12  # Tüm kartlar ve butonlarda aynı değer

    # ── Renk paleti ───────────────────────────────────────────────────────
    COLORS = {
        'bg_primary':      '#0A0A0F',
        'bg_secondary':    '#12121A',
        'bg_surface':      '#1A1A25',
        'bg_card':         '#141420',
        'border':          '#2A2A3A',
        'border_accent':   '#00f2ff',
        'text_primary':    '#E8E8F0',
        'text_secondary':  '#8888AA',
        'text_disabled':   '#444455',
        'bg_disabled':     '#0E0E18',

        'accent_primary':  '#0078D4',
        'accent_hover':    '#00A2FF',
        'accent_pressed':  '#004578',
        'text_on_accent':  '#FFFFFF',
        'accent_glow':     '#00f2ff',

        'success':         '#00C851',
        'warning':         '#FF8800',
        'error':           '#E81123',
        'danger':          '#E81123',
        'danger_hover':    '#FF3B3B',

        'input_bg':        '#0D0D18',
        'input_border':    '#2A2A3A',
        'input_focus':     '#0078D4',

        'progress_bg':     '#12121A',
        'progress_chunk':  'qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0078D4, stop:1 #00f2ff)',

        'slider_groove':   '#12121A',
        'slider_handle':   'qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #00f2ff, stop:1 #0078D4)',

        'active_button':   '#0078D4',
        'active_text':     '#FFFFFF',

        'motor_bg':        '#12121A',
        'motor_selected':  '#0078D4',
        'motor_border':    '#00f2ff',
        'motor_text':      '#E8E8F0',
        'indicator_on':    '#00f2ff',
        'indicator_off':   '#2A2A3A',

        # NavBar
        'nav_bg':          '#08080F',
        'nav_border':      '#00f2ff',
        'nav_text':        '#A0A0C0',
        'nav_text_active': '#00f2ff',
    }

    # ── Kiosk Boyut Hiyerarşisi ────────────────────────────────────────────

    @staticmethod
    def get_screen_rect():
        """Birincil ekranın geometrisini döner."""
        screen = QApplication.primaryScreen()
        return screen.availableGeometry()

    @classmethod
    def main_card_size(cls):
        """Login / MainMenu kartı boyutu: ekranın %45'i."""
        rect = cls.get_screen_rect()
        w = int(rect.width() * 0.45)
        h = int(rect.height() * 0.52)
        return w, h

    @classmethod
    def modal_card_size(cls):
        """Settings / YesNo modal kartı boyutu: ekranın %28'i."""
        rect = cls.get_screen_rect()
        w = int(rect.width() * 0.28)
        h = int(rect.height() * 0.38)
        return w, h

    @classmethod
    def center_on_screen(cls, window):
        """Pencereyi ekran ortasına yerleştirir."""
        rect = cls.get_screen_rect()
        geo = window.frameGeometry()
        cx = rect.center()
        geo.moveCenter(cx)
        window.move(geo.topLeft())

    # ── Ana stil ──────────────────────────────────────────────────────────
    @classmethod
    def get_app_stylesheet(cls) -> str:
        """Uygulama geneli QSS stylesheet'i."""
        c = cls.COLORS
        r = cls.RADIUS
        return f"""
        /* ═══════════ Genel ═══════════ */
        QMainWindow, QWidget {{
            background-color: {c['bg_primary']};
            color: {c['text_primary']};
            font-family: 'Inter', 'Segoe UI', 'Montserrat', sans-serif;
            font-size: 13px;
        }}

        /* ═══════════ Butonlar ═══════════ */
        QPushButton {{
            background-color: #1E1E2E;
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: {r}px;
            padding: 8px 15px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-weight: 500;
            min-height: 28px;
        }}
        QPushButton:hover {{
            background-color: #272738;
            border: 1px solid {c['accent_glow']};
            color: {c['accent_glow']};
        }}
        QPushButton:pressed {{
            background-color: #0A0A18;
        }}
        QPushButton:disabled {{
            background-color: {c['bg_disabled']};
            color: {c['text_disabled']};
            border-color: {c['border']};
        }}
        QPushButton:checked {{
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 #0078D4, stop:1 #005A9E);
            color: #FFFFFF;
            border: 2px solid {c['accent_glow']};
            border-radius: {r}px;
        }}

        /* ═══════════ Input ═══════════ */
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {c['input_bg']};
            color: {c['accent_glow']};
            border: 1px solid {c['input_border']};
            border-radius: {r}px;
            padding: 6px 10px;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            font-weight: bold;
            font-size: 14px;
            selection-background-color: {c['accent_primary']};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {c['input_focus']};
            background-color: {c['bg_secondary']};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 8px;
        }}

        /* ═══════════ Label ═══════════ */
        QLabel {{
            color: {c['text_secondary']};
            font-size: 13px;
            background: transparent;
        }}

        /* ═══════════ Progress Bar ═══════════ */
        QProgressBar {{
            border: 1px solid {c['border']};
            border-radius: 6px;
            text-align: center;
            background-color: {c['progress_bg']};
            color: #FFF;
            min-height: 20px;
            font-weight: bold;
        }}
        QProgressBar::chunk {{
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                stop:0 #0078D4, stop:1 #00f2ff);
            border-radius: 4px;
        }}

        /* ═══════════ Slider ═══════════ */
        QSlider::groove:horizontal {{
            border: 1px solid {c['border']};
            height: 8px;
            background: {c['slider_groove']};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: {c['slider_handle']};
            border: 1px solid #111;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {c['accent_glow']};
        }}

        /* ═══════════ Scroll Bar ═══════════ */
        QScrollBar:vertical {{
            background: {c['bg_primary']};
            width: 8px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {c['border']};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* ═══════════ Tab Widget ═══════════ */
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            background: {c['bg_primary']};
            border-radius: 4px;
        }}
        QTabBar::tab {{
            background: {c['bg_secondary']};
            color: {c['text_secondary']};
            border: 1px solid {c['border']};
            padding: 8px 18px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {c['accent_primary']};
            color: {c['text_on_accent']};
        }}

        /* ═══════════ MessageBox ═══════════ */
        QMessageBox {{
            background-color: {c['bg_primary']};
        }}
        QMessageBox QLabel {{
            color: {c['text_primary']};
        }}

        /* ═══════════ Frame ═══════════ */
        QFrame {{
            border: none;
        }}

        /* ═══════════ ToolTip ═══════════ */
        QToolTip {{
            background-color: {c['bg_surface']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            padding: 4px;
            border-radius: 4px;
        }}
        """

    # ── Glassmorphism Kart Stili ──────────────────────────────────────────
    @classmethod
    def glass_card_style(cls) -> str:
        """Ana kiosk kartları için glassmorphism stili."""
        c = cls.COLORS
        r = cls.RADIUS
        return f"""
            background: rgba(15, 15, 28, 0.92);
            border: 1px solid rgba(0, 242, 255, 0.25);
            border-radius: {r * 2}px;
        """

    @classmethod
    def glass_card_inner_style(cls) -> str:
        """İç container için transparent arka plan."""
        return "background: transparent; border: none;"

    # ── NavBar Stili ──────────────────────────────────────────────────────
    @classmethod
    def nav_bar_style(cls) -> str:
        """Üstteki sabit NavigationBar için QSS."""
        c = cls.COLORS
        return f"""
            QFrame#NavBar {{
                background-color: {c['nav_bg']};
                border-bottom: 1px solid rgba(0, 242, 255, 0.3);
                border-radius: 0px;
            }}
            QLabel#NavTitle {{
                color: {c['nav_text_active']};
                font-size: 13px;
                font-weight: bold;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                letter-spacing: 2px;
                background: transparent;
            }}
            QLabel#NavBreadcrumb {{
                color: {c['nav_text']};
                font-size: 11px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                background: transparent;
            }}
            QPushButton#NavExitBtn {{
                background: transparent;
                border: 1px solid rgba(232, 17, 35, 0.5);
                border-radius: 6px;
                color: rgba(232, 17, 35, 0.9);
                font-size: 11px;
                font-weight: bold;
                padding: 4px 12px;
                min-height: 24px;
            }}
            QPushButton#NavExitBtn:hover {{
                background: rgba(232, 17, 35, 0.15);
                border-color: #E81123;
                color: #FF4444;
            }}
            QPushButton#NavBackBtn {{
                background: transparent;
                border: 1px solid rgba(0, 242, 255, 0.3);
                border-radius: 6px;
                color: rgba(0, 242, 255, 0.7);
                font-size: 11px;
                padding: 4px 12px;
                min-height: 24px;
            }}
            QPushButton#NavBackBtn:hover {{
                background: rgba(0, 242, 255, 0.1);
                border-color: #00f2ff;
                color: #00f2ff;
            }}
        """

    # ── Kiosk Buton Stili ─────────────────────────────────────────────────
    @classmethod
    def kiosk_button_style(cls) -> str:
        """Ana menü kiosk butonları için büyük, belirgin stil."""
        c = cls.COLORS
        r = cls.RADIUS
        return f"""
            QPushButton {{
                background: rgba(20, 20, 35, 0.8);
                border: 1px solid rgba(0, 242, 255, 0.2);
                border-radius: {r}px;
                color: {c['text_secondary']};
                font-size: 15px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                letter-spacing: 2px;
                min-height: 52px;
                padding: 0px 20px;
            }}
            QPushButton:hover {{
                background: rgba(0, 120, 212, 0.25);
                border: 1px solid {c['accent_glow']};
                color: {c['accent_glow']};
            }}
            QPushButton:pressed {{
                background: rgba(0, 120, 212, 0.4);
            }}
        """

    @classmethod
    def kiosk_start_button_style(cls) -> str:
        """START butonu için özel vurgulu stil."""
        return """
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0A3D6B, stop:1 #051E38);
                border: 1px solid #00f2ff;
                border-radius: 12px;
                color: #00f2ff;
                font-size: 15px;
                font-weight: 700;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                letter-spacing: 3px;
                min-height: 52px;
                padding: 0px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0D5699, stop:1 #0A3D6B);
                border-color: #00f2ff;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background: #051E38;
            }
        """

    @classmethod
    def kiosk_exit_button_style(cls) -> str:
        """EXIT butonu için tehlike stili."""
        return """
            QPushButton {
                background: transparent;
                border: 1px solid rgba(232, 17, 35, 0.4);
                border-radius: 8px;
                color: rgba(232, 17, 35, 0.8);
                font-size: 11px;
                font-weight: bold;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                letter-spacing: 1px;
                padding: 6px 14px;
                min-height: 28px;
            }
            QPushButton:hover {
                background: rgba(232, 17, 35, 0.12);
                border-color: #E81123;
                color: #FF4444;
            }
        """

    # ── Bileşen stilleri ──────────────────────────────────────────────────

    @classmethod
    def motor_button_style(cls) -> str:
        """Motor kontrol butonları için standart sade stil."""
        c = cls.COLORS
        r = cls.RADIUS
        return f"""
        QPushButton {{
            border: 1px solid {c['border']};
            border-radius: {r}px;
            padding: 8px;
            background-color: #1E1E2E;
            color: {c['text_primary']};
            font: bold 12px 'Segoe UI';
        }}
        QPushButton:hover {{
            background-color: #272738;
            border-color: {c['accent_glow']};
        }}
        """

    @classmethod
    def active_button_style(cls) -> str:
        """Aktif (seçili) durumdaki butonlar için stil."""
        return f"""
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
            stop:0 #1A2A40, stop:1 #0D1820);
        color: #00f2ff;
        border: 1px solid #0078D4;
        border-radius: {ThemeManager.RADIUS}px;
        """

    @classmethod
    def danger_button_style(cls) -> str:
        """Tehlike durumu butonları (STOP vb.) için stil."""
        c = cls.COLORS
        r = cls.RADIUS
        return f"""
        QPushButton {{
            background-color: {c['danger']};
            color: white;
            border: 2px solid {c['danger_hover']};
            border-radius: {r}px;
            font-weight: bold;
            padding: 8px;
        }}
        QPushButton:hover {{
            background-color: {c['danger_hover']};
        }}
        """

    @classmethod
    def indicator_style(cls, is_on: bool) -> str:
        """Gösterge (indicator) paneli stili."""
        c = cls.COLORS
        color = c['indicator_on'] if is_on else c['indicator_off']
        return f"background-color: {color}; border-radius: 8px; min-width: 16px; min-height: 16px;"

    @classmethod
    def disabled_button_style(cls) -> str:
        """Devre dışı buton stili."""
        c = cls.COLORS
        r = cls.RADIUS
        return f"background-color: {c['bg_disabled']}; border: 1px solid {c['border']}; border-radius: {r}px; color: {c['text_disabled']};"

    @classmethod
    def enabled_button_style(cls) -> str:
        """Etkin (kapalı) buton stili."""
        r = ThemeManager.RADIUS
        return f"""
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
            stop:0 #111122, stop:1 #080812);
        color: #E0E0E0;
        border: 1px solid #2A2A3A;
        border-radius: {r}px;
        """

    @classmethod
    def selected_motor_button_style(cls) -> str:
        """Seçili motor buton stili."""
        c = cls.COLORS
        r = cls.RADIUS
        return f"color: {c['danger']}; background-color: {c['bg_secondary']}; border: 2px solid {c['danger']}; border-radius: {r}px;"

    @classmethod
    def log_panel_style(cls) -> str:
        """Log paneli stili."""
        c = cls.COLORS
        return f"""
        QTextEdit {{
            background-color: {c['bg_surface']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
            padding: 6px;
        }}
        """


def apply_theme(app):
    """Uygulamaya temayı uygular.

    Args:
        app: QApplication instance
    """
    app.setStyle("Fusion")
    app.setStyleSheet(ThemeManager.get_app_stylesheet())
