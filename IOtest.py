"""
LIMA Home Position Bar (Kiosk UI — Refactored)
==============================================
Home positioning takip ekranı.
Ekranın %50'si boyutunda modal kart tasarımı.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QTextEdit, QPushButton, QLineEdit, QComboBox,
                            QLabel, QMessageBox, QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import (QIODevice, pyqtSignal, QObject, QPropertyAnimation, 
                         QUrl, Qt, QEasingCurve, QDateTime, QRectF)
from PyQt5.QtGui import QPixmap, QColor, QFont, QPalette, QLinearGradient, QPainter, QBrush, QPen
from PyQt5.QtMultimedia import QSoundEffect
import sys

from StateManager import manager
from portopen import portConnect
from styles.theme import ThemeManager


class ModalCardWidget(QWidget):
    """Glassmorphism tasarımında Home Position kartı."""
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
        hl = QLinearGradient(0, 0, self.width(), 0)
        hl.setColorAt(0.0, QColor(0, 200, 255, 0))
        hl.setColorAt(0.5, QColor(0, 200, 255, 18))
        hl.setColorAt(1.0, QColor(0, 200, 255, 0))
        painter.fillRect(QRectF(1, 1, self.width() - 2, 1), QBrush(hl))
        painter.end()


class HomepositionBar(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("HomepositionBar")
        self.setWindowTitle("LIMA — Home Positioning")
        self.setWindowIcon(QtGui.QIcon(manager.get_image_path("mainicon")))
        
        # Initialize variables
        self.bufferValuelar = []
        self.buffer = []
        self.bufferStringler = []
        self.commandstring = ''
        self.has_shown_msg = False
        self.log_visible = False
        
        # Initialize components
        self.bufferTxt = QtWidgets.QTextEdit()
        self.comboBox = QComboBox()
        self.serialPort = manager.serialPort
        self.textEditReciveData = QTextEdit()
        
        # Connect signal for port reading
        self.serialPort.readyRead.connect(self.dataReceived)
        
        # Set up click sound
        self.clickSound = QSoundEffect()
        self.clickSound.setSource(QUrl.fromLocalFile(manager.get_image_path("click.wav")))
        self.clickSound.setVolume(1.0)
        
        # Set up UI
        self.setupUI()
        self.portConnectfnTest()
        
        # Start home position timer
        self.timerHOME = QtCore.QTimer()
        self.timerHOME.singleShot(3000, self.HOMESZsend)

    def setupUI(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)
        self.showMaximized()

        self.centralwidget = QWidget(self)
        self.centralwidget.setStyleSheet("background-color: #07070F;")
        self.setCentralWidget(self.centralwidget)

        root = QVBoxLayout(self.centralwidget)
        root.setContentsMargins(0, 0, 0, 0)

        # Arka plan resmi
        self.bg_label = QLabel(self.centralwidget)
        self.bg_label.setGeometry(self.centralwidget.rect())
        pix = QPixmap(manager.get_image_path("558571"))
        if not pix.isNull():
            self.bg_label.setPixmap(pix.scaled(screen.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        self.bg_label.lower()
        self.bg_label.setStyleSheet("opacity: 0.1;")

        content_layout = QVBoxLayout()
        root.addLayout(content_layout)

        # Header: Exit butonu
        header = QHBoxLayout()
        header.setContentsMargins(20, 15, 20, 0)
        header.addStretch()
        self.back_button = QPushButton("✕  ABORT")
        self.back_button.setStyleSheet(ThemeManager.kiosk_exit_button_style())
        self.back_button.clicked.connect(self.open_main_window)
        header.addWidget(self.back_button)
        content_layout.addLayout(header)

        # Modal Kart
        center_h = QHBoxLayout()
        center_h.addStretch(1)

        self.card = ModalCardWidget()
        self.card.setFixedSize(int(screen.width() * 0.55), int(screen.height() * 0.75))
        card_inner = QVBoxLayout(self.card)
        card_inner.setContentsMargins(40, 30, 40, 30)
        card_inner.setSpacing(15)

        # Başlık Bölümü
        title_box = QVBoxLayout()
        main_title = QLabel("HOME POSITIONING")
        main_title.setAlignment(Qt.AlignCenter)
        main_title.setStyleSheet("color: #0088ff; font-size: 20px; font-weight: bold; letter-spacing: 5px;")
        title_box.addWidget(main_title)

        sub_title = QLabel("System Level Synchronization")
        sub_title.setAlignment(Qt.AlignCenter)
        sub_title.setStyleSheet("color: rgba(100,180,240,0.5); font-size: 11px; letter-spacing: 2px;")
        title_box.addWidget(sub_title)
        card_inner.addLayout(title_box)

        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(0,180,255,0.1); margin: 5px 0;")
        card_inner.addWidget(line)

        # Durum Panel Izgarası
        indicators_layout = QtWidgets.QGridLayout()
        indicators_layout.setSpacing(15)
        
        self.create_indicator_panel(indicators_layout, "SXY Status", "labelSXY", 0, 0)
        self.create_indicator_panel(indicators_layout, "SZY Status", "labelSZY", 0, 1)
        self.create_indicator_panel(indicators_layout, "MRXY Status", "labelMRXY", 0, 2)
        self.create_indicator_panel(indicators_layout, "MLXY Status", "labelMLXY", 0, 3)
        self.create_indicator_panel(indicators_layout, "MRZ Status", "labelMRZ", 1, 0)
        self.create_indicator_panel(indicators_layout, "MLZ Status", "labelMLZ", 1, 1)
        self.create_indicator_panel(indicators_layout, "HOME Status", "labelHOME", 1, 2)
        card_inner.addLayout(indicators_layout)

        # Alt Bölüm: İşlem ve Progress
        bottom_box = QVBoxLayout()
        bottom_box.setSpacing(15)

        self.status_text = QLabel("Initializing homing sequence...")
        self.status_text.setAlignment(Qt.AlignCenter)
        self.status_text.setStyleSheet("color: rgba(160,160,190,0.8); font-size: 12px;")
        bottom_box.addWidget(self.status_text)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 200)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #12121A; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0055ff, stop:1 #00f2ff); border-radius: 3px; }
        """)
        bottom_box.addWidget(self.progress_bar)

        self.emergency_btn = QPushButton("⚠  EMERGENCY STOP")
        self.emergency_btn.setCursor(Qt.PointingHandCursor)
        self.emergency_btn.setStyleSheet(ThemeManager.danger_button_style())
        self.emergency_btn.clicked.connect(self.EmergencyStoped)
        self.emergency_btn.clicked.connect(self.add_click_sound)
        bottom_box.addWidget(self.emergency_btn)

        card_inner.addLayout(bottom_box)
        center_h.addWidget(self.card)
        center_h.addStretch(1)

        content_layout.addStretch(1)
        content_layout.addLayout(center_h)
        content_layout.addStretch(1)

        # Log Panel
        self.logTextEdit = QtWidgets.QTextEdit()
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setStyleSheet(ThemeManager.log_panel_style())
        self.logTextEdit.setFixedHeight(100)
        self.logTextEdit.hide()
        content_layout.addWidget(self.logTextEdit)

        # Timer for progress bar
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(150)

        self._fade_in_card()

    def create_indicator_panel(self, parent_layout, title, label_name, row, col):
        panel = QWidget()
        panel.setStyleSheet(f"background: rgba(25, 25, 40, 0.6); border: 1px solid rgba(0,180,255,0.1); border-radius: 12px;")
        p_lay = QVBoxLayout(panel)
        p_lay.setContentsMargins(10, 10, 10, 10)
        
        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Inter", 8, QFont.Bold))
        t_lbl.setStyleSheet("color: rgba(200,200,220,0.6); background: transparent; border: none;")
        t_lbl.setAlignment(Qt.AlignCenter)
        p_lay.addWidget(t_lbl)
        
        setattr(self, label_name, QLabel())
        lbl = getattr(self, label_name)
        lbl.setFixedSize(45, 45)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background: transparent; border: none;")
        p_lay.addWidget(lbl, alignment=Qt.AlignCenter)
        
        parent_layout.addWidget(panel, row, col)

    def _fade_in_card(self):
        effect = QGraphicsOpacityEffect(self.card)
        self.card.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

    def add_click_sound(self):
        self.clickSound.play()

    def update_progress(self):
        val = self.progress_bar.value() + 1
        if val <= 200:
            self.progress_bar.setValue(val)
            if val == 50: self.status_text.setText("Verifying Z-axis limit switches...")
            if val == 120: self.status_text.setText("Calibrating XY stage origin...")
        else:
            self.timer.stop()

    def portConnectfnTest(self):
        portConnect(self)

    def append_log(self, text):
        ts = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.logTextEdit.append(f"[{ts}] {text}")

    def dataReceived(self):
        try:
            raw = self.serialPort.readAll().data().decode("cp1252", errors="ignore")
            # Gelen datayı işleme mantığı (Basitleştirilmiş)
            if "=" in raw:
                cmd = raw.split("=")[0]
                val = raw.split("=")[1][0] if len(raw.split("=")[1]) > 0 else "0"
                self.update_indicator(cmd, [val])
            self.append_log(f"RX: {raw}")
        except Exception as e:
            self.append_log(f"RX Error: {str(e)}")

    def update_indicator(self, command, buffer_values):
        label_map = {
            "SXYHST": "labelSXY", "SZTHST": "labelSZY",
            "MRXYHST": "labelMRXY", "MLXYHST": "labelMLXY",
            "MRZHST": "labelMRZ", "MLZHST": "labelMLZ",
            "HOMESYSHST": "labelHOME"
        }
        if command in label_map:
            lbl = getattr(self, label_map[command])
            pix = QPixmap(manager.get_image_path("green.png" if buffer_values[0] == "1" else "red.png"))
            lbl.setPixmap(pix.scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            if command == "HOMESYSHST" and buffer_values[0] == "1":
                self.status_text.setText("Homing successful. Redirecting...")
                QtCore.QTimer.singleShot(1500, self.open_new_window)

    def HOMESZsend(self):
        try:
            from command_manager import cmd_mgr
            cmd_mgr.home_axis('SYSTEM')
            self.append_log("TX: SYSTEM HOME command sent.")
            self.logTextEdit.show()
        except Exception as e:
            self.append_log(f"TX Error: {str(e)}")

    def EmergencyStoped(self):
        try:
            from command_manager import cmd_mgr
            cmd_mgr.stop(1)
            self.status_text.setText("EMERGENCY STOP ACTIVATED")
            self.status_text.setStyleSheet("color: #ff4444; font-weight: bold;")
        except: pass

    def open_main_window(self):
        from MainMenu import Ui_MainWindow
        self._mm_win = QMainWindow()
        self._mm_ui = Ui_MainWindow()
        self._mm_ui.MainscreenUi(self._mm_win)
        manager.switch_window(self._mm_win)
        self.close()

    def open_new_window(self):
        from Process import Ui_ProcessScreen
        self.proc_win = QMainWindow()
        self.proc_ui = Ui_ProcessScreen()
        self.proc_ui.setupUi(self.proc_win)
        manager.switch_window(self.proc_win)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    from styles.theme import apply_theme
    apply_theme(app)
    window = HomepositionBar()
    window.show()
    sys.exit(app.exec_())