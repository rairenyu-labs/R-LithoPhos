"""
LIMA Motor Control (Refactored)
================================
Tüm motor, valf, home, hız, exposure komutları modüler yapıda.
Seri iletişim: CommandManager → SerialManager → Binary Protocol
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QTextEdit, QPushButton, QLineEdit, QMessageBox, QGridLayout, QLabel,
    QLCDNumber, QProgressBar, QSlider, QFrame, QSizePolicy, QComboBox, QStackedWidget)
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import (QIODevice, pyqtSignal, QObject, Qt, QThread,
    QCoreApplication, QMetaObject, QPoint, QSize, QUrl, QRect, QTimer)
from PyQt5.QtGui import QImage, QPixmap, QPalette
import sys, time

from protocol import LimaCommand
from serial_manager import serial_mgr
from command_manager import cmd_mgr
from portopen import portConnect
from StateManager import manager
from styles.theme import ThemeManager
from nav_bar import NavBar


class Ui_MotorControl(QMainWindow):

    def __init__(self):
        super().__init__()
        self.comboBox = QComboBox()
        self.serialPort = manager.serialPort

        if self.serialPort.isOpen():
            self.serialPort.clear()
        self.buffer = []
        # (Eski sistem, silebilirsin de)
        self.rx_buffer = bytearray() # YENİ: Binary verileri biriktireceğimiz havuz
        self.bufferStringler = []
        self.bufferValuelar = []
        self.commandstring = ''
        self.COMcheck = ["MASKVAC","MSKHVAC","SAMPVAC","SMPHVAC","VRINGVAC","CONTVAC","",""]

        # Position buffers as QTextEdit for UI display
        self._pos_buffers = {}
        for name in ['SYPOS','SXPOS','STPOS','SZPOS','MRXPOS','MRYPOS',
                      'MLXPOS','MLYPOS','MRZPOS','MLZPOS','Energy','Power','Txt']:
            te = QtWidgets.QTextEdit()
            setattr(self, f'buffer{name}', te)
            te.setStyleSheet("background-color: #FFFFEE; color: #B30000; border: 2px solid #FF5050; border-radius: 4px; font-weight: bold; font-size: 15px; padding: 2px;")
            self._pos_buffers[name] = te

        self.is_forward = False 
        self.slider_value = 0
        self.setupUi(self)

        # Hook up logging and standby tracking
        cmd_mgr.log_callback = self._on_cmd_sent

        self.showMaximized()
        self.setWindowTitle("LIMA — Motor Control")

        # ── NavBar eklentisi ──────────────────────────────────────────
        self._nav_bar = NavBar(
            self,
            breadcrumb="Motor Control",
            show_back=True,
            back_callback=self.back_button_setup,
            on_exit=self.close,
        )
        # NavBar'ı en üste, mevcut tüm widget'ların önüne yerleştir
        self._nav_bar.setParent(self.centralwidget)
        self._nav_bar.move(0, 0)
        self._nav_bar.resize(self.centralwidget.width(), 44)
        self._nav_bar.raise_()
        self._nav_bar.show()
        # ─────────────────────────────────────────────────────────────

        self.portConnectfnTest()

        # Start cameras
        self.start_camera()
        self.start_camera2()

    def _on_cmd_sent(self, msg):
        self._log_message("OUT", msg)
        # Apply waiting state to label if command corresponds to one
        cmd_name = msg.split()[0]
        reply_key = self.CMD_TO_REPLY.get(cmd_name)
        if reply_key:
            label_attr = self.INDICATORS_MAP.get(reply_key)
            if label_attr:
                self._set_waiting_state(label_attr)

    def _set_waiting_state(self, label_attr):
        label = getattr(self, label_attr, None)
        if not label: return
        label.setText("...WAIT...")
        label.setStyleSheet("color: #ff9900; font-weight: bold;")
        
        # 2 saniye timeout — cevap gelmezse kırmızı göster
        def check_timeout():
            if label.text() == "...WAIT...":
                red_path = manager.get_image_path("red") if hasattr(manager, 'get_image_path') else "red.png"
                pix = QtGui.QPixmap(red_path)
                label.setText("")
                label.setStyleSheet("")
                if not pix.isNull():
                    label.setPixmap(pix)
                    label.setAlignment(Qt.AlignCenter)
                else:
                    label.setText("✗")
                    label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        QTimer.singleShot(2000, check_timeout)



    def portConnectfnTest(self):
        portConnect(self)

    CMD_TO_REPLY = {
        'MASKVSEL': 'MASKVAC', 'SAMPVSEL': 'SAMPVAC', 'SAMPHVSEL': 'SAMPHVAC',
        'HARDCONTACTSEL': 'HARDCONTACTVAC', 'SAMPFVSEL': 'SAMPFVAC', 'CONVSEL': 'CONTVAC',
        'WECLSEL': 'WECLOCK', 'OPTICSEL': 'OPTICSEL', 'RINGSEL': 'RINGSEL',
        'HOMESX': 'HOMESXOK', 'HOMESY': 'HOMESYOK', 'HOMESZ': 'HOMESZOK',
        'HOMESTH': 'HOMESTHOK', 'HOMEMRX': 'HOMEMRXOK', 'HOMEMRY': 'HOMEMRYOK',
        'HOMEMLX': 'HOMEMLXOK', 'HOMEMLY': 'HOMEMLYOK', 'HOMEMRZ': 'HOMEMRZOK',
        'HOMEMLZ': 'HOMEMLZOK', 'HOMESXY': 'HOMESXYOK', 'HOMEMRXY': 'HOMEMRXYOK',
        'HOMEMLXY': 'HOMEMLXYOK', 'HOMESYSTM': 'HOMESYSTMOK',
        'KEEPHPOS': 'KEEPHSTAT', 'CONTPOS': 'CONTPSTAT',
        'GAP': 'GAPPOSSTAT',
    }

    INDICATORS_MAP = {
        **{
            'HOMESXOK': 'image_labelHOMESX', 'HOMESYOK': 'image_labelHOMESY',
            'HOMESZOK': 'image_labelHOMESZ', 'HOMESTHOK': 'image_labelHOMESTH',
            'HOMEMRXOK': 'image_labelHOMEMRX', 'HOMEMRYOK': 'image_labelHOMEMRY',
            'HOMEMLXOK': 'image_labelHOMEMLX', 'HOMEMLYOK': 'image_labelHOMEMLY',
            'HOMEMRZOK': 'image_labelHOMEMRZ', 'HOMEMLZOK': 'image_labelHOMEMLZ',
            'HOMESXYOK': 'image_labelHOMESXY', 'HOMEMRXYOK': 'image_labelHOMEMRXY',
            'HOMEMLXYOK': 'image_labelHOMEMLXY',
            'HOMESYSTMOK': 'image_labelHOMESTH2',  # HomeAxis13 → HOMESYSTM → STH2 label
        },
        **{
            'MASKVAC': 'image_labelMASKVAC', 'MASKHVAC': 'image_labelMSKHVAC', 'HARDCONTACTVAC': 'image_labelMSKHVAC',
            'SAMPVAC': 'image_labelSAMPVAC', 'SAMPHVAC': 'image_labelSMPHVAC',
            'WECLOCK': 'image_labelWECSEL', 'CONTVAC': 'image_labelCONTVAC',
            'SAMPFVAC': 'image_labelSAMPFSEL', 'OPTICSEL': 'image_labelOPTIVAC',
            'RINGSEL': 'image_labelRINGSEL',
        },
        **{
            'KEEPHSTAT': 'image_labelKEEPHSTAT',
            'CONTPSTAT': 'image_labelCONTPSTAT',
            'GAPPOSSTAT': 'image_labelGAPPOSSTAT',
        }
    }

    # ═══════════ Merkezi Yardımcı Fonksiyonlar ═══════════

    def _log_message(self, direction, msg):
        import html as html_lib
        if not hasattr(self, 'mainLogBox'):
            return
        time_str = QtCore.QTime.currentTime().toString("HH:mm:ss.zzz")
        
        # Oku yönlerini (<< ve >>) HTML entities olarak tanımla
        # Yoksa QTextEdit "<<" işaretini HTML tag başlangıcı sanıp tüm metni yutuyor!
        prefix = "&gt;&gt; OUT:" if direction == "OUT" else "&lt;&lt; IN:"
        color = "#00bbff" if direction == "OUT" else "#00ee00"
        
        # HTML tag olarak algılanmaması için escape ediyoruz
        safe_msg = html_lib.escape(str(msg))
        
        html_str = f'<span style="color:{color}; font-weight:bold;">[{time_str}] {prefix} {safe_msg}</span>'
        self.mainLogBox.append(html_str)
        # Scroll to bottom
        scrollbar = self.mainLogBox.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _get_input_value(self, line_edit, label="Position"):
        """LineEdit'ten int değer okur, boşsa uyarı gösterir."""
        text = line_edit.text()
        if not text:
            msg = QMessageBox()
            msg.setText(f"{label} Değeri Girmediniz")
            msg.setWindowTitle("Hata")
            msg.exec_()
            return 0
        return int(text)

    def _send_cmd(self, cmd_name, value=1):
        """Tek satırda komut gönderir."""
        cmd_mgr.send(cmd_name, value)

    # ═══════════ Hız & Işık Kontrolleri ═══════════

    def update_progress_bar(self, value):
        sender = self.sender()
        if isinstance(sender, QSlider):
            if sender.isSliderDown():
                self.slider_value = value
            else:
                mapping = {
                    self.slider_3: self.progress_bar_3,
                    self.slider_4: self.progress_bar_4,
                    self.slider_Light: self.progress_bar_Light,
                }
                if hasattr(self, 'slider_Light2'):
                    mapping[self.slider_Light2] = self.progress_bar_Light2
                bar = mapping.get(sender)
                if bar:
                    bar.setValue(self.slider_value)

    def update_motor_speed4(self, value):
        self.progress_bar_4.setValue(value)
        cmd_mgr.set_speed('SXY', value * 0x64 // 100)

    def update_motor_speed3(self, value):
        self.progress_bar_3.setValue(value)
        cmd_mgr.set_speed('MIC', value * 0x64 // 100)

    def update_Light_degree(self, value):
        self.progress_bar_Light.setValue(value)
        cmd_mgr.set_light(value * 0x64 // 100)

    def update_Light2_degree(self, value):
        self.progress_bar_Light2.setValue(value)
        cmd_mgr.set_light(value * 0x64 // 100)

    # ═══════════ Buton Görünürlük Yönetimi ═══════════

    def _get_all_direction_buttons(self):
        return [
            self.zed_up_button, self.zed_down_button,
            self.MicroL_left_button, self.MicroL_right_button,
            self.sample_down_button, self.sample_left_button,
            self.sample_right_button, self.sample_up_button,
            self.MicroS_down_button, self.MicroS_up_button,
            self.Theta_left_button, self.Theta_right_button,
            self.MicroS_right_button, self.MicroS_left_button,
            self.MicroL_up_button, self.MicroL_down_button,
            self.MicroLZed_up_button, self.MicroLZed_down_button,
            self.MicroRZed_up_button, self.MicroRZed_down_button,
        ]

    def _get_motor_buttons(self):
        return [self.Zed_button, self.sample_button, self.MicroL_button,
                self.MicroS_button, self.Theta_button, self.MicroLZed,
                self.MicroRZed, self.back_button]

    def possitionhide(self):
        if self.possition_button.isChecked():
            for btn in self._get_all_direction_buttons():
                if hasattr(btn, 'setVisible'): btn.setVisible(False)

    def distancehide(self):
        if self.distance_button.isChecked():
            for btn in self._get_all_direction_buttons():
                if hasattr(btn, 'setVisible'): btn.setVisible(False)

    def ButtonDisable(self):
        motor_btns = self._get_motor_buttons()
        checked = None
        for b in motor_btns:
            if b.isChecked():
                checked = b
                break
                
        for b in motor_btns:
            if checked and b != checked:
                b.setEnabled(False)
            else:
                b.setEnabled(True)

    def button_check(self):
        buttons = self._get_all_direction_buttons()
        selected = None
        for b in buttons:
            if b.isChecked():
                selected = b
                break
        for b in buttons:
            b.setEnabled(b == selected or selected is None)

    def button_check_Move(self):
        buttons = [self.limit_button, self.distance_button, self.possition_button]
        selected = None
        for b in buttons:
            if b.isChecked():
                selected = b
                break
        for b in buttons:
            b.setEnabled(b == selected or selected is None)

    def button_check_Movedetail(self):
        self._move_detail_logic(self.distance_button)

    def button_check_Movedetail2(self):
        self._move_detail_logic(self.possition_button)

    def _move_detail_logic(self, target_btn):
        buttons = [self.distance_button, self.possition_button]
        selected = None
        for b in buttons:
            if b.isChecked():
                selected = b
                break
        for b in buttons:
            b.setEnabled(b == selected or selected is None)
        motor_btns = [self.MicroLZed, self.MicroRZed, self.MicroL_button,
                      self.MicroS_button, self.Theta_button, self.sample_button, self.Zed_button]
        for mb in motor_btns:
            if mb.isChecked():
                target_btn.setVisible(True)
                target_btn.setEnabled(True)
                mb.setEnabled(not target_btn.isChecked())

    # ═══════════ Motor Buton Toggle'ları ═══════════

    def _toggle_motor_buttons(self, btn_list, main_btn, active_style=None):
        visible = not btn_list[0].isVisible()
        for b in btn_list:
            b.setVisible(visible)

    def zed_button_clicked(self):
        self._toggle_motor_buttons([self.zed_up_button, self.zed_down_button], self.Zed_button)

    def sample_button_clicked(self):
        self._toggle_motor_buttons([self.sample_up_button, self.sample_down_button,
            self.sample_left_button, self.sample_right_button], self.sample_button)

    def MicroL_button_clicked(self):
        self._toggle_motor_buttons([self.MicroL_right_button, self.MicroL_left_button,
            self.MicroL_down_button, self.MicroL_up_button], self.MicroL_button)

    def MicroS_button_clicked(self):
        self._toggle_motor_buttons([self.MicroS_up_button, self.MicroS_down_button,
            self.MicroS_left_button, self.MicroS_right_button], self.MicroS_button)

    def MicroLZed_button_clicked(self):
        self._toggle_motor_buttons([self.MicroLZed_up_button, self.MicroLZed_down_button], self.MicroLZed)

    def MicroRZed_button_clicked(self):
        self._toggle_motor_buttons([self.MicroRZed_up_button, self.MicroRZed_down_button], self.MicroRZed)

    def Theta_button_clicked(self):
        self._toggle_motor_buttons([self.Theta_right_button, self.Theta_left_button], self.Theta_button)

    # ═══════════ Jog Komutları (Modüler) ═══════════

    def _jog_handler(self, button, axis, direction, icon_active, icon_inactive):
        """Genel jog buton handler. Basılıysa hareket, bırakılırsa STOP."""
        if button.isChecked():
            if direction == 'P':
                cmd_mgr.jog_positive(axis)
            else:
                cmd_mgr.jog_negative(axis)
            button.setIcon(QtGui.QIcon(manager.get_image_path(icon_active)))
        else:
            cmd_mgr.stop()
            button.setIcon(QtGui.QIcon(manager.get_image_path(icon_inactive)))

    def _position_distance_handler(self, axis, line_edit, mode_btn, pos_cmd, dist_cmd, pos_label="Position"):
        """Position veya Distance modunda komut gönderir."""
        if self.possition_button.isChecked():
            val = self._get_input_value(line_edit, pos_label)
            cmd_mgr.send(pos_cmd, val)
        elif self.distance_button.isChecked():
            val = self._get_input_value(line_edit, "Distance")
            cmd_mgr.send(dist_cmd, val)

    # ── Sample ──
    def portSendDataSampleYP(self):
        if self.sample_up_button.isChecked() and self.possition_button.isChecked():
            val_y = self._get_input_value(self.lineEditSendData_2)
            cmd_mgr.set_mpos('SY', val_y)
            val_x = self._get_input_value(self.lineEditSendData)
            cmd_mgr.set_mpos('SX', val_x)
            cmd_mgr.move_to_position('SXY', val_x)
        elif self.sample_up_button.isChecked() and self.distance_button.isChecked():
            val_y = self._get_input_value(self.lineEditSendData_2, "Distance")
            cmd_mgr.set_gpos('SY', val_y)
            val_x = self._get_input_value(self.lineEditSendData, "Distance")
            cmd_mgr.set_gpos('SX', val_x)
            cmd_mgr.send('GOSXY', val_x)
        elif self.sample_up_button.isChecked():
            self._jog_handler(self.sample_up_button, 'SY', 'P', "redup", "uparrow2")
        else:
            cmd_mgr.stop()
            self.sample_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.sample_up_button

    def portSendDataSampleYN(self):
        self._jog_handler(self.sample_down_button, 'SY', 'N', "reddown", "downarrow2")

    def portSendDataSampleXP(self):
        self._jog_handler(self.sample_right_button, 'SX', 'P', "redright", "rightarrow2")

    def portSendDataSampleXN(self):
        self._jog_handler(self.sample_left_button, 'SX', 'N', "redleft", "leftarrow2")

    # ── Micro Right (S) ──
    def portSendDataMicRightYP(self):
        if self.MicroS_up_button.isChecked() and self.possition_button.isChecked():
            cmd_mgr.set_mpos('MRY', self._get_input_value(self.lineEditSendData_2))
            cmd_mgr.set_mpos('MRX', self._get_input_value(self.lineEditSendData))
            cmd_mgr.move_to_position('MR', self._get_input_value(self.lineEditSendData))
        elif self.MicroS_up_button.isChecked() and self.distance_button.isChecked():
            cmd_mgr.set_gpos('MRY', self._get_input_value(self.lineEditSendData_2, "Distance"))
            cmd_mgr.set_gpos('MRX', self._get_input_value(self.lineEditSendData, "Distance"))
            cmd_mgr.go_distance('MR', self._get_input_value(self.lineEditSendData))
        elif self.MicroS_up_button.isChecked():
            self._jog_handler(self.MicroS_up_button, 'MRY', 'P', "redup", "uparrow2")
        else:
            cmd_mgr.stop()
            self.MicroS_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.MicroS_up_button

    def portSendDataMicroSXN(self):
        self._jog_handler(self.MicroS_left_button, 'MRX', 'N', "redleft", "leftarrow2")

    def portSendDataMicRightXP(self):
        self._jog_handler(self.MicroS_right_button, 'MRX', 'P', "redright", "rightarrow2")

    def portSendDataMicRightYN(self):
        self._jog_handler(self.MicroS_down_button, 'MRY', 'N', "reddown", "downarrow2")

    # ── Micro Left ──
    def portSendDataMicLeftYP(self):
        if self.MicroL_up_button.isChecked() and self.possition_button.isChecked():
            cmd_mgr.set_mpos('MLY', self._get_input_value(self.lineEditSendData_2))
            cmd_mgr.set_mpos('MLX', self._get_input_value(self.lineEditSendData))
            cmd_mgr.move_to_position('ML', self._get_input_value(self.lineEditSendData))
        elif self.MicroL_up_button.isChecked() and self.distance_button.isChecked():
            cmd_mgr.set_gpos('MLY', self._get_input_value(self.lineEditSendData_2, "Distance"))
            cmd_mgr.set_gpos('MLX', self._get_input_value(self.lineEditSendData, "Distance"))
            cmd_mgr.go_distance('ML', self._get_input_value(self.lineEditSendData))
        elif self.MicroL_up_button.isChecked():
            self._jog_handler(self.MicroL_up_button, 'MLY', 'P', "redup", "uparrow2")
        else:
            cmd_mgr.stop()
            self.MicroL_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.MicroL_up_button

    def portSendDataMicLeftYN(self):
        self._jog_handler(self.MicroL_down_button, 'MLY', 'N', "reddown", "downarrow2")

    def portSendDataMicLeftXN(self):
        self._jog_handler(self.MicroL_left_button, 'MLX', 'N', "redleft", "leftarrow2")

    def portSendDataMicLeftXP(self):
        self._jog_handler(self.MicroL_right_button, 'MLX', 'P', "redright", "rightarrow2")

    # ── Micro Right Zed ──
    def portSendDataMicRightZedYP(self):
        if self.MicroRZed_up_button.isChecked() and self.possition_button.isChecked():
            cmd_mgr.move_to_position('MRZ', self._get_input_value(self.lineEditSendData_2))
        elif self.MicroRZed_up_button.isChecked() and self.distance_button.isChecked():
            cmd_mgr.go_distance('MRZ', self._get_input_value(self.lineEditSendData_2, "Distance"))
        else:
            self._jog_handler(self.MicroRZed_up_button, 'MRZ', 'P', "redup", "uparrow2")

    def portSendDataMicRightZedYN(self):
        self._jog_handler(self.MicroRZed_down_button, 'MRZ', 'N', "reddown", "downarrow2")

    # ── Micro Left Zed ──
    def portSendDataMicLeftZedYP(self):
        if self.MicroLZed_up_button.isChecked() and self.possition_button.isChecked():
            cmd_mgr.move_to_position('MLZ', self._get_input_value(self.lineEditSendData))
        elif self.MicroLZed_up_button.isChecked() and self.distance_button.isChecked():
            cmd_mgr.go_distance('MLZ', self._get_input_value(self.lineEditSendData, "Distance"))
        else:
            self._jog_handler(self.MicroLZed_up_button, 'MLZ', 'P', "redup", "uparrow2")

    def portSendDataMicLeftZedYN(self):
        self._jog_handler(self.MicroLZed_down_button, 'MLZ', 'N', "reddown", "downarrow2")

    # ── Theta ──
    def portSendDataThetaXP(self):
        if self.Theta_right_button.isChecked() and self.possition_button.isChecked():
            cmd_mgr.move_to_position('STH', self._get_input_value(self.lineEditSendData))
        elif self.Theta_right_button.isChecked() and self.distance_button.isChecked():
            cmd_mgr.go_distance('STH', self._get_input_value(self.lineEditSendData, "Distance"))
        else:
            self._jog_handler(self.Theta_right_button, 'STH', 'P', "redright", "rightarrow2")

    def portSendDataThetaXN(self):
        if self.Theta_left_button.isChecked() and self.possition_button.isChecked():
            cmd_mgr.move_to_position('STH', self._get_input_value(self.lineEditSendData))
        elif self.Theta_left_button.isChecked() and self.distance_button.isChecked():
            cmd_mgr.go_distance('STH', self._get_input_value(self.lineEditSendData, "Distance"))
        else:
            self._jog_handler(self.Theta_left_button, 'STH', 'N', "redleft", "leftarrow2")

    # ── Zed ──
    def portSendDataZedYP(self):
        if self.zed_up_button.isChecked() and self.possition_button.isChecked():
            cmd_mgr.move_to_position('SZ', self._get_input_value(self.lineEditSendData))
        elif self.zed_up_button.isChecked() and self.distance_button.isChecked():
            cmd_mgr.go_distance('SZ', self._get_input_value(self.lineEditSendData, "Distance"))
        else:
            self._jog_handler(self.zed_up_button, 'SZ', 'P', "redup", "uparrow2")

    def portSendDataZedYN(self):
        self._jog_handler(self.zed_down_button, 'SZ', 'N', "reddown", "downarrow2")

    # ── Mic-Op ──
    def portSendDataMic_Op(self):
        val = int(self.lineEditSendData.text())
        cmd_mgr.send('YP', val)

    # ═══════════ Hız Modu Butonları ═══════════

    def portSendDataSampleSlow(self):
        cmd_mgr.set_speed('SAMPLE', 1 if self.button_SampleSlow.isChecked() else 0)

    def portSendDataSampleFast(self):
        cmd_mgr.set_speed('SAMPLE', 1 if self.button_SampleFast.isChecked() else 0)

    def portSendDataMicroSlow(self):
        cmd_mgr.set_speed('MICRO', 1 if self.button_MicroSlow.isChecked() else 0)

    def portSendDataMicroFast(self):
        cmd_mgr.set_speed('MICRO', 1 if self.button_MicroFast.isChecked() else 0)

    # ═══════════ Valf Butonları (Modüler) ═══════════

    _valve_map = {
        'send_butonValfler':  'MASKVSEL',   'send_butonValfler1': 'SAMPVSEL',
        'send_butonValfler2': 'SAMPHVSEL',  'send_butonValfler3': 'HARDCONTACTSEL',
        'send_butonValfler4': 'SAMPFVSEL',  'send_butonValfler5': 'CONVSEL',
        'send_butonValfler6': 'WECLSEL',    'send_butonValfler7': 'OPTICSEL',
        'send_butonValfler8': 'RINGSEL',
    }

    def _valve_handler(self, btn, cmd_name):
        val = 1 if btn.isChecked() else 0
        cmd_mgr.send(cmd_name, val)
        

    def send_butonValfler(self):  self._valve_handler(self.button_valfler, 'MASKVSEL')
    def send_butonValfler1(self): self._valve_handler(self.button_valfler1, 'SAMPVSEL')
    def send_butonValfler2(self): self._valve_handler(self.button_valfler2, 'SAMPHVSEL')
    def send_butonValfler3(self): self._valve_handler(self.button_valfler3, 'HARDCONTACTSEL')
    def send_butonValfler4(self): self._valve_handler(self.button_valfler4, 'SAMPFVSEL')
    def send_butonValfler5(self): self._valve_handler(self.button_valfler5, 'CONVSEL')
    def send_butonValfler6(self): self._valve_handler(self.button_valfler6, 'WECLSEL')
    def send_butonValfler7(self): self._valve_handler(self.button_valfler7, 'OPTICSEL')
    def send_butonValfler8(self): self._valve_handler(self.button_valfler8, 'RINGSEL')

    # ═══════════ Test/Joy/Light/Exposure/Gap/Contact ═══════════

    def _toggle_send(self, btn, cmd_on, cmd_off='STOP', val_on=1, val_off=0):
        if btn.isChecked():
            cmd_mgr.send(cmd_on, val_on)
            if "ON" in btn.text(): btn.setText(btn.text().replace("ON", "OFF"))
            elif "OFF" in btn.text(): btn.setText(btn.text().replace("OFF", "ON"))
        else:
            cmd_mgr.send(cmd_off, val_off)
            if "ON" in btn.text(): btn.setText(btn.text().replace("ON", "OFF"))
            elif "OFF" in btn.text(): btn.setText(btn.text().replace("OFF", "ON"))

    def send_Testmode_back(self):
        self._toggle_send(self.button_testmode_back, 'TESTMODEBACK', 'TESTMODE')

    def send_Joymode(self):
        self._toggle_send(self.button_joymode, 'JOYMODE', 'JOYMODEBACK')

    def send_light_ON(self):
        self._toggle_send(self.button_light, 'OPTC', 'OPM')

    def send_Exposure(self):
        if hasattr(self, 'lineEditSendData_exp'):
            val = self._get_input_value(self.lineEditSendData_exp, "Exposure")
            cmd_mgr.set_exposure(val)

    def send_ExpEnergy(self):
        if hasattr(self, 'lineEditExpEnergy'):
            val = self._get_input_value(self.lineEditExpEnergy, "Energy")
            cmd_mgr.set_exposure_energy(val)

    def send_ExpPower(self):
        if hasattr(self, 'lineEditExpPower'):
            val = self._get_input_value(self.lineEditExpPower, "Power")
            cmd_mgr.set_exposure_power(val)

    def send_KeepHolder(self):
        self._toggle_send(self.button_KeepHolder, 'KEEPHPOS')

    def send_ContactPos(self):
        self._toggle_send(self.button_ContactPos, 'CONTPOS')

    def GapDataSend(self):
        if hasattr(self, 'lineEditGap'):
            val = self._get_input_value(self.lineEditGap, "Gap")
            cmd_mgr.set_gap(val)

    # ═══════════ Home Axis Butonları (Modüler) ═══════════

    _home_axis_map = {
        'send_butonHomePAxis':   'HOMESX',    'send_butonHomePAxis1':  'HOMESY',
        'send_butonHomePAxis2':  'HOMESZ',    'send_butonHomePAxis3':  'HOMEMLX',
        'send_butonHomePAxis4':  'HOMEMLY',   'send_butonHomePAxis5':  'HOMEMRX',
        'send_butonHomePAxis6':  'HOMEMRY',   'send_butonHomePAxis7':  'HOMEMLZ',
        'send_butonHomePAxis8':  'HOMEMRZ',   'send_butonHomePAxis9':  'HOMESYSTM',
        'send_butonHomePAxis10': 'HOMESXY',   'send_butonHomePAxis11': 'HOMEMRXY',
        'send_butonHomePAxis12': 'HOMEMLXY',  'send_butonHomePAxis13': 'HOMESTH',
    }

    def _home_handler(self, btn, cmd_name):
        if btn.isChecked():
            cmd_mgr.send(cmd_name, 1)
        else:
            cmd_mgr.stop(0)

    def send_butonHomePAxis(self):    self._home_handler(self.button_HomeAxis, 'HOMESX')
    def send_butonHomePAxis1(self):   self._home_handler(self.button_HomeAxis1, 'HOMESY')
    def send_butonHomePAxis2(self):   self._home_handler(self.button_HomeAxis2, 'HOMESZ')
    def send_butonHomePAxis3(self):   self._home_handler(self.button_HomeAxis3, 'HOMESTH')
    def send_butonHomePAxis4(self):   self._home_handler(self.button_HomeAxis4, 'HOMEMRX')
    def send_butonHomePAxis5(self):   self._home_handler(self.button_HomeAxis5, 'HOMEMRY')
    def send_butonHomePAxis6(self):   self._home_handler(self.button_HomeAxis6, 'HOMEMLX')
    def send_butonHomePAxis7(self):   self._home_handler(self.button_HomeAxis7, 'HOMEMLY')
    def send_butonHomePAxis8(self):   self._home_handler(self.button_HomeAxis8, 'HOMEMRZ')
    def send_butonHomePAxis9(self):   self._home_handler(self.button_HomeAxis9, 'HOMEMLZ')
    def send_butonHomePAxis10(self):  self._home_handler(self.button_HomeAxis10, 'HOMESXY')
    def send_butonHomePAxis11(self):  self._home_handler(self.button_HomeAxis11, 'HOMEMRXY')
    def send_butonHomePAxis12(self):  self._home_handler(self.button_HomeAxis12, 'HOMEMLXY')
    def send_butonHomePAxis13(self):  self._home_handler(self.button_HomeAxis13, 'HOMESYSTM')
    def send_butonHomePAxisJoker(self): self._home_handler(self.button_HomeAxis9, 'HOMESYSTM')

    # ═══════════ Veri Alımı (Data Received) ═══════════

    # ═══════════ Veri Alımı (YENİ BINARY SİSTEM) ═══════════

    def _process_binary_command(self, cmd, value):
        """Binary protokolden gelen komutu işler ve UI'ı günceller."""
        cmd_name = getattr(cmd, 'name', str(cmd))
        
        # ── MQTT PUBLISH (mevcut kodun en üstüne ekle) ──────────────
        from mqtt_publisher import lima_mqtt

        # Valf durumları → lima/valve topiği
        VALVE_CMDS = {
            'MASKVAC', 'SAMPFVAC', 'SAMPHVAC',
            'CONTVAC', 'WECLOCK', 'OPTICSEL', 'RINGSEL'
        }
        # Motor/Homing → lima/motor topiği
        HOME_CMDS = {
            'HOMESXOK', 'HOMESYOK', 'HOMESZOK', 'HOMESTHOK',
            'HOMEMLXOK', 'HOMEMRZOK'
        }
        # Pozisyon → lima/position topiği
        POS_CMDS = {
            'SXMPOS', 'SYMPOS', 'MLZPOS', 'MRZPOS'
        }
        # Süreç → lima/process topiği
        PROC_CMDS = {
            'AUTOALIGN', 'AUTOFOCUS', 'ALIGNCHK', 'EXPOSURE'
        }

        reply_key = self.CMD_TO_REPLY.get(cmd_name, cmd_name)

        if reply_key in VALVE_CMDS:
            lima_mqtt.publish("lima/valve", {
                "cmd": reply_key,
                "value": value,
                "status": "open" if value == 1 else "closed"
            })
        elif cmd_name in HOME_CMDS:
            lima_mqtt.publish("lima/motor", {
                "cmd": cmd_name,
                "value": value,
                "status": "ok" if value == 1 else "failed"
            })
        elif cmd_name in POS_CMDS:
            lima_mqtt.publish("lima/position", {
                "cmd": cmd_name,
                "value": value
            })
        elif cmd_name in PROC_CMDS:
            lima_mqtt.publish("lima/process", {
                "cmd": cmd_name,
                "value": value
            })

        from protocol import LimaCommand

        # PyQt sinyalinden gelen objeden güvenli şekilde komut ismini al
        cmd_name = getattr(cmd, 'name', str(cmd))
        self._log_message("IN", f"{cmd_name} (Value: {value})")

        # UI için Yeşil/Kırmızı İkon Yolları
        if 'manager' in globals():
            img_green = manager.get_image_path("green")
            img_red = manager.get_image_path("red")
        else:
            img_green = "green.png"
            img_red = "red.png"

        # ── 1. HANDSHAKE (Bağlantı Onayı) ──
        if cmd == LimaCommand.YP:
            if value == 1:
                self._log_message("SYS", "STM32 Cihazı ile Bağlantı Kuruldu! ✅")
            return

        # ── 2. POZİSYON GÜNCELLEMELERİ ──
        # STM32'den gelen pozisyon komutlarını ekrandaki kutucuklara yaz
        POS_MAP = {
            'SXMPOS':  'bufferSXPOS',   'SYMPOS':  'bufferSYPOS',
            'MLXMPOS': 'bufferMLXPOS',  'MLYMPOS': 'bufferMLYPOS',
            'MRXMPOS': 'bufferMRXPOS',  'MRYMPOS': 'bufferMRYPOS',
            # Doğrudan isim eşleşmesi olan komutlar (eski uyumluluk)
            'SXPOS':   'bufferSXPOS',   'SYPOS':   'bufferSYPOS',
            'STPOS':   'bufferSTPOS',   'SZPOS':   'bufferSZPOS',
            'MRXPOS':  'bufferMRXPOS',  'MRYPOS':  'bufferMRYPOS',
            'MLXPOS':  'bufferMLXPOS',  'MLYPOS':  'bufferMLYPOS',
            'MRZPOS':  'bufferMRZPOS',  'MLZPOS':  'bufferMLZPOS',
            'EXPENERGY': 'bufferEnergy', 'EXPPOWER': 'bufferPower',
        }

        buf_attr = POS_MAP.get(cmd.name)
        if buf_attr:
            buf_widget = getattr(self, buf_attr, None)
            if buf_widget:
                buf_widget.setPlainText(str(value))
            return  # Pozisyon komutu işlendi, devam etmeye gerek yok

        # ── 3. UI GÖSTERGELERİNİ (Indicators) GÜNCELLEME ──
        reply_key = self.CMD_TO_REPLY.get(cmd_name, cmd_name)
        target_label_name = self.INDICATORS_MAP.get(reply_key) or self.INDICATORS_MAP.get(cmd_name)

        if target_label_name:
            label = getattr(self, target_label_name, None)
            if label:
                red_path   = manager.get_image_path("red")   if hasattr(manager, 'get_image_path') else "red.png"
                green_path = manager.get_image_path("green") if hasattr(manager, 'get_image_path') else "green.png"
                img = green_path if value == 1 else red_path
                pix = QtGui.QPixmap(img)
                label.setStyleSheet("")  # waiting stilini temizle
                label.setText("")        # "...WAIT..." yazısını temizle
                if not pix.isNull():
                    label.setPixmap(pix)
                    label.setAlignment(Qt.AlignCenter)
                else:
                    label.setText("✓" if value == 1 else "✗")
                    label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;" if value == 1
                                        else "color: red; font-weight: bold; font-size: 14px;")

        # HOMESTH→STH2 duplikasyonu kaldırıldı (image_labelHOMESTH2 artık HOMESYSTM altında)

        # ── 5. HOMESZ buton reset ── (kaldırıldı: STM32 HOMESZOK'u çok hızlı gönderirse buton
        # anında unchecked olup siyah kalıyordu; buton state'i kullanıcıya bırakıldı)

        # ── 6. Sistem Status Mesajları ──
        if cmd.name == "HOMESYSTM":
            if value == 0:
                self.msg_box_zero()
            elif value == 1:
                self.msg_box_one()

        # ── 7. Hinfo.txt / Log Kutusu Güncellemesi ──
        # Binary protokolde Txt komutu varsa log kutusuna yaz
        if cmd.name == "COMCHECK":
            self._log_message("SYS", f"COMCHECK yanıtı: {value}")

    # ═══════════ Mesaj Kutuları ═══════════

    def msg_box_one(self):
        msg = QMessageBox()
        msg.setText("Operation Successful")
        msg.setWindowTitle("Success")
        msg.exec_()

    def msg_box_zero(self):
        msg = QMessageBox()
        msg.setText("Operation Failed")
        msg.setWindowTitle("Error")
        msg.exec_()

    def msg_box_port(self):
        msg = QMessageBox()
        msg.setText("Port already open")
        msg.setWindowTitle("Info")
        msg.exec_()

    def msg_box_port2(self):
        msg = QMessageBox()
        msg.setText("Failed to open port")
        msg.setWindowTitle("Error")
        msg.exec_()

    # ═══════════ Navigation ═══════════

    def back_button_setup(self):
        self.setupwindow = None
        from SetupWindow import Ui_setupwindow
        self.setupwindow = QMainWindow()
        self.ui = Ui_setupwindow()
        self.ui.setupscreenUi(self.setupwindow)
        manager.switch_window(self.setupwindow)

    def openSystemControl(self):
        pass  # SystemWindow placeholder

    def listSerialPorts(self):
        for port_name in serial_mgr.available_ports():
            self.comboBox.addItem(port_name)

    def portDisconnect(self):
        serial_mgr.disconnect()


    # ═══════════ setupUi — Widget Creation (Preserved) ═══════════

    def setupUi(self, MotorWindow):
        MotorWindow.setObjectName("MotorWindow")
        MotorWindow.resize(1938, 1098)
        self.centralwidget = QtWidgets.QWidget(MotorWindow)
        self.centralwidget.setObjectName("centralwidget")

        MotorWindow.setWindowIcon(QtGui.QIcon(manager.get_image_path("mainicon")))
        
        # Make buffers highly visible
        buffer_style = "background-color: #FAFAFA; color: #111; border: 2px solid #E67E22; border-radius: 4px; font-weight: bold; font-size: 14px;"
        
        # Ensure layout properties are stripped out safely
        self.setCentralWidget(self.centralwidget)

        # ── Arkaplan Resmi ──
        self._bg_label = QtWidgets.QLabel(self.centralwidget)
        self._bg_label.setGeometry(self.centralwidget.rect())
        self._bg_path = r"C:\Users\Can\Desktop\Upgraded LIMA\Images\558571.png"
        _bg_pix = QtGui.QPixmap(self._bg_path)
        if not _bg_pix.isNull():
            self._bg_label.setPixmap(
                _bg_pix.scaled(self.centralwidget.size(),
                               Qt.KeepAspectRatioByExpanding,
                               Qt.SmoothTransformation)
            )
        self._bg_label.lower()
        self._bg_label.setScaledContents(False)


       

        # ══════════ TWO-PAGE LAYOUT STRUCTURE ══════════
        # Left panel: switchable pages (55% width)
        # Right panel: fixed camera feeds (45% width)
        _screen = QApplication.primaryScreen()
        _sg = _screen.availableGeometry() if _screen else QRect(0, 0, 1920, 1080)
        _sw, _sh = _sg.width(), _sg.height()
        _left_w = int(_sw * 0.55)
        _right_w = _sw - _left_w
        _top_h = 95      # top bar height
        _tab_h = 60       # bottom tab bar height
        _content_h = _sh - _top_h - _tab_h

        # -- Camera Panel (right side, always visible) --
        self.cam_panel = QWidget(self.centralwidget)
        self.cam_panel.setGeometry(_left_w, 0, _right_w, _sh - _tab_h)
        self.cam_panel.setStyleSheet("background-color: #0a0a14;")

        _cam_layout = QVBoxLayout(self.cam_panel)
        _cam_layout.setContentsMargins(4, 4, 4, 4)
        _cam_layout.setSpacing(4)

        self.cam1_display = QLabel("CAM1")
        self.cam1_display.setAlignment(Qt.AlignCenter)
        self.cam1_display.setStyleSheet(
            "background-color: #111; color: #555; font-size: 28px; "
            "border: 1px solid #333; border-radius: 6px;")
        self.cam1_display.setMinimumHeight(200)

        self.cam2_display = QLabel("CAM2")
        self.cam2_display.setAlignment(Qt.AlignCenter)
        self.cam2_display.setStyleSheet(
            "background-color: #111; color: #555; font-size: 28px; "
            "border: 1px solid #333; border-radius: 6px;")
        self.cam2_display.setMinimumHeight(200)

        _cam_layout.addWidget(self.cam1_display, stretch=1)
        _cam_layout.addWidget(self.cam2_display, stretch=1)

        # -- Vertical divider between left panel and camera panel --
        _vdiv = QFrame(self.centralwidget)
        _vdiv.setFrameShape(QFrame.VLine)
        _vdiv.setGeometry(_left_w - 1, 0, 2, _sh - _tab_h)
        _vdiv.setStyleSheet("color: #333;")

        # -- Top bar horizontal divider --
        _hdiv_top = QFrame(self.centralwidget)
        _hdiv_top.setFrameShape(QFrame.HLine)
        _hdiv_top.setGeometry(0, _top_h, _left_w, 2)
        _hdiv_top.setStyleSheet("color: #333;")

        # Store layout metrics for later use
        self._layout_left_w = _left_w
        self._layout_sh = _sh
        self._layout_top_h = _top_h
        self._layout_tab_h = _tab_h
        self._layout_content_h = _content_h



        # Tam ekran ayarı setupUi sonunda yapılır
        self.setWindowTitle('LIMA Motor Control')
    

        
      
        
        
       
        # self.camera_button2 = QPushButton(self.centralwidget)
        # self.camera_button2.setGeometry(QtCore.QRect(150,800,60,90))
        # self.camera_button2.setText("")
        # self.camera_button2.setFont(QtGui.QFont("Arial", 8))
        # self.camera_button2.clicked.connect(self.open_camera2)
        # self.camera_button2.setStyleSheet("background-color: transparent; color: #FFFFFF;")
        # self.camera_button2.setIcon(QtGui.QIcon(manager.get_image_path("Camera")))
        # self.camera_button2
        # self.camera_button2.setIconSize(QtCore.QSize(100, 100))

        ####

        # self.camera_button = QPushButton(self.centralwidget)
        # self.camera_button.setGeometry(QtCore.QRect(55,800,60,90))
        # self.camera_button.setText("")
        # self.camera_button.setFont(QtGui.QFont("Arial", 8))
        # self.camera_button.clicked.connect(self.open_camera)
        # self.camera_button.setStyleSheet("background-color: transparent; color: #FFFFFF;")
        # self.camera_button.setIcon(QtGui.QIcon(manager.get_image_path("Camera")))
        # self.camera_button
        # self.camera_button.setIconSize(QtCore.QSize(100, 100))
    
        ############TEST MODE // JOY MODE############

        self.button_testmode_back = QPushButton(self.centralwidget)
        self.button_testmode_back.setGeometry(QtCore.QRect(85, 640, 100, 40))
        self.button_testmode_back.setText("Testmode")
        self.button_testmode_back.setCheckable(True)
        self.button_testmode_back.setFont(QtGui.QFont("Arial", 8))  
        self.button_testmode_back.clicked.connect(self.send_Testmode_back)
        



        self.button_joymode = QPushButton(self.centralwidget)
        self.button_joymode.setGeometry(QtCore.QRect(85, 700, 100, 40))
        self.button_joymode.setText("Joy Mode")
        self.button_joymode.setCheckable(True)
        self.button_joymode.setFont(QtGui.QFont("Arial", 8)) 
        self.button_joymode.clicked.connect(self.send_Joymode)
        


        self.button_KeepHolder  = QPushButton(self.centralwidget)
        self.button_KeepHolder.setGeometry(QtCore.QRect(300, 520, 80, 30))
        self.button_KeepHolder.setText("Keep Holder")
        self.button_KeepHolder.setCheckable(True)
        self.button_KeepHolder.setFont(QtGui.QFont("Arial", 8))  
        self.button_KeepHolder.clicked.connect(self.send_KeepHolder)
        

        self.button_ContactPos = QPushButton(self.centralwidget)
        self.button_ContactPos.setGeometry(QtCore.QRect(400, 520, 80, 30))
        self.button_ContactPos.setText("Contact Pos")
        self.button_ContactPos.setCheckable(True)
        self.button_ContactPos.setFont(QtGui.QFont("Arial", 8))  
        self.button_ContactPos.clicked.connect(self.send_ContactPos)
        

        self.button_Gap  = QPushButton(self.centralwidget)
        self.button_Gap.setGeometry(QtCore.QRect(500, 520, 80, 30))
        self.button_Gap.setText("Gap")
        self.button_Gap.setCheckable(True)
        self.button_Gap.setFont(QtGui.QFont("Arial", 8))  
        self.button_Gap.clicked.connect(self.GapDataSend)
        

        
      


  

        #################### V A L F L E R ###############################################
        self.button_valfler  = QPushButton(self.centralwidget)
        self.button_valfler.setGeometry(QtCore.QRect(20, 200, 80, 30))
        self.button_valfler.setText("MASCVAC")
        self.button_valfler.setCheckable(True)
        self.button_valfler.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler.clicked.connect(self.send_butonValfler)
        


        self.button_valfler1  = QPushButton(self.centralwidget)
        self.button_valfler1.setGeometry(QtCore.QRect(20, 300, 80, 30))
        self.button_valfler1.setText("SAMPVSEL")
        self.button_valfler1.setCheckable(True)
        self.button_valfler1.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler1.clicked.connect(self.send_butonValfler1)
        


        self.button_valfler2  = QPushButton(self.centralwidget)
        self.button_valfler2.setGeometry(QtCore.QRect(20, 400, 80, 30))
        self.button_valfler2.setText("SAMPHVSEL")
        self.button_valfler2.setCheckable(True)
        self.button_valfler2.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler2.clicked.connect(self.send_butonValfler2)
        


        self.button_valfler3  = QPushButton(self.centralwidget)
        self.button_valfler3.setGeometry(QtCore.QRect(20, 500, 80, 30))
        self.button_valfler3.setText("HARDCONTACTSEL")
        self.button_valfler3.setCheckable(True)
        self.button_valfler3.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler3.clicked.connect(self.send_butonValfler3)
        


        self.button_valfler4  = QPushButton(self.centralwidget)
        self.button_valfler4.setGeometry(QtCore.QRect(160, 200, 80, 30))
        self.button_valfler4.setText("SAMPFVSEL")
        self.button_valfler4.setCheckable(True)
        self.button_valfler4.setFont(QtGui.QFont("Arial", 7))  
        self.button_valfler4.clicked.connect(self.send_butonValfler4)
        


        self.button_valfler5  = QPushButton(self.centralwidget)
        self.button_valfler5.setGeometry(QtCore.QRect(160, 300, 80, 30))
        self.button_valfler5.setText("CONTVAC")
        self.button_valfler5.setCheckable(True)
        self.button_valfler5.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler5.clicked.connect(self.send_butonValfler5)
        


        self.button_valfler6  = QPushButton(self.centralwidget)
        self.button_valfler6.setGeometry(QtCore.QRect(160, 400, 80, 30))
        self.button_valfler6.setText("WECSEL")
        self.button_valfler6.setCheckable(True)
        self.button_valfler6.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler6.clicked.connect(self.send_butonValfler6)
        


        self.button_valfler7  = QPushButton(self.centralwidget)
        self.button_valfler7.setGeometry(QtCore.QRect(160, 500, 80, 30))
        self.button_valfler7.setText("OPTICSEL")
        self.button_valfler7.setCheckable(True)
        self.button_valfler7.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler7.clicked.connect(self.send_butonValfler7)
        

        self.button_valfler8  = QPushButton(self.centralwidget)
        self.button_valfler8.setGeometry(QtCore.QRect(160, 100, 80, 30))
        self.button_valfler8.setText("RINGSEL")
        self.button_valfler8.setCheckable(True)
        self.button_valfler8.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler8.clicked.connect(self.send_butonValfler8)
        

        self.button_valfler9  = QPushButton(self.centralwidget)
        self.button_valfler9.setGeometry(QtCore.QRect(20, 100, 80, 30))
        self.button_valfler9.setText("EMPTYSEL")
        self.button_valfler9.setCheckable(True)
        self.button_valfler9.setFont(QtGui.QFont("Arial", 8))  
        self.button_valfler9.clicked.connect(self.send_butonValfler8)
        




        ################ H O M C H E C K ################

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(300,200,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMESX = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMESX.setObjectName("image_labelHOMESX")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMESX)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(400,200,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMESY = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMESY.setObjectName("image_labelHOMESY")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMESY)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(500,200,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMESZ = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMESZ.setObjectName("image_labelHOMESZ")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMESZ)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(700,200,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMRX = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMRX.setObjectName("image_labelHOMEMRX")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMRX)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(300,350,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMRY = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMRY.setObjectName("image_labelHOMEMRY")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMRY)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(600,200,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMESTH = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMESTH.setObjectName("image_labelHOMESTH")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMESTH)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(400,350,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMLX = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMLX.setObjectName("image_labelHOMEMLX")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMLX)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(500,350,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMLY = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMLY.setObjectName("image_labelHOMEMLY")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMLY)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(600,350,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMRZ = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMRZ.setObjectName("image_labelHOMEMRZ")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMRZ)
        
        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(700,350,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMLZ = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMLZ.setObjectName("image_labelHOMEMLZ")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMLZ)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(300,470,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMESXY = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMESXY.setObjectName("image_labelHOMESXY")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMESXY)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(400,470,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMRXY = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMRXY.setObjectName("image_labelHOMEMRXY")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMRXY)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(500,470,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMEMLXY = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMEMLXY.setObjectName("image_labelHOMEMLXY")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMEMLXY)

        self.verticalLayoutWidget_HMC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_HMC.setGeometry(QtCore.QRect(600,470,75,50))
        self.verticalLayoutWidget_HMC.setObjectName("verticalLayoutWidget_HMC")
        self.verticalLayoutWidget_HMC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_HMC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_HMC)
        self.verticalLayout_HMC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_HMC.setObjectName("verticalLayout_HMC")
        self.image_labelHOMESTH2 = QtWidgets.QLabel(self.verticalLayoutWidget_HMC)
        self.image_labelHOMESTH2.setObjectName("image_labelHOMESTH2")
        self.verticalLayout_HMC.addWidget(self.image_labelHOMESTH2)



        #################################################

        self.verticalLayoutWidget_keep = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_keep.setGeometry(QtCore.QRect(305,540,75,50))
        self.verticalLayoutWidget_keep.setObjectName("verticalLayoutWidget_keep")
        self.verticalLayoutWidget_keep.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_keep = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_keep)
        self.verticalLayout_keep.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_keep.setObjectName("verticalLayout_keep")
        self.image_labelKEEPHSTAT = QtWidgets.QLabel(self.verticalLayoutWidget_keep)
        self.image_labelKEEPHSTAT.setObjectName("image_labelKEEPHSTAT")
        self.verticalLayout_keep.addWidget(self.image_labelKEEPHSTAT)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(405,540,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")  
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                               #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelCONTPSTAT = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelCONTPSTAT.setObjectName("image_labelCONTPSTAT")
        self.verticalLayout_VAC.addWidget(self.image_labelCONTPSTAT)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(505,540,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")   
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                              #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelGAPPOSSTAT = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelGAPPOSSTAT.setObjectName("image_labelGAPPOSSTAT")
        self.verticalLayout_VAC.addWidget(self.image_labelGAPPOSSTAT)


        #################################################


        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(20,240,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelMASKVAC = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelMASKVAC.setObjectName("image_labelMASKVAC")
        self.verticalLayout_VAC.addWidget(self.image_labelMASKVAC)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(20,540,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")  
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                               #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelMSKHVAC = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelMSKHVAC.setObjectName("image_labelMSKHVAC")
        self.verticalLayout_VAC.addWidget(self.image_labelMSKHVAC)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(20,340,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")   
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                              #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelSAMPVAC = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelSAMPVAC.setObjectName("image_labelSAMPVAC")
        self.verticalLayout_VAC.addWidget(self.image_labelSAMPVAC)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(20,440,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")   
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                              #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelSMPHVAC = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelSMPHVAC.setObjectName("image_labelSMPHVAC")
        self.verticalLayout_VAC.addWidget(self.image_labelSMPHVAC)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(160,440,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")  
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                               #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelWECSEL = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelWECSEL.setObjectName("image_labelWECSEL")
        self.verticalLayout_VAC.addWidget(self.image_labelWECSEL)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(160,340,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                                 #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelCONTVAC = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelCONTVAC.setObjectName("image_labelCONTVAC")
        self.verticalLayout_VAC.addWidget(self.image_labelCONTVAC)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(160,240,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")  
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                               #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelSAMPFSEL = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelSAMPFSEL.setObjectName("image_labelSAMPFSEL")
        self.verticalLayout_VAC.addWidget(self.image_labelSAMPFSEL)

        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(160,540,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")    
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                             #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelOPTIVAC = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelOPTIVAC.setObjectName("image_labelOPTIVAC")
        self.verticalLayout_VAC.addWidget(self.image_labelOPTIVAC)

    
        self.verticalLayoutWidget_VAC = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_VAC.setGeometry(QtCore.QRect(160,140,75,50))
        self.verticalLayoutWidget_VAC.setObjectName("verticalLayoutWidget_VAC")    
        self.verticalLayoutWidget_VAC.setStyleSheet("background-color: transparent; color: #242F36")                                   #õlabels                             #õlabels
        self.verticalLayout_VAC = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_VAC)
        self.verticalLayout_VAC.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_VAC.setObjectName("verticalLayout_VAC")
        self.image_labelRINGSEL = QtWidgets.QLabel(self.verticalLayoutWidget_VAC)
        self.image_labelRINGSEL.setObjectName("image_labelRINGSEL")
        self.verticalLayout_VAC.addWidget(self.image_labelRINGSEL)



        #################################################################################



        """Butonların Hepsi"""
        # ZED Aşağı Butonu
        self.zed_down_button = QPushButton(self.centralwidget)
        self.zed_down_button.setGeometry(QtCore.QRect(375, 805, 75, 75))       
        self.zed_down_button.setText("▼")
        self.zed_down_button.setCheckable(True)
        self.zed_down_button.setFont(QtGui.QFont("Arial", 20))  
        self.zed_down_button.clicked.connect(self.portSendDataZedYN)
        self.zed_down_button.clicked.connect(self.button_check)  
        self.zed_down_button.setVisible(False)
        
        self.zed_down_button.setText("")
        self.zed_down_button.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2")))
        self.zed_down_button
        self.zed_down_button.setIconSize(QtCore.QSize(110, 110))

        # ZED Yukarı Butonu
        self.zed_up_button = QPushButton(self.centralwidget)
        self.zed_up_button.setGeometry(QtCore.QRect(375, 655, 75, 75))
        self.zed_up_button.setText("▲")
        self.zed_up_button.setCheckable(True)
        self.zed_up_button.setFont(QtGui.QFont("Arial", 20))  
        self.zed_up_button.clicked.connect(self.button_check)
        self.zed_up_button.clicked.connect(self.portSendDataZedYP)
        self.zed_up_button.setVisible(False)
        
        self.zed_up_button.setText("")
        self.zed_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.zed_up_button
        self.zed_up_button.setIconSize(QtCore.QSize(100, 100))

#Sample up button
        self.sample_up_button = QPushButton(self.centralwidget)
        self.sample_up_button.setGeometry(QtCore.QRect(375, 655, 75, 75))
        self.sample_up_button.setText("▼")
        self.sample_up_button.setCheckable(True)
        self.sample_up_button.setFont(QtGui.QFont("Arial", 20))
        self.sample_up_button.clicked.connect(self.portSendDataSampleYP)
        self.sample_up_button.clicked.connect(self.button_check)
        self.sample_up_button.setVisible(False)
        
        self.sample_up_button.setText("")
        self.sample_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.sample_up_button
        self.sample_up_button.setIconSize(QtCore.QSize(100, 100))


        


      
            
       

         # sample Aşağı Butonu
        self.sample_down_button = QPushButton(self.centralwidget)
        self.sample_down_button.setGeometry(QtCore.QRect(375, 805, 75, 75))
        self.sample_down_button.setText("▼")
        self.sample_down_button.setCheckable(True)
        self.sample_down_button.setFont(QtGui.QFont("Arial", 20))
        self.sample_down_button.clicked.connect(self.portSendDataSampleYN)
        self.sample_down_button.clicked.connect(self.button_check)
        self.sample_down_button.setVisible(False)
        
        self.sample_down_button.setText("")
        self.sample_down_button.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2")))
        self.sample_down_button
        self.sample_down_button.setIconSize(QtCore.QSize(100, 100))

        

         # sample Sol Butonu
        self.sample_left_button = QPushButton(self.centralwidget)
        self.sample_left_button.setGeometry(QtCore.QRect(300, 730, 75, 75))
        self.sample_left_button.setText("◄")
        self.sample_left_button.setCheckable(True)
        self.sample_left_button.setFont(QtGui.QFont("Arial", 20))
        self.sample_left_button.clicked.connect(self.portSendDataSampleXN)
        self.sample_left_button.clicked.connect(self.button_check)
        self.sample_left_button.setVisible(False)
        
        self.sample_left_button.setText("")
        self.sample_left_button.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2")))
        self.sample_left_button
        self.sample_left_button.setIconSize(QtCore.QSize(100, 100))



         # sample Sağ Butonu
        self.sample_right_button = QPushButton(self.centralwidget)
        self.sample_right_button.setGeometry(QtCore.QRect(450, 730, 75, 75))
        self.sample_right_button.setText("►")
        self.sample_right_button.setCheckable(True)
        self.sample_right_button.setFont(QtGui.QFont("Arial", 20))
        self.sample_right_button.clicked.connect(self.portSendDataSampleXP)  
        self.sample_right_button.clicked.connect(self.button_check)
        self.sample_right_button.setVisible(False)
        
        self.sample_right_button.setText("")
        self.sample_right_button.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2")))
        self.sample_right_button
        self.sample_right_button.setIconSize(QtCore.QSize(100, 100))

        # microL Yukarı Butonu
        self.MicroL_up_button = QPushButton(self.centralwidget)
        self.MicroL_up_button.setGeometry(QtCore.QRect(610, 230, 75, 75))
        self.MicroL_up_button.setText("▲")
        self.MicroL_up_button.setCheckable(True)
        self.MicroL_up_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroL_up_button.clicked.connect(self.portSendDataMicLeftYP)
        self.MicroL_up_button.clicked.connect(self.button_check)
        self.MicroL_up_button.setVisible(False)
        
        self.MicroL_up_button.setText("")
        self.MicroL_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.MicroL_up_button
        self.MicroL_up_button.setIconSize(QtCore.QSize(100, 100))
       

         # microL Aşağı Butonu
        self.MicroL_down_button = QPushButton(self.centralwidget)
        self.MicroL_down_button.setGeometry(QtCore.QRect(610, 380, 75, 75))
        self.MicroL_down_button.setText("▼")
        self.MicroL_down_button.setCheckable(True)
        self.MicroL_down_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroL_down_button.clicked.connect(self.portSendDataMicLeftYN)
        self.MicroL_down_button.clicked.connect(self.button_check)
        self.MicroL_down_button.setVisible(False)
        
        self.MicroL_down_button.setText("")
        self.MicroL_down_button.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2")))
        self.MicroL_down_button
        self.MicroL_down_button.setIconSize(QtCore.QSize(100, 100))


        # MicroL Sağ Butonu
        self.MicroL_right_button = QPushButton(self.centralwidget)
        self.MicroL_right_button.setGeometry(QtCore.QRect(685, 305, 75, 75))
        self.MicroL_right_button.setText("►")
        self.MicroL_right_button.setCheckable(True)
        self.MicroL_right_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroL_right_button.clicked.connect(self.portSendDataMicLeftXP)     
        self.MicroL_right_button.clicked.connect(self.button_check)
        self.MicroL_right_button.setVisible(False)
        
        self.MicroL_right_button.setText("")
        self.MicroL_right_button.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2")))
        self.MicroL_right_button
        self.MicroL_right_button.setIconSize(QtCore.QSize(100, 100))
    #mcşro L sol
        self.MicroL_left_button = QPushButton(self.centralwidget)
        self.MicroL_left_button.setGeometry(QtCore.QRect(535, 305, 75, 75))
        self.MicroL_left_button.setText("►")
        self.MicroL_left_button.setCheckable(True)
        self.MicroL_left_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroL_left_button.clicked.connect(self.portSendDataMicLeftXN)
        self.MicroL_left_button.clicked.connect(self.button_check)
        self.MicroL_left_button.setVisible(False)
        
        self.MicroL_left_button.setText("")
        self.MicroL_left_button.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2")))
        self.MicroL_left_button
        self.MicroL_left_button.setIconSize(QtCore.QSize(100, 100))

     # microS Yukarı Butonu
        self.MicroS_up_button = QPushButton(self.centralwidget)
        self.MicroS_up_button.setGeometry(QtCore.QRect(610, 230, 75, 75))
        self.MicroS_up_button.setText("▲")
        self.MicroS_up_button.setCheckable(True)
        self.MicroS_up_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroS_up_button.clicked.connect(self.portSendDataMicRightYP)
        self.MicroS_up_button.clicked.connect(self.button_check)
        self.MicroS_up_button.setVisible(False)
        
        self.MicroS_up_button.setText("")
        self.MicroS_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.MicroS_up_button
        self.MicroS_up_button.setIconSize(QtCore.QSize(100, 100))
       

         # microS Aşağı Butonu
        self.MicroS_down_button = QPushButton(self.centralwidget)
        self.MicroS_down_button.setGeometry(QtCore.QRect(610, 380, 75, 75))
        self.MicroS_down_button.setText("▼")
        self.MicroS_down_button.setCheckable(True)
        self.MicroS_down_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroS_down_button.clicked.connect(self.portSendDataMicRightYN)   
        self.MicroS_down_button.clicked.connect(self.button_check)
        self.MicroS_down_button.setVisible(False)
        
        self.MicroS_down_button.setText("")
        self.MicroS_down_button.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2")))
        self.MicroS_down_button
        self.MicroS_down_button.setIconSize(QtCore.QSize(100, 100))

        # microS sol Butonu
        self.MicroS_left_button = QPushButton(self.centralwidget)
        self.MicroS_left_button.setGeometry(QtCore.QRect(535, 305, 75, 75))
        self.MicroS_left_button.setText("▼")
        self.MicroS_left_button.setCheckable(True)
        self.MicroS_left_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroS_left_button.clicked.connect(self.portSendDataMicroSXN)
        self.MicroS_left_button.clicked.connect(self.button_check)
        self.MicroS_left_button.setVisible(False)
        
        self.MicroS_left_button.setText("")
        self.MicroS_left_button.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2")))
        self.MicroS_left_button
        self.MicroS_left_button.setIconSize(QtCore.QSize(100, 100))

        # microS sağ Butonu
        self.MicroS_right_button = QPushButton(self.centralwidget)
        self.MicroS_right_button.setGeometry(QtCore.QRect(685, 305, 75, 75))
        self.MicroS_right_button.setText("▼")
        self.MicroS_right_button.setCheckable(True)
        self.MicroS_right_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroS_right_button.clicked.connect(self.portSendDataMicRightXP)
        self.MicroS_right_button.clicked.connect(self.button_check)
        self.MicroS_right_button.setVisible(False)
        
        self.MicroS_right_button.setText("")
        self.MicroS_right_button.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2")))
        self.MicroS_right_button
        self.MicroS_right_button.setIconSize(QtCore.QSize(100, 100))

        #MicroLefet Zed up button
        self.MicroLZed_up_button = QPushButton(self.centralwidget)
        self.MicroLZed_up_button.setGeometry(QtCore.QRect(610, 230, 75, 75))
        self.MicroLZed_up_button.setText("▲")
        self.MicroLZed_up_button.setCheckable(True)
        self.MicroLZed_up_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroLZed_up_button.clicked.connect(self.portSendDataMicLeftZedYP)
        self.MicroLZed_up_button.clicked.connect(self.button_check)
        self.MicroLZed_up_button.setVisible(False)
        
        self.MicroLZed_up_button.setText("")
        self.MicroLZed_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.MicroLZed_up_button
        self.MicroLZed_up_button.setIconSize(QtCore.QSize(100, 100))

         #MicroLeft Zed down button
        self.MicroLZed_down_button = QPushButton(self.centralwidget)
        self.MicroLZed_down_button.setGeometry(QtCore.QRect(610, 380, 75, 75))
        self.MicroLZed_down_button.setText("▲")
        self.MicroLZed_down_button.setCheckable(True)
        self.MicroLZed_down_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroLZed_down_button.clicked.connect(self.portSendDataMicLeftZedYN)
        self.MicroLZed_down_button.clicked.connect(self.button_check)
        self.MicroLZed_down_button.setVisible(False)
        
        self.MicroLZed_down_button.setText("")
        self.MicroLZed_down_button.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2")))
        self.MicroLZed_down_button
        self.MicroLZed_down_button.setIconSize(QtCore.QSize(100, 100))

        #  #MicroL Zed left button
        # self.MicroLZed_left_button = QPushButton(self.centralwidget)
        # self.MicroLZed_left_button.setGeometry(QtCore.QRect(535, 305, 75, 75))
        # self.MicroLZed_left_button.setText("▲")
        # self.MicroLZed_left_button.setCheckable(True)
        # self.MicroLZed_left_button.setFont(QtGui.QFont("Arial", 20))
        #   #Send Datası yok
        # self.MicroLZed_left_button.clicked.connect(self.button_check)
        # self.MicroLZed_left_button.setVisible(False)
        # self.MicroLZed_left_button.setStyleSheet("background-color: #d7d6e5;")
        # self.MicroLZed_left_button.setText("")
        # self.MicroLZed_left_button.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow")))
        # self.MicroLZed_left_button.setIconSize(QtCore.QSize(48, 48))

        #  #MicroL Zed right button
        # self.MicroLZed_right_button = QPushButton(self.centralwidget)
        # self.MicroLZed_right_button.setGeometry(QtCore.QRect(685, 305, 75, 75))
        # self.MicroLZed_right_button.setText("▲")
        # self.MicroLZed_right_button.setCheckable(True)
        # self.MicroLZed_right_button.setFont(QtGui.QFont("Arial", 20))
        # #Send Datası yok
        # self.MicroLZed_right_button.clicked.connect(self.button_check)
        # self.MicroLZed_right_button.setVisible(False)
        # self.MicroLZed_right_button.setStyleSheet("background-color: #d7d6e5;")
        # self.MicroLZed_right_button.setText("")
        # self.MicroLZed_right_button.setIcon(QtGui.QIcon(manager.get_image_path("rigtharrow")))
        # self.MicroLZed_right_button.setIconSize(QtCore.QSize(48, 48))

         #MicroRight Zed up button
        self.MicroRZed_up_button = QPushButton(self.centralwidget)
        self.MicroRZed_up_button.setGeometry(QtCore.QRect(610, 230, 75, 75))
        self.MicroRZed_up_button.setText("▲")
        self.MicroRZed_up_button.setCheckable(True)
        self.MicroRZed_up_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroRZed_up_button.clicked.connect(self.portSendDataMicRightZedYP)
        self.MicroRZed_up_button.clicked.connect(self.button_check)
        self.MicroRZed_up_button.setVisible(False)
        
        self.MicroRZed_up_button.setText("")
        self.MicroRZed_up_button.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))
        self.MicroRZed_up_button
        self.MicroRZed_up_button.setIconSize(QtCore.QSize(100, 100))

         #MicroR Zed down button
        self.MicroRZed_down_button = QPushButton(self.centralwidget)
        self.MicroRZed_down_button.setGeometry(QtCore.QRect(610, 380, 75, 75))
        self.MicroRZed_down_button.setText("▲")
        self.MicroRZed_down_button.setCheckable(True)
        self.MicroRZed_down_button.setFont(QtGui.QFont("Arial", 20))
        self.MicroRZed_down_button.clicked.connect(self.portSendDataMicRightZedYN)
        self.MicroRZed_down_button.clicked.connect(self.button_check)
        self.MicroRZed_down_button.setVisible(False)
        
        self.MicroRZed_down_button.setText("")
        self.MicroRZed_down_button.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2")))
        self.MicroRZed_down_button
        self.MicroRZed_down_button.setIconSize(QtCore.QSize(100, 100))

        #  #MicroR Zed left button
        #self.MicroRZed_left_button = QPushButton(self.centralwidget)
        # self.MicroRZed_left_button.setGeometry(QtCore.QRect(535, 305, 75, 75))
        # self.MicroRZed_left_button.setText("▲")
        # self.MicroRZed_left_button.setCheckable(True)
        # self.MicroRZed_left_button.setFont(QtGui.QFont("Arial", 20))
        # #Send Datası yok
        # self.MicroRZed_left_button.clicked.connect(self.button_check)
        # self.MicroRZed_left_button.setVisible(False)
        # self.MicroRZed_left_button.setStyleSheet("background-color: #d7d6e5;")
        # self.MicroRZed_left_button.setText("")
        # self.MicroRZed_left_button.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow")))
        # self.MicroRZed_left_button.setIconSize(QtCore.QSize(48, 48))

        #  #MicroR Zed right button
        # self.MicroRZed_right_button = QPushButton(self.centralwidget)
        # self.MicroRZed_right_button.setGeometry(QtCore.QRect(685, 305, 75, 75))
        # self.MicroRZed_right_button.setText("▲")
        # self.MicroRZed_right_button.setCheckable(True)
        # self.MicroRZed_right_button.setFont(QtGui.QFont("Arial", 20))
        # #Send Datası yok
        # self.MicroRZed_right_button.clicked.connect(self.button_check)
        # self.MicroRZed_right_button.setVisible(False)
        # self.MicroRZed_right_button.setStyleSheet("background-color: #d7d6e5;")
        # self.MicroRZed_right_button.setText("")
        # self.MicroRZed_right_button.setIcon(QtGui.QIcon(manager.get_image_path("rigtharrow")))
        # self.MicroRZed_right_button.setIconSize(QtCore.QSize(48, 48))

        # #Limit BUTTON
        self.limit_button = QPushButton(self.centralwidget)
        self.limit_button.setGeometry(QtCore.QRect(190, 00, 130, 50))
        self.limit_button.setText("▲")
        self.limit_button.setCheckable(True)
        self.limit_button.setFont(QtGui.QFont("Arial", 20))
        self.limit_button.clicked.connect(self.button_check_Move)
        self.limit_button.setVisible(False)
        self.limit_button.setStyleSheet("background-color: #0080FF; color: #FFFFFF;")
        self.limit_button.setText("Limit")
        self.limit_button.setIcon(QtGui.QIcon(""))
        self.limit_button
        self.limit_button.setIconSize(QtCore.QSize(48, 48))
        
        #Distance Button
        self.distance_button = QPushButton(self.centralwidget)
        self.distance_button.setGeometry(QtCore.QRect(290, 35, 130, 50))
        self.distance_button.setText("▲")
        self.distance_button.setCheckable(True)
        self.distance_button.setFont(QtGui.QFont("Arial", 20))
        self.distance_button.clicked.connect(self.button_check_Move) 
        self.distance_button.clicked.connect(self.button_check_Movedetail)
        self.distance_button.clicked.connect(self.distancehide)    
        self.distance_button.setVisible(True)
        self.distance_button.setText("Distance")
        self.distance_button.setStyleSheet("border : 2px solid black; border-radius :5px;")
        #Possition Button
        self.possition_button = QPushButton(self.centralwidget)
        self.possition_button.setGeometry(QtCore.QRect(440, 35, 130, 50))
        self.possition_button.setText("▲")
        self.possition_button.setCheckable(True)
        self.possition_button.setFont(QtGui.QFont("Arial", 20))
        self.possition_button.clicked.connect(self.possitionhide)
        self.possition_button.clicked.connect(self.button_check_Movedetail2)
        self.possition_button.clicked.connect(self.button_check_Move)
        self.possition_button.setVisible(True)
        self.possition_button.setStyleSheet("border : 2px solid black; border-radius :5px;")
        self.possition_button.setText("Position")
        


# Tehta Sağ Butonu
        self.Theta_right_button = QPushButton(self.centralwidget)
        self.Theta_right_button.setGeometry(QtCore.QRect(450, 730, 75, 75))
        self.Theta_right_button.setText("►")
        self.Theta_right_button.setCheckable(True)
        self.Theta_right_button.setFont(QtGui.QFont("Arial", 20))
        self.Theta_right_button.clicked.connect(self.portSendDataThetaXP)                 
        self.Theta_right_button.clicked.connect(self.button_check)
        self.Theta_right_button.setVisible(False)
        
        self.Theta_right_button.setText("")
        self.Theta_right_button.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2")))
        self.Theta_right_button
        self.Theta_right_button.setIconSize(QtCore.QSize(100, 100))
    #theta L sol
        self.Theta_left_button = QPushButton(self.centralwidget)
        self.Theta_left_button.setGeometry(QtCore.QRect(300, 730, 75, 75))
        self.Theta_left_button.setText("►")
        self.Theta_left_button.setCheckable(True)
        self.Theta_left_button.setFont(QtGui.QFont("Arial", 20))
        self.Theta_left_button.clicked.connect(self.portSendDataThetaXN)                 
        self.Theta_left_button.clicked.connect(self.button_check)
        self.Theta_left_button.setVisible(False)
        
        self.Theta_left_button.setText("")
        self.Theta_left_button.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2")))
        self.Theta_left_button
        self.Theta_left_button.setIconSize(QtCore.QSize(100, 100))

        
        #back button
        self.back_button= QPushButton(self.centralwidget)
        self.back_button.setGeometry(QtCore.QRect(100,900,70,30))
        self.back_button.setText("BACK")
        self.back_button.setFont(QtGui.QFont("Arial", 4))
        self.back_button.clicked.connect(self.back_button_setup)
        self.back_button.clicked.connect(self.portDisconnect)
        self.back_button.clicked.connect(MotorWindow.close)
        


          #system button
        self.system= QPushButton(self.centralwidget)
        self.system.setGeometry(QtCore.QRect(0,750,50,30))
        self.system.setText("Sys")
        self.system.setVisible(False)
        self.system.setFont(QtGui.QFont("Arial", 4))
        self.system.clicked.connect(self.openSystemControl)
        self.system.setStyleSheet("background-color: #36454F;")


        #ZED Butonu
        self.Zed_button = QPushButton(self.centralwidget)
        self.Zed_button.setGeometry(QtCore.QRect(620,620,150,75))
        self.Zed_button.setText("Zed")
        self.Zed_button.setVisible(True)
        self.Zed_button.setFont(QtGui.QFont("Times New Roman", 12))
        self.Zed_button.clicked.connect(self.zed_button_clicked)
        self.Zed_button.setStyleSheet("background-color: #FFFFFF; border : 2px solid black; border-radius : 20px;")
        self.Zed_button.clicked.connect(self.ButtonDisable)
        self.Zed_button.setCheckable(True)


        #Micro L Zed Button
        self.MicroLZed = QPushButton(self.centralwidget)
        self.MicroLZed.setGeometry(QtCore.QRect(300,400,150,75))
        self.MicroLZed.setText("Microscope Left ZED")
        self.MicroLZed.setVisible(True)
        self.MicroLZed.setFont(QtGui.QFont("Times New Roman", 8))
        self.MicroLZed.clicked.connect(self.MicroLZed_button_clicked)
        
        self.MicroLZed.clicked.connect(self.ButtonDisable)
        self.MicroLZed.setCheckable(True)

        #Micro R Zed Button
        self.MicroRZed = QPushButton(self.centralwidget)
        self.MicroRZed.setGeometry(QtCore.QRect(880,400,150,75))
        self.MicroRZed.setText("Microscope Right ZED")
        self.MicroRZed.setVisible(True)
        self.MicroRZed.setFont(QtGui.QFont("Times New Roman", 8))
        self.MicroRZed.clicked.connect(self.MicroRZed_button_clicked)
        
        self.MicroRZed.clicked.connect(self.ButtonDisable)
        self.MicroRZed.setCheckable(True)


       
        
        

        #port Butonu
        self.port_button = QPushButton(self.centralwidget)
        self.port_button.setGeometry(QtCore.QRect(100,30,70,30))
        self.port_button.setText("Port Open")
        self.port_button.setFont(QtGui.QFont("Times New Roman", 8))
        #self.port_button.clicked.connect(self.portConnect)
        self.port_button.setStyleSheet("background-color: transparent;  border : 2px solid black; border-radius :1px;")
        

        #microL Butonu
        self.MicroL_button = QPushButton(self.centralwidget)
        self.MicroL_button.setGeometry(QtCore.QRect(300,140,150,75))
        self.MicroL_button.setText("Microscope Left")
        self.MicroL_button.setVisible(True)
        self.MicroL_button.setFont(QtGui.QFont("Times New Roman", 8))
        self.MicroL_button.clicked.connect(self.MicroL_button_clicked)
        
        self.MicroL_button.clicked.connect(self.ButtonDisable)
        self.MicroL_button.setCheckable(True)



         #MicroS Butonu
        self.MicroS_button = QPushButton(self.centralwidget)
        self.MicroS_button.setGeometry(QtCore.QRect(880,140,150,75))
        self.MicroS_button.setText("Microscope Right")
        self.MicroS_button.setVisible(True)
        self.MicroS_button.setFont(QtGui.QFont("Times New Roman", 8))
        self.MicroS_button.clicked.connect(self.MicroS_button_clicked)
        
        self.MicroS_button.clicked.connect(self.ButtonDisable)
        self.MicroS_button.setCheckable(True)
        
        
        #Sample Butonu
        self.sample_button = QPushButton(self.centralwidget)
        self.sample_button.setGeometry(QtCore.QRect(740,730,150,75))
        self.sample_button.setText("Sample X/Y")
        self.sample_button.setVisible(True)
        self.sample_button.setFont(QtGui.QFont("Arial", 12))
        self.sample_button.clicked.connect(self.sample_button_clicked)
        self.sample_button.setStyleSheet("background-color: #FFFFFF;border : 2px solid black; border-radius : 20px;")
        self.sample_button.clicked.connect(self.ButtonDisable)
        self.sample_button.setCheckable(True)


       

        #Theta Butonu
        self.Theta_button = QPushButton(self.centralwidget)
        self.Theta_button.setGeometry(QtCore.QRect(860,620,150,75))
        self.Theta_button.setText("Theta")
        self.Theta_button.setVisible(True)
        self.Theta_button.setFont(QtGui.QFont("Arial", 12))
        self.Theta_button.clicked.connect(self.Theta_button_clicked)
        self.Theta_button.setStyleSheet("background-color: #FFFFFF;border : 2px solid black; border-radius : 20px;")
        self.Theta_button.clicked.connect(self.ButtonDisable)
        self.Theta_button.setCheckable(True)

        


        



        #HomePose Butonları
        self.button_HomeAxis = QPushButton(self.centralwidget)
        self.button_HomeAxis.setText("Homepos HOMESX")
        self.button_HomeAxis.setGeometry(300,150,100,35)
        self.button_HomeAxis.clicked.connect(self.send_butonHomePAxis)# Homepose eksenler butonu
        self.button_HomeAxis.setCheckable(True)
        

        self.button_HomeAxis1 = QPushButton("Homepos HOMESY", self.centralwidget)
        self.button_HomeAxis1.setGeometry(400,150,100,35)
        self.button_HomeAxis1.clicked.connect(self.send_butonHomePAxis1)# Homepose eksenler butonu
        self.button_HomeAxis1.setCheckable(True)
        

        self.button_HomeAxis2 = QPushButton("Homepos HOMESZ", self.centralwidget)
        self.button_HomeAxis2.setGeometry(500,150,100,35)
        self.button_HomeAxis2.clicked.connect(self.send_butonHomePAxis2)# Homepose eksenler butonu
        self.button_HomeAxis2.setCheckable(True)
        

        self.button_HomeAxis3 = QPushButton("Homepos HOMESTH", self.centralwidget)
        self.button_HomeAxis3.setGeometry(600,150,100,35)
        self.button_HomeAxis3.clicked.connect(self.send_butonHomePAxis3)# Homepose eksenler butonu
        self.button_HomeAxis3.setCheckable(True)
        

        self.button_HomeAxis4 = QPushButton("Homepos HOMEMRX", self.centralwidget)
        self.button_HomeAxis4.setGeometry(700,150,100,35)
        self.button_HomeAxis4.clicked.connect(self.send_butonHomePAxis4)# Homepose eksenler butonu
        self.button_HomeAxis4.setCheckable(True)
        

        self.button_HomeAxis5 = QPushButton("Homepos HOMEMRY", self.centralwidget)
        self.button_HomeAxis5.setGeometry(300,300,100,35)
        self.button_HomeAxis5.clicked.connect(self.send_butonHomePAxis5)# Homepose eksenler butonu
        self.button_HomeAxis5.setCheckable(True)
        

        self.button_HomeAxis6 = QPushButton("Homepos HOMEMLX", self.centralwidget)
        self.button_HomeAxis6.setGeometry(400,300,100,35)
        self.button_HomeAxis6.clicked.connect(self.send_butonHomePAxis6)# Homepose eksenler butonu
        self.button_HomeAxis6.setCheckable(True)
        

        self.button_HomeAxis7 = QPushButton("Homepos HOMEMLY", self.centralwidget)
        self.button_HomeAxis7.setGeometry(500,300,100,35)
        self.button_HomeAxis7.clicked.connect(self.send_butonHomePAxis7)# Homepose eksenler butonu
        self.button_HomeAxis7.setCheckable(True)
        

        self.button_HomeAxis8 = QPushButton("Homepos HOMEMRZ", self.centralwidget)
        self.button_HomeAxis8.setGeometry(600,300,100,35)
        self.button_HomeAxis8.clicked.connect(self.send_butonHomePAxis8)# Homepose eksenler butonu
        self.button_HomeAxis8.setCheckable(True)
        

        self.button_HomeAxis9 = QPushButton("Homepos HOMEMLZ", self.centralwidget)
        self.button_HomeAxis9.setGeometry(700,300,100,35)
        self.button_HomeAxis9.clicked.connect(self.send_butonHomePAxis9)# Homepose eksenler butonu
        self.button_HomeAxis9.setCheckable(True)
        

        self.button_HomeAxis10 = QPushButton("HOMESXY", self.centralwidget)
        self.button_HomeAxis10.setGeometry(300,430,100,35)
        self.button_HomeAxis10.clicked.connect(self.send_butonHomePAxis10)# Homepose eksenler butonu
        self.button_HomeAxis10.setCheckable(True)
        

        self.button_HomeAxis11 = QPushButton("HOMEMRXY", self.centralwidget)
        self.button_HomeAxis11.setGeometry(400,430,100,35)
        self.button_HomeAxis11.clicked.connect(self.send_butonHomePAxis11)# Homepose eksenler butonu
        self.button_HomeAxis11.setCheckable(True)
        

        self.button_HomeAxis12 = QPushButton("HOMEMLXY", self.centralwidget)
        self.button_HomeAxis12.setGeometry(500,430,100,35)
        self.button_HomeAxis12.clicked.connect(self.send_butonHomePAxis12)# Homepose eksenler butonu
        self.button_HomeAxis12.setCheckable(True)
        

        self.button_HomeAxis13 = QPushButton("HOMESYSTM", self.centralwidget)
        self.button_HomeAxis13.setGeometry(600,430,100,35)
        self.button_HomeAxis13.clicked.connect(self.send_butonHomePAxis13)# Homepose eksenler butonu
        self.button_HomeAxis13.setCheckable(True)
        


        #Light Buttons
        self.button_light = QPushButton(self.centralwidget)
        self.button_light.setText("Light ON")
        self.button_light.setGeometry(350,650,150,70)
        self.button_light.clicked.connect(self.send_light_ON)# Homepose eksenler butonu
        self.button_light.setCheckable(True)
        

        self.button_Exposure = QPushButton(self.centralwidget)
        self.button_Exposure.setText("Exposure")
        self.button_Exposure.setGeometry(300,580,150,50)
        self.button_Exposure.clicked.connect(self.send_Exposure)
        self.button_Exposure.setCheckable(True)
        

        #ExpEnergy
        self.button_ExpEnergy = QPushButton(self.centralwidget)
        self.button_ExpEnergy.setText("ExpEnergy")
        self.button_ExpEnergy.setGeometry(500,580,100,50)
        self.button_ExpEnergy.clicked.connect(self.send_ExpEnergy)# Homepose eksenler butonu
        self.button_ExpEnergy.setCheckable(True)
        self.button_ExpEnergy.setVisible(False)
        


        self.verticalLayoutWidget_ExpEnergy = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_ExpEnergy.setGeometry(QtCore.QRect(500, 640, 110, 40))
        self.verticalLayoutWidget_ExpEnergy.setObjectName("verticalLayoutWidget_ExpEnergy")
        self.verticalLayoutWidget_ExpEnergy.setStyleSheet("background-color: transparent; color: #36454F")                                  #õlabels
        self.verticalLayout_ExpEnergy = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_ExpEnergy)
        self.verticalLayout_ExpEnergy.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_ExpEnergy.setObjectName("verticalLayout_ExpEnergy")
        self.label_ExpEnergy = QtWidgets.QLabel(self.verticalLayoutWidget_ExpEnergy)
        self.label_ExpEnergy.setObjectName("label_ExpEnergy")
        self.verticalLayout_ExpEnergy.addWidget(self.label_ExpEnergy)


        #ExpPower   
        self.button_ExpPower = QPushButton(self.centralwidget)
        self.button_ExpPower.setText("ExpPower")
        self.button_ExpPower.setGeometry(650,580,100,50)
        self.button_ExpPower.clicked.connect(self.send_ExpPower)# Homepose eksenler butonu
        self.button_ExpPower.setCheckable(True)
        self.button_ExpPower.setVisible(False)
        

        self.verticalLayoutWidget_ExpPower = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_ExpPower.setGeometry(QtCore.QRect(650, 640, 110, 40))
        self.verticalLayoutWidget_ExpPower.setObjectName("verticalLayoutWidget_ExpPower")
        self.verticalLayoutWidget_ExpPower.setStyleSheet("background-color: transparent; color: #36454F")                                  #õlabels
        self.verticalLayout_ExpPower = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_ExpPower)
        self.verticalLayout_ExpPower.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_ExpPower.setObjectName("verticalLayout_ExpPower")
        self.label_ExpPower = QtWidgets.QLabel(self.verticalLayoutWidget_ExpPower)
        self.label_ExpPower.setObjectName("label_ExpPower")
        self.verticalLayout_ExpPower.addWidget(self.label_ExpPower)

        

        #send data
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(300, 750, 300, 23))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lineEditSendData = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.lineEditSendData.setObjectName("lineEditSendData")
        self.verticalLayout.addWidget(self.lineEditSendData)
        self.verticalLayoutWidget.setStyleSheet("background-color: transparent;")
        self.lineEditSendData.setStyleSheet("background-color: white; border: 2px solid black; border-radius: 5px; font-weight: bold; font-size: 14px; color: black;")
        
        
        

        #send data2
        self.verticalLayoutWidget_8 =QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_8.setGeometry(QtCore.QRect(300, 780, 300, 23))
        self.verticalLayoutWidget_8.setObjectName("verticalLayoutWidget")
        self.verticalLayoutWidget_8.setStyleSheet("background-color: transparent;")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_8)
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_8.setObjectName("verticalLayout")
        self.lineEditSendData_2 = QtWidgets.QLineEdit(self.verticalLayoutWidget_8)
        self.lineEditSendData_2.setObjectName("verticalLayout_8")
        self.verticalLayout_8.addWidget(self.lineEditSendData_2)
        self.lineEditSendData_2.setStyleSheet("background-color: white; border: 2px solid black; border-radius: 5px; font-weight: bold; font-size: 14px; color: black;")

        #      send exp data  
        self.verticalLayoutWidget_exp = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_exp.setGeometry(QtCore.QRect(300, 810, 100, 23))
        self.verticalLayoutWidget_exp.setObjectName("verticalLayoutWidget_exp")
        self.verticalLayout_exp = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_exp)
        self.verticalLayout_exp.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_exp.setObjectName("verticalLayout")
        self.lineEditSendData_exp = QtWidgets.QLineEdit(self.verticalLayoutWidget_exp)
        self.lineEditSendData_exp.setObjectName("lineEditSendData_exp")
        self.lineEditSendData_exp.setText("80")
        self.verticalLayout_exp.addWidget(self.lineEditSendData_exp)
        self.verticalLayoutWidget_exp.setStyleSheet("background-color: transparent;")
        self.lineEditSendData_exp.setStyleSheet("background-color: white; border: 2px solid black; border-radius: 5px; font-weight: bold; font-size: 14px; color: black;")


        


        # ==========================================================
        # Unified Log Text Box (Replaces scattered textEditReciveData)
        # ==========================================================
        self.verticalLayoutWidget_Energy = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_Energy.setObjectName("verticalLayoutWidget_Energy")
        self.verticalLayoutWidget_Energy.setStyleSheet("background-color: transparent; color: #36454F")  
        self.verticalLayout_Energy = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_Energy)
        self.verticalLayout_Energy.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_Energy.addWidget(self.bufferEnergy)

        self.verticalLayoutWidget_Power = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_Power.setObjectName("verticalLayoutWidget_Power")
        self.verticalLayoutWidget_Power.setStyleSheet("background-color: transparent; color: #36454F")  
        self.verticalLayout_Power = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_Power)
        self.verticalLayout_Power.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_Power.addWidget(self.bufferPower)

        self.verticalLayoutWidget_18 = QtWidgets.QWidget(self.centralwidget)
        # The position will be updated in _reposition_and_show
        self.verticalLayoutWidget_18.setGeometry(QtCore.QRect(300, 840, 250, 100))
        self.verticalLayoutWidget_18.setObjectName("verticalLayoutWidget_18")
        self.verticalLayoutWidget_18.setStyleSheet("background-color: transparent; border : 1px solid #444; border-radius : 5px")  
        self.verticalLayout_18 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_18)
        self.verticalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.mainLogBox = QtWidgets.QTextEdit(self.verticalLayoutWidget_18)
        self.mainLogBox.setObjectName("mainLogBox")
        self.mainLogBox.setReadOnly(True)
        self.mainLogBox.setStyleSheet("background-color: #1a1a2e; color: #ddd; font-family: Consolas; font-size: 11px;")
        self.verticalLayout_18.addWidget(self.mainLogBox)
        
        # Keep bufferTxt hidden/separate if it was used programmatically
        self.bufferTxt.setVisible(False)
        self.verticalLayout_18.addWidget(self.bufferTxt)






      
### Lightning McQueen #

        _SLIDER_STYLE = """
QSlider::groove:horizontal {
    border: 1px solid #444;
    height: 8px;
    background: #2a2a3e;
    border-radius: 4px;
    margin: 2px 0;
}
QSlider::handle:horizontal {
    background: #4a90d9;
    border: 1px solid #357ab8;
    width: 18px;
    height: 18px;
    margin: -5px 0;
    border-radius: 9px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #357ab8, stop:1 #4a90d9);
    border-radius: 4px;
}
"""
        _PROGRESSBAR_STYLE = """
QProgressBar {
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #1a1a2e;
    color: #ffffff;
    text-align: center;
    font-size: 11px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #357ab8, stop:1 #4a90d9);
    border-radius: 3px;
}
"""
        _SW = 170   # tüm slider'lar için eşit genişlik
        _SH = 68    # tüm slider'lar için eşit yükseklik
        _SLIDER_BG = "background-color: transparent; color: #FFFFFF"

        # Örnek 3
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(520, 500, _SW, _SH))
        self.verticalLayoutWidget_3.setStyleSheet(_SLIDER_BG)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_3.setSpacing(6)

        self.progress_bar_3 = QtWidgets.QProgressBar(self.verticalLayoutWidget_3)
        self.progress_bar_3.setStyleSheet(_PROGRESSBAR_STYLE)
        self.progress_bar_3.setFixedHeight(18)
        self.slider_3 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.verticalLayoutWidget_3)
        self.slider_3.setStyleSheet(_SLIDER_STYLE)
        self.slider_3.setRange(0, 100)
        self.slider_3.setFixedHeight(30)
        self.slider_3.valueChanged.connect(self.update_progress_bar)
        self.slider_3.valueChanged.connect(self.update_motor_speed3)

        self.verticalLayout_3.addWidget(self.progress_bar_3)
        self.verticalLayout_3.addWidget(self.slider_3)

        # Örnek 4
        self.verticalLayoutWidget_4 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_4.setGeometry(QtCore.QRect(520, 880, _SW, _SH))
        self.verticalLayoutWidget_4.setStyleSheet(_SLIDER_BG)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout_4.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_4.setSpacing(6)

        self.progress_bar_4 = QtWidgets.QProgressBar(self.verticalLayoutWidget_4)
        self.progress_bar_4.setStyleSheet(_PROGRESSBAR_STYLE)
        self.progress_bar_4.setFixedHeight(18)
        self.slider_4 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.verticalLayoutWidget_4)
        self.slider_4.setStyleSheet(_SLIDER_STYLE)
        self.slider_4.setRange(0, 100)
        self.slider_4.setFixedHeight(30)
        self.slider_4.valueChanged.connect(self.update_progress_bar)
        self.slider_4.valueChanged.connect(self.update_motor_speed4)

        self.verticalLayout_4.addWidget(self.progress_bar_4)
        self.verticalLayout_4.addWidget(self.slider_4)

        #Light 1
        self.verticalLayoutWidget_Light = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_Light.setGeometry(QtCore.QRect(300, 300, _SW, _SH))
        self.verticalLayoutWidget_Light.setStyleSheet(_SLIDER_BG)
        self.verticalLayout_Light = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_Light)
        self.verticalLayout_Light.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_Light.setSpacing(6)

        self.progress_bar_Light = QtWidgets.QProgressBar(self.verticalLayoutWidget_Light)
        self.progress_bar_Light.setStyleSheet(_PROGRESSBAR_STYLE)
        self.progress_bar_Light.setFixedHeight(18)
        self.slider_Light = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.verticalLayoutWidget_Light)
        self.slider_Light.setStyleSheet(_SLIDER_STYLE)
        self.slider_Light.setRange(0, 100)
        self.slider_Light.setFixedHeight(30)
        self.slider_Light.valueChanged.connect(self.update_progress_bar)
        self.slider_Light.valueChanged.connect(self.update_Light_degree)

        self.verticalLayout_Light.addWidget(self.progress_bar_Light)
        self.verticalLayout_Light.addWidget(self.slider_Light)

        #Light 2
        self.verticalLayoutWidget_Light2 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_Light2.setGeometry(QtCore.QRect(850, 300, _SW, _SH))
        self.verticalLayoutWidget_Light2.setStyleSheet(_SLIDER_BG)
        self.verticalLayout_Light2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_Light2)
        self.verticalLayout_Light2.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_Light2.setSpacing(6)

        self.progress_bar_Light2 = QtWidgets.QProgressBar(self.verticalLayoutWidget_Light2)
        self.progress_bar_Light2.setStyleSheet(_PROGRESSBAR_STYLE)
        self.progress_bar_Light2.setFixedHeight(18)
        self.slider_Light2 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.verticalLayoutWidget_Light2)
        self.slider_Light2.setStyleSheet(_SLIDER_STYLE)
        self.slider_Light2.setRange(0, 100)
        self.slider_Light2.setFixedHeight(30)
        self.slider_Light2.valueChanged.connect(self.update_progress_bar)
        self.slider_Light2.valueChanged.connect(self.update_Light2_degree)

        self.verticalLayout_Light2.addWidget(self.progress_bar_Light2)
        self.verticalLayout_Light2.addWidget(self.slider_Light2)
  

        
        # self.verticalLayout_3.addWidget(self.bufferMRXPOS)
        

        ############################################################################
        # self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.centralwidget)
        # self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(780, 195, 60, 30))
        # self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_4")
        # self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        # self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        # self.verticalLayout_3.setObjectName("verticalLayout_4")
        # self.new_data_received = QtWidgets.QTextEdit(self.verticalLayoutWidget_3)
        # self.new_data_received.setObjectName("textEditReciveData")
        # self.verticalLayout_3.addWidget(self.bufferMRXPOS)
        ############################################################################

        self.verticalLayoutWidget_11 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_11.setGeometry(QtCore.QRect(300, 210, 110, 40))
        self.verticalLayoutWidget_11.setObjectName("verticalLayoutWidget_2")
        self.verticalLayoutWidget_11.setStyleSheet("background-color: transparent; color: #36454F")                                  #õlabels
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_11)
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_11.setObjectName("verticalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.verticalLayoutWidget_11)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_11.addWidget(self.label_3)

        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(300, 240, 110, 40))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setStyleSheet("background-color: transparent; color: #36454F")                                   #õlabels
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)

        self.verticalLayoutWidget_5 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_5.setGeometry(QtCore.QRect(880, 205, 110, 40))
        self.verticalLayoutWidget_5.setObjectName("verticalLayoutWidget_2") 
        self.verticalLayoutWidget_5.setStyleSheet("background-color: transparent; color: #36454F")                                  #õlabels
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_5)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_4 = QtWidgets.QLabel(self.verticalLayoutWidget_5)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_5.addWidget(self.label_4)

        self.verticalLayoutWidget_6 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_6.setGeometry(QtCore.QRect(880, 235, 110, 40))
        self.verticalLayoutWidget_6.setObjectName("verticalLayoutWidget_6")  
        self.verticalLayoutWidget_6.setStyleSheet("background-color: transparent; color: #36454F")                                 #õlabels
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_6)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_5 = QtWidgets.QLabel(self.verticalLayoutWidget_6)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_6.addWidget(self.label_5)


        self.verticalLayoutWidget_7 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_7.setGeometry(QtCore.QRect(300, 475, 110, 40))
        self.verticalLayoutWidget_7.setObjectName("verticalLayoutWidget_7")
        self.verticalLayoutWidget_7.setStyleSheet("background-color: transparent; color: #36454F")                                  #õlabels
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_7)
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label_6 = QtWidgets.QLabel(self.verticalLayoutWidget_7)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_7.addWidget(self.label_6)

        self.verticalLayoutWidget_15 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_15.setGeometry(QtCore.QRect(880, 475, 110, 40))
        self.verticalLayoutWidget_15.setObjectName("verticalLayoutWidget_15")    
        self.verticalLayoutWidget_15.setStyleSheet("background-color: transparent; color: #36454F")                               #õlabels
        self.verticalLayout_15 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_15)
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.label_7 = QtWidgets.QLabel(self.verticalLayoutWidget_15)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_15.addWidget(self.label_7)

        self.verticalLayoutWidget_16 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_16.setGeometry(QtCore.QRect(550, 690, 130, 40))
        self.verticalLayoutWidget_16.setObjectName("verticalLayoutWidget_16")  
        self.verticalLayoutWidget_16.setStyleSheet("background-color: transparent; color: #36454F")                                 #õlabels
        self.verticalLayout_16 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_16)
        self.verticalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.label_8 = QtWidgets.QLabel(self.verticalLayoutWidget_16)
        self.label_8.setObjectName("label_8")
        self.verticalLayout_16.addWidget(self.label_8)

        self.verticalLayoutWidget_17 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_17.setGeometry(QtCore.QRect(780, 690, 130, 40))
        self.verticalLayoutWidget_17.setObjectName("verticalLayoutWidget_17")      
        self.verticalLayoutWidget_17.setStyleSheet("background-color: transparent; color: #36454F")                             #õlabels
        self.verticalLayout_17 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_17)
        self.verticalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_17.setObjectName("verticalLayout_17")
        self.label_9 = QtWidgets.QLabel(self.verticalLayoutWidget_17)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_17.addWidget(self.label_9)

        self.verticalLayoutWidget_20 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_20.setGeometry(QtCore.QRect(710, 795, 110, 40))
        self.verticalLayoutWidget_20.setObjectName("verticalLayoutWidget_20")      
        self.verticalLayoutWidget_20.setStyleSheet("background-color: transparent; color: #36454F")                            #õlabels
        self.verticalLayout_20 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_20)
        self.verticalLayout_20.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_20.setObjectName("verticalLayout_20")
        self.label_10 = QtWidgets.QLabel(self.verticalLayoutWidget_20)
        self.label_10.setObjectName("label_10")
        self.verticalLayout_20.addWidget(self.label_10)

        self.verticalLayoutWidget_19 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_19.setGeometry(QtCore.QRect(710, 820, 110, 40))
        self.verticalLayoutWidget_19.setObjectName("verticalLayoutWidget_19")      
        self.verticalLayoutWidget_19.setStyleSheet("background-color: transparent; color: #36454F")                             #õlabels
        self.verticalLayout_19 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_19)
        self.verticalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_19.setObjectName("verticalLayout_19")
        self.label_11 = QtWidgets.QLabel(self.verticalLayoutWidget_19)
        self.label_11.setObjectName("label_11")
        self.verticalLayout_19.addWidget(self.label_11)

     
   

      

        # self.verticalLayoutWidget_9 = QtWidgets.QWidget(self.centralwidget)
        # self.verticalLayoutWidget_9.setGeometry(QtCore.QRect(750, 220, 60, 40))
        # self.verticalLayoutWidget_9.setObjectName("verticalLayoutWidget_9")                                 #õlabels
        # self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_9)
        # self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        # self.verticalLayout_9.setObjectName("verticalLayout_9")
        # self.label_7 = QtWidgets.QLabel(self.verticalLayoutWidget_9)
        # self.label_7.setObjectName("label_7")
        # self.verticalLayout_9.addWidget(self.label_7)

        
############################################################################
        

    

############################################################################

        #Portun bağlantısını gösteriyor
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(100, 70, 70, 20))
        self.comboBox.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius: 5px;")


        serial_mgr.data_received.connect(self._process_binary_command)        


        self.listSerialPorts()
        
  

        MotorWindow.setCentralWidget(self.centralwidget)
        
        self.retranslateUi(MotorWindow)
        QtCore.QMetaObject.connectSlotsByName(MotorWindow)

        # ── Tüm butonların başlangıç stilini uygula (siyah/kapalı) ──
        self._apply_initial_button_styles()


    # ═══════════════════════════════════════════════════════════
    # LAYOUT YENİDEN DÜZENLEME — Final, güvenilir versiyon
    # ═══════════════════════════════════════════════════════════

    def _reposition_and_show(self):
        """
        Tüm widget'ları sol panel genişliğine (self._layout_left_w) göre yeniden
        konumlandırır. Sayfa set'lerini (set yapısı) oluşturup show_page(1) çağırır.
        Hiçbir sinyal/veri bozulmaz.
        """
        G   = 8
        L   = self._layout_left_w    # Sol panel px genişliği
        H   = self._layout_sh        # Ekran yüksekliği
        TOP = self._layout_top_h     # Üst çubuk yüksekliği (95)
        TAB = self._layout_tab_h     # Alt tab çubuğu (60)

        # ── Yardımcı: buffer/label'ın parent container'ını bul ──
        def _c(attr):
            w = getattr(self, attr, None)
            if w:
                p = w.parentWidget()
                if p and p is not self.centralwidget:
                    return p
            return None

        def _collect(*attrs):
            s = set()
            for a in attrs:
                c = getattr(self, a, None)
                if c:
                    p = c.parentWidget()
                    if p and p is not self.centralwidget:
                        s.add(p)
                    else:
                        s.add(c)
            return s

        # ════════════════════════════════════════════════════════
        # SAYFA 1  —  Motor Kontrol
        # ════════════════════════════════════════════════════════

        # Satır 1: 4 Microscope seçim butonu
        R1W = (L - 5*G) // 4
        R1H = 65
        R1Y = TOP + G
        for i, btn in enumerate([self.MicroL_button, self.MicroS_button,
                                   self.MicroLZed, self.MicroRZed]):
            btn.setGeometry(G + i*(R1W+G), R1Y, R1W, R1H)

        # Satır 2: 3 büyük motor seçim butonu
        R2W = (L - 4*G) // 3
        R2H = 85
        R2Y = R1Y + R1H + G
        for i, btn in enumerate([self.Zed_button, self.Theta_button, self.sample_button]):
            btn.setGeometry(G + i*(R2W+G), R2Y, R2W, R2H)

        # İçerik alanı başlangıcı
        CY  = R2Y + R2H + 20
        DPW = int(L * 0.20)   # Distance/Position Buton Genişliği
        INPUT_W = int(L * 0.15) # Veri kutusu genişliği
        DPH = 50

        # Distance / Position / Limit (Sol kolon yan yana)
        self.distance_button.setGeometry (G, CY, DPW, DPH)
        self.verticalLayoutWidget.setGeometry(G + DPW + G, CY + (DPH-34)//2, INPUT_W, 34)

        CY += DPH + G
        self.possition_button.setGeometry(G, CY, DPW, DPH)
        self.verticalLayoutWidget_8.setGeometry(G + DPW + G, CY + (DPH-34)//2, INPUT_W, 34)

        CY += DPH + G
        self.limit_button.setGeometry(G, CY, DPW + G + INPUT_W, DPH)

        # Bottom Panel Constraints (Grid array of 10 Data Monitor blocks horizontally spanning L)
        BUF_Y_START = H - TAB - G - 160
        BUF_COL_W = max(50, (L - 6*G) // 5)
        BUF_H = 26
        BUF_ROW_GAP = 12

        buf_pairs = [
            ('verticalLayoutWidget_11', 'bufferMLXPOS'),  # MLXPOS
            ('verticalLayoutWidget_2',  'bufferMLYPOS'),  # MLYPOS
            ('verticalLayoutWidget_7',  'bufferMLZPOS'),  # MLZPOS
            ('verticalLayoutWidget_5',  'bufferMRXPOS'),  # MRXPOS
            ('verticalLayoutWidget_6',  'bufferMRYPOS'),  # MRYPOS
            ('verticalLayoutWidget_15', 'bufferMRZPOS'),  # MRZPOS
            ('verticalLayoutWidget_16', 'bufferSZPOS'),   # Sample Zed
            ('verticalLayoutWidget_17', 'bufferSTPOS'),   # Sample Theta
            ('verticalLayoutWidget_20', 'bufferSXPOS'),   # Sample X
            ('verticalLayoutWidget_19', 'bufferSYPOS'),   # Sample Y
        ]

        for idx, (lbl_attr, buf_attr) in enumerate(buf_pairs):
            r = idx // 5
            c = idx % 5
            bx = G + c*(BUF_COL_W + G)
            by = BUF_Y_START + r*(2*BUF_H + BUF_ROW_GAP)
            
            lc = getattr(self, lbl_attr, None)
            if lc: lc.setGeometry(bx, by, BUF_COL_W, BUF_H)
            
            bc = getattr(self, buf_attr, None)
            if bc:
                bc.setParent(self.centralwidget)
                bc.setGeometry(bx, by + BUF_H, BUF_COL_W, BUF_H)
                bc.setStyleSheet("background-color: transparent; border: 2px solid black; border-radius: 4px; font-weight: bold; font-size: 15px; color: black;")
                bc.setVisible(True)

        # Right Panel Constraints (Sliders shifted here with auto-generated labels)
        SLIDER_W = min(220, int(L * 0.25))
        SLIDER_X = L - SLIDER_W - G
        SLY = R2Y + R2H + 20

        slider_labels = ["Motor Speed 1", "Motor Speed 2", "Light Intensity 1", "Light Intensity 2"]
        slider_widgets = ['verticalLayoutWidget_3', 'verticalLayoutWidget_4', 'verticalLayoutWidget_Light', 'verticalLayoutWidget_Light2']
        
        for i, attr in enumerate(slider_widgets):
            lbl_name = f"_dynamic_slider_lbl_{i}"
            if not hasattr(self, lbl_name):
                lbl = QtWidgets.QLabel(self.centralwidget)
                lbl.setStyleSheet("color: #36454F; font-weight: bold; font-size: 13px;") 
                lbl.setAlignment(QtCore.Qt.AlignCenter)
                lbl.setText(slider_labels[i])
                setattr(self, lbl_name, lbl)
                if hasattr(self, '_page1_set'):
                    self._page1_set.add(lbl)
                elif hasattr(self, '_always_set'):
                    self._always_set.add(lbl)
            
            lbl = getattr(self, lbl_name)
            lbl.setGeometry(SLIDER_X, SLY, SLIDER_W, 25)
            
            w = getattr(self, attr, None)
            if w:
                w.setGeometry(SLIDER_X, SLY + 25, SLIDER_W, 55)
            SLY += 90

        # Ok tuşu pad merkezi (Sol-orta alanın the residual spacei)
        PAD_MID = (G + DPW + G + INPUT_W + SLIDER_X) // 2
        PCX = PAD_MID
        PCY = (R2Y + R2H + 20 + BUF_Y_START) // 2
        AW = AH = 85

        UP_X = PCX - AW // 2;       UP_Y = PCY - AH - AH // 2
        DN_X = PCX - AW // 2;       DN_Y = PCY + AH // 2
        LT_X = PCX - AH - AW // 2;  LT_Y = PCY - AH // 2
        RT_X = PCX + AW // 2;       RT_Y = PCY - AH // 2

        for btn in [self.zed_up_button,    self.sample_up_button,
                    self.MicroL_up_button,  self.MicroS_up_button,
                    self.MicroLZed_up_button, self.MicroRZed_up_button]:
            btn.setGeometry(UP_X, UP_Y, AW, AH)
        for btn in [self.zed_down_button,    self.sample_down_button,
                    self.MicroL_down_button,  self.MicroS_down_button,
                    self.MicroLZed_down_button, self.MicroRZed_down_button]:
            btn.setGeometry(DN_X, DN_Y, AW, AH)
        for btn in [self.sample_left_button, self.MicroL_left_button,
                    self.MicroS_left_button,  self.Theta_left_button]:
            btn.setGeometry(LT_X, LT_Y, AW, AH)
        for btn in [self.sample_right_button, self.MicroL_right_button,
                    self.MicroS_right_button,  self.Theta_right_button]:
            btn.setGeometry(RT_X, RT_Y, AW, AH)

        # Logo (sayfa 1)
        if hasattr(self, 'logoLabelup'):
            self.logoLabelup.setGeometry(PCX - 85, PCY + (AH//2) + AH + 20, 170, 55)

        # ════════════════════════════════════════════════════════
        # SAYFA 2  —  Valfler / Home
        # ════════════════════════════════════════════════════════

        # ════════════════════════════════════════════════════════
        # LAYER 1: Valfler (Left 35%) / Home & Keep Holder (Right 65%)
        # ════════════════════════════════════════════════════════
        VALF_W = int(L * 0.35)
        HOME_W = L - VALF_W
        
        BW = max(80, (VALF_W - 3*G) // 2)
        BH = 48
        LABEL_H = 22
        ROW_H = BH + LABEL_H + G
        
        VC1 = G
        VC2 = VC1 + BW + G
        
        # Remove EMPTYSEL (button_valfler9)
        self.button_valfler9.setVisible(False)
        valf_L = [self.button_valfler, self.button_valfler1, self.button_valfler2, self.button_valfler3]
        valf_L_labels = ['image_labelMASKVAC','image_labelSAMPVAC','image_labelSMPHVAC','image_labelMSKHVAC']
        
        valf_R = [self.button_valfler8, self.button_valfler4, self.button_valfler5, self.button_valfler6, self.button_valfler7]
        valf_R_labels = ['image_labelRINGSEL','image_labelSAMPFSEL','image_labelCONTVAC','image_labelWECSEL','image_labelOPTIVAC']

        for i, btn in enumerate(valf_L):
            vy = TOP + G + i*ROW_H
            btn.setGeometry(VC1, vy, BW, BH)
            if i < len(valf_L_labels) and valf_L_labels[i]:
                c = _c(valf_L_labels[i])
                if c: c.setGeometry(VC1, vy + BH + 2, BW, LABEL_H)
                lbl = getattr(self, valf_L_labels[i], None)
                if lbl:
                    lbl.setAlignment(QtCore.Qt.AlignCenter)
                    lbl.setText("STANDBY")

        for i, btn in enumerate(valf_R):
            vy = TOP + G + i*ROW_H
            btn.setGeometry(VC2, vy, BW, BH)
            if i < len(valf_R_labels) and valf_R_labels[i]:
                c = _c(valf_R_labels[i])
                if c: c.setGeometry(VC2, vy + BH + 2, BW, LABEL_H)
                lbl = getattr(self, valf_R_labels[i], None)
                if lbl:
                    lbl.setAlignment(QtCore.Qt.AlignCenter)
                    lbl.setText("STANDBY")

        # Home Axis grid (Right side)
        HX = VALF_W + G
        HBW = max(80, (HOME_W - 6*G) // 5)
        
        home_rows = [
            [self.button_HomeAxis,   self.button_HomeAxis1,  self.button_HomeAxis2, self.button_HomeAxis3,  self.button_HomeAxis4],
            [self.button_HomeAxis5,  self.button_HomeAxis6,  self.button_HomeAxis7, self.button_HomeAxis8,  self.button_HomeAxis9],
            [self.button_HomeAxis10, self.button_HomeAxis11, self.button_HomeAxis12, self.button_HomeAxis13],
            [self.button_KeepHolder, self.button_ContactPos, self.button_Gap]
        ]
        hmc_grid = [
            ['image_labelHOMESX',  'image_labelHOMESY',   'image_labelHOMESZ', 'image_labelHOMESTH', 'image_labelHOMEMRX'],
            ['image_labelHOMEMRY', 'image_labelHOMEMLX',  'image_labelHOMEMLY', 'image_labelHOMEMRZ', 'image_labelHOMEMLZ'],
            ['image_labelHOMESXY', 'image_labelHOMEMRXY', 'image_labelHOMEMLXY', 'image_labelHOMESTH2'],
            ['image_labelKEEPHSTAT','image_labelCONTPSTAT','image_labelGAPPOSSTAT']
        ]

        Y_CURSOR = TOP + G
        for ri, row in enumerate(home_rows):
            for ci, btn in enumerate(row):
                btn.setGeometry(HX + ci*(HBW+G), Y_CURSOR, HBW, BH)
                if ri < len(hmc_grid) and ci < len(hmc_grid[ri]):
                    attr = hmc_grid[ri][ci]
                    c = _c(attr)
                    if c: c.setGeometry(HX + ci*(HBW+G), Y_CURSOR + BH + 2, HBW, LABEL_H)
                    lbl = getattr(self, attr, None)
                    if lbl:
                        lbl.setAlignment(QtCore.Qt.AlignCenter)
                        lbl.setText("STANDBY")
            Y_CURSOR += ROW_H + G

        # ════════════════════════════════════════════════════════
        # LAYER 2: Exposure & Light (Orta Katman)
        # ════════════════════════════════════════════════════════
        EXP_Y = max(TOP + G + 5*ROW_H, Y_CURSOR) + 15
        EX_BW = min(200, (L - 4*G) // 3)
        EX_BH = 50

        # Exposure row
        self.button_Exposure.setGeometry(G, EXP_Y, EX_BW, EX_BH)
        self.verticalLayoutWidget_exp.setGeometry(G + EX_BW + G, EXP_Y + (EX_BH-26)//2, EX_BW, 26)
        
        self.button_ExpEnergy.setVisible(False)
        self.verticalLayoutWidget_ExpEnergy.setGeometry(L//2, EXP_Y + (EX_BH-26)//2, EX_BW, 26)
        self.verticalLayoutWidget_Energy.setGeometry(L//2 + EX_BW + G, EXP_Y + (EX_BH-26)//2, EX_BW, 26)
        lbl_en = getattr(self, 'label_ExpEnergy', None)
        if lbl_en: lbl_en.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)

        # Light row
        EXP_Y2 = EXP_Y + EX_BH + 15
        self.button_light.setGeometry(G, EXP_Y2, EX_BW, EX_BH)
        
        self.button_ExpPower.setVisible(False)
        self.verticalLayoutWidget_ExpPower.setGeometry(L//2, EXP_Y2 + (EX_BH-26)//2, EX_BW, 26)
        self.verticalLayoutWidget_Power.setGeometry(L//2 + EX_BW + G, EXP_Y2 + (EX_BH-26)//2, EX_BW, 26)
        lbl_pow = getattr(self, 'label_ExpPower', None)
        if lbl_pow: lbl_pow.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)

        # ════════════════════════════════════════════════════════
        # LAYER 3: Mode & Port (Left) / Txt (Right) at Bottom
        # ════════════════════════════════════════════════════════
        BOTTOM_Y = H - TAB - 20
        
        # Txt box (Right)
        TXT_H = 180
        TXT_W = int(L * 0.55)
        self.verticalLayoutWidget_18.setGeometry(L - TXT_W - G, BOTTOM_Y - TXT_H, TXT_W, TXT_H)

        # Mode & Port (Left)
        MW = int(L * 0.35)
        MH = 44
        MODE_START_Y = BOTTOM_Y - (4*MH + 3*G)
        
        self.port_button.setGeometry(G, MODE_START_Y, 80, MH)
        self.comboBox.setGeometry(G + 90, MODE_START_Y, 110, MH)
        
        self.button_testmode_back.setGeometry(G, MODE_START_Y + MH + G, MW, MH)
        self.button_joymode.setGeometry(G, MODE_START_Y + 2*(MH + G), MW, MH)
        self.back_button.setGeometry(G, MODE_START_Y + 3*(MH + G), MW, MH)

        # Kamera butonları (sayfa 2)
        # self.camera_button.setGeometry (VC1,      H - TAB - 108, 60, 90)
        # self.camera_button2.setGeometry(VC1 + 70, H - TAB - 108, 60, 90)

        # ════════════════════════════════════════════════════════
        # Widget set'lerini oluştur (set yapısı — hızlı lookup)
        # ════════════════════════════════════════════════════════

        # Sayfa 1 buffer ve label container'ları
        p1_buf = _collect('bufferMLXPOS','bufferMLYPOS','bufferMLZPOS',
                           'bufferMRXPOS','bufferMRYPOS','bufferMRZPOS',
                           'bufferSZPOS','bufferSTPOS','bufferSXPOS','bufferSYPOS')
        p1_lbl = set(filter(None, [getattr(self, a, None) for a in [
            'verticalLayoutWidget_11','verticalLayoutWidget_2','verticalLayoutWidget_7',
            'verticalLayoutWidget_5', 'verticalLayoutWidget_6','verticalLayoutWidget_15',
            'verticalLayoutWidget_16','verticalLayoutWidget_17',
            'verticalLayoutWidget_20','verticalLayoutWidget_19',
        ]]))
        p1_sliders = set(filter(None, [getattr(self, a, None) for a in [
            'verticalLayoutWidget_3','verticalLayoutWidget_4',
            'verticalLayoutWidget_Light','verticalLayoutWidget_Light2',
        ]]))

        self._page1_set = set([
            self.MicroL_button,  self.MicroS_button,  self.MicroLZed, self.MicroRZed,
            self.Zed_button,     self.Theta_button,   self.sample_button,
            self.distance_button, self.possition_button,
            self.verticalLayoutWidget, self.verticalLayoutWidget_8,
            # self.camera_button,  self.camera_button2,
        ]) | p1_buf | p1_lbl | p1_sliders
        if hasattr(self, 'logoLabelup'):
            self._page1_set.add(self.logoLabelup)

        # Sayfa 2 indicator container'ları
        vac_c = _collect('image_labelMASKVAC','image_labelMSKHVAC','image_labelSAMPVAC',
                          'image_labelSMPHVAC','image_labelWECSEL','image_labelCONTVAC',
                          'image_labelSAMPFSEL','image_labelOPTIVAC','image_labelRINGSEL')
        hmc_c = _collect('image_labelHOMESX', 'image_labelHOMESY',  'image_labelHOMESZ',
                          'image_labelHOMESTH','image_labelHOMEMRX','image_labelHOMEMRY',
                          'image_labelHOMEMLX','image_labelHOMEMLY','image_labelHOMEMRZ',
                          'image_labelHOMEMLZ','image_labelHOMESXY','image_labelHOMEMRXY',
                          'image_labelHOMEMLXY','image_labelHOMESTH2')
        kcg_c = _collect('image_labelKEEPHSTAT','image_labelCONTPSTAT','image_labelGAPPOSSTAT')
        ep_c  = set(filter(None, [getattr(self, a, None) for a in [
            'verticalLayoutWidget_Energy','verticalLayoutWidget_Power']]))

        self._page2_set = set(filter(None, [
            self.button_valfler,  self.button_valfler1, self.button_valfler2,
            self.button_valfler3, self.button_valfler4, self.button_valfler5,
            self.button_valfler6, self.button_valfler7, self.button_valfler8,
            
            self.button_HomeAxis,   self.button_HomeAxis1,  self.button_HomeAxis2,
            self.button_HomeAxis3,  self.button_HomeAxis4,  self.button_HomeAxis5,
            self.button_HomeAxis6,  self.button_HomeAxis7,  self.button_HomeAxis8,
            self.button_HomeAxis9,  self.button_HomeAxis10, self.button_HomeAxis11,
            self.button_HomeAxis12, self.button_HomeAxis13,
            self.button_Exposure,   self.button_light,
            getattr(self, 'label_ExpEnergy', None), getattr(self, 'label_ExpPower', None),
            self.button_KeepHolder, self.button_ContactPos, self.button_Gap,
            self.button_testmode_back, self.button_joymode, self.back_button,
            self.verticalLayoutWidget_exp,
            self.verticalLayoutWidget_ExpEnergy, self.verticalLayoutWidget_ExpPower,
            self.verticalLayoutWidget_18,
            # self.camera_button, self.camera_button2,
            self.comboBox, self.port_button,
        ])) | vac_c | hmc_c | kcg_c | ep_c

        # Yön tuşları — sayfa 1'de motor seçimine göre toggle
        self._dir_btn_set = set([
            self.zed_up_button,      self.zed_down_button,
            self.sample_up_button,   self.sample_down_button,
            self.sample_left_button, self.sample_right_button,
            self.MicroL_up_button,   self.MicroL_down_button,
            self.MicroL_left_button, self.MicroL_right_button,
            self.MicroS_up_button,   self.MicroS_down_button,
            self.MicroS_left_button, self.MicroS_right_button,
            self.MicroLZed_up_button, self.MicroLZed_down_button,
            self.MicroRZed_up_button, self.MicroRZed_down_button,
            self.Theta_left_button,   self.Theta_right_button,
            self.limit_button,
        ])

        # Her zaman görünür set
        self._always_set = {self._bg_label, self.cam_panel, self.btn_page1, self.btn_page2}
        if hasattr(self, 'logoLabel'):
            self._always_set.add(self.logoLabel)

        # Sayfa 1'i göster
        self.show_page(1)

    def _apply_initial_button_styles(self):
        """
        Tüm checkable butonlara iki durumlu toggle stili uygular.
        OFF (baslangic): koyu/siyah  |  ON (:checked): mavi gradient
        """
        TOGGLE = """
QPushButton {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #383838;
    border: 1px solid #444444;
}
QPushButton:pressed {
    background-color: #1A1A1A;
}
QPushButton:checked {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #0078D4, stop:1 #005A9E);
    color: #FFFFFF;
    border: 2px solid #00f2ff;
    border-radius: 8px;
}
QPushButton:disabled {
    background-color: #121212;
    color: #444444;
    border: 1px solid #222222;
}
"""
        _TAB_STYLE = """
QPushButton {
    background-color: #1a1a2e;
    color: #888;
    border: 2px solid transparent;
    border-radius: 4px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2a2a3e;
    color: #ccc;
}
QPushButton:checked {
    background-color: #357ab8;
    color: #fff;
    border: 2px solid #5599ff;
}
"""
        self.btn_page1 = QPushButton("Motors & Settings", self.centralwidget)
        self.btn_page1.setGeometry(0, self._layout_sh - self._layout_tab_h, self._layout_left_w // 2, self._layout_tab_h)
        self.btn_page1.setCheckable(True)
        self.btn_page1.setChecked(True)
        self.btn_page1.setStyleSheet(_TAB_STYLE)
        self.btn_page1.clicked.connect(lambda: self.show_page(1))

        self.btn_page2 = QPushButton("Valves & Controls", self.centralwidget)
        self.btn_page2.setGeometry(self._layout_left_w // 2, self._layout_sh - self._layout_tab_h, self._layout_left_w // 2, self._layout_tab_h)
        self.btn_page2.setCheckable(True)
        self.btn_page2.setStyleSheet(_TAB_STYLE)
        self.btn_page2.clicked.connect(lambda: self.show_page(2))

        # Bottom border for tab area
        _hdiv_bot = QFrame(self.centralwidget)
        _hdiv_bot.setFrameShape(QFrame.HLine)
        _hdiv_bot.setGeometry(0, self._layout_sh - self._layout_tab_h, self._layout_left_w, 2)
        _hdiv_bot.setStyleSheet("color: #333;")

        # Tüm widget'ları yeniden konumlandır ve sayfa 1'i göster
        self._reposition_and_show()

        toggle_buttons = [
            self.Zed_button, self.sample_button, self.Theta_button,
            self.MicroL_button, self.MicroS_button,
            self.MicroLZed, self.MicroRZed,
            self.distance_button, self.possition_button,
            self.button_testmode_back, self.button_joymode,
            self.button_KeepHolder, self.button_ContactPos, self.button_Gap,
        ]

        for attr in ['button_valfler', 'button_valfler1', 'button_valfler2',
                     'button_valfler3', 'button_valfler4', 'button_valfler5',
                     'button_valfler6', 'button_valfler7', 'button_valfler8',
                     'button_valfler9']:
            btn = getattr(self, attr, None)
            if btn:
                toggle_buttons.append(btn)

        for i in range(14):
            attr = f'button_HomeAxis{i}' if i > 0 else 'button_HomeAxis'
            btn = getattr(self, attr, None)
            if btn:
                toggle_buttons.append(btn)

        for attr in ['button_light', 'button_Exposure', 'button_ExpEnergy', 'button_ExpPower']:
            btn = getattr(self, attr, None)
            if btn:
                toggle_buttons.append(btn)

        for btn in toggle_buttons:
            btn.setStyleSheet(TOGGLE)

        motor_sel_btns = [
            self.Zed_button, self.sample_button, self.Theta_button,
            self.MicroL_button, self.MicroS_button,
            self.MicroLZed, self.MicroRZed
        ]
        for btn in motor_sel_btns:
            btn.toggled.connect(self._motor_selection_handler)

    def _motor_selection_handler(self, checked=False):
        motor_btns = [
            self.Zed_button, self.sample_button, self.Theta_button,
            self.MicroL_button, self.MicroS_button,
            self.MicroLZed, self.MicroRZed
        ]
        any_motor_selected = any(b.isChecked() for b in motor_btns)
        
        if any_motor_selected:
            if not self.distance_button.isChecked() and not self.possition_button.isChecked():
                self.distance_button.setEnabled(False)
                self.possition_button.setEnabled(False)
        else:
            self.distance_button.setEnabled(True)
            self.possition_button.setEnabled(True)

    def show_page(self, page_num):
        """Sol paneli temiz geçişle değiştirir. Kamera paneli etkilenmez."""
        always = getattr(self, '_always_set', set())

        # Adım 1: Sol panel widget'larının tamamını gizle
        for child in self.centralwidget.children():
            if isinstance(child, QtWidgets.QWidget) and child not in always:
                child.setVisible(False)

        # Adım 2: Sabit widget'ları göster
        for w in always:
            w.setVisible(True)

        # Adım 3: Sayfanın widget'larını göster
        if page_num == 1:
            self.btn_page1.setChecked(True)
            self.btn_page2.setChecked(False)
            for w in getattr(self, '_page1_set', set()):
                w.setVisible(True)
            # Yön tuşları motor seçimine bağlı — başta gizli
        else:
            self.btn_page1.setChecked(False)
            self.btn_page2.setChecked(True)
            for w in getattr(self, '_page2_set', set()):
                w.setVisible(True)

        self._current_page = page_num



    def start_camera(self):
        try:
            from camera import Camera
            self.camera = Camera()
            self.camera.start()
            self.camera.frame_update.connect(self.update_frame)
        except Exception as e:
            print(f"Camera1 initialization error: {e}")

    def start_camera2(self):
        try:
            from camera2 import Camera2
            self.camera2 = Camera2()
            self.camera2.start()
            self.camera2.frame_update.connect(self.update_frame2)
        except Exception as e:
            print(f"Camera2 initialization error: {e}")

    def stop_camera(self):
        if hasattr(self, 'camera'):
            self.camera.stop()

    def stop_camera2(self):
        if hasattr(self, 'camera2'):
            self.camera2.stop()

    def update_frame(self, Camera1):
        from PyQt5.QtGui import QPixmap
        q_image = QPixmap.fromImage(Camera1)
        self.cam1_display.setPixmap(q_image)

    def update_frame2(self, Camera2):
        from PyQt5.QtGui import QPixmap
        q_image2 = QPixmap.fromImage(Camera2)
        self.cam2_display.setPixmap(q_image2)

    def retranslateUi(self, MotorWindow):
            _translate = QtCore.QCoreApplication.translate
            MotorWindow.setWindowTitle(_translate("MotorWindow", "Motor Control Screen"))
            
            self.button_HomeAxis.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMESX", None))
            self.button_HomeAxis1.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMESY", None))
            self.button_HomeAxis2.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMESZ", None))
            self.button_HomeAxis3.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMESTH", None))
            self.button_HomeAxis4.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMEMRX", None))
            self.button_HomeAxis5.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMEMRY", None))
            self.button_HomeAxis6.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMEMLX", None))
            self.button_HomeAxis7.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMEMLY", None))
            self.button_HomeAxis8.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMEMRZ", None))
            self.button_HomeAxis9.setText(QtCore.QCoreApplication.translate("MotorWindow", u"HOMEMLZ", None))
            self.label_ExpEnergy.setText(_translate("","ExpEnergy"))
            self.label_ExpPower.setText(_translate("","ExpPower"))
            self.label_3.setText(_translate("", "MLXPOS   :"))
            self.label_2.setText(_translate("", "MLYPOS   :"))
            self.label_4.setText(_translate("", "MRXPOS  :"))
            self.label_5.setText(_translate("", "MRYPOS  :"))
            self.label_6.setText(_translate("", "MLZPOS  :"))
            self.label_7.setText(_translate("", "MRZPOS  :"))
            self.label_8.setText(_translate("", "Sample Zed Position  :"))
            self.label_8.setFont(QtGui.QFont("Arial", 8))
            self.label_9.setText(_translate("", "Sample Theta Position  :"))
            self.label_9.setFont(QtGui.QFont("Arial", 8))
            self.label_10.setText(_translate("", "Sample X Position:"))
            self.label_10.setFont(QtGui.QFont("Arial", 8))
            self.label_11.setText(_translate("", "Sample Y Position:"))
            self.label_11.setFont(QtGui.QFont("Arial", 8))
            self.image_labelMASKVAC.setText(_translate("", "MASKVAC"))
            self.image_labelMSKHVAC.setText(_translate("", "HARDCONT..."))
            self.image_labelSAMPVAC.setText(_translate("", "SAMPVAC"))
            self.image_labelSMPHVAC.setText(_translate("", "SAMPHVAC"))
            self.image_labelWECSEL.setText(_translate("", "WECLOCK"))
            self.image_labelCONTVAC.setText(_translate("", "CONTVAC"))
            self.image_labelSAMPFSEL.setText(_translate("", "SAMPFVAC  :"))#SAMPFVSEL
            self.image_labelOPTIVAC.setText(_translate("", "OPTICSEL  :"))
            self.image_labelRINGSEL.setText(_translate("", "RINGSEL  :"))
            self.image_labelHOMESX.setText(_translate("", "HOMESX  :"))
            self.image_labelHOMESY.setText(_translate("", "HOMESY  :"))
            self.image_labelHOMESZ.setText(_translate("", "HOMESZ  :"))
            self.image_labelHOMESTH.setText(_translate("", "HOMESTH  :"))
            self.image_labelHOMEMRX.setText(_translate("", "HOMEMRX  :"))
            self.image_labelHOMEMRY.setText(_translate("", "HOMEMRY  :"))
            self.image_labelHOMEMLX.setText(_translate("", "HOMEMLX  :"))
            self.image_labelHOMEMLY.setText(_translate("", "HOMEMLY  :"))
            self.image_labelHOMEMRZ.setText(_translate("", "HOMEMRZ  :"))
            self.image_labelHOMEMLZ.setText(_translate("", "HOMEMLZ  :"))
            self.image_labelHOMESTH2.setText(_translate("", "HOMESTH  :"))
            self.image_labelHOMEMLXY.setText(_translate("", "HOMEMLXY  :"))
            self.image_labelHOMEMRXY.setText(_translate("", "HOMEMRXY  :"))
            self.image_labelHOMESXY.setText(_translate("", "HOMESXY  :"))
            self.image_labelKEEPHSTAT.setText(_translate("", "KEEPSTAT  :"))
            self.image_labelCONTPSTAT.setText(_translate("", "CONTPSTAT  :"))
            self.image_labelGAPPOSSTAT.setText(_translate("", "GAPPOS  :"))




            

    

           
            #self.label_7.setText(_translate("","label" ))

            #self.label_1.setText(_translate("", "Data Value      :"))

    def resizeEvent(self, event):
        """Pencere yeniden boyutlandırılınca arka planı tam sığdır."""
        super().resizeEvent(event)
        if hasattr(self, '_bg_label') and hasattr(self, '_bg_path'):
            self._bg_label.setGeometry(self.centralwidget.rect())
            _pix = QtGui.QPixmap(self._bg_path)
            if not _pix.isNull():
                self._bg_label.setPixmap(
                    _pix.scaled(self.centralwidget.size(),
                                Qt.KeepAspectRatioByExpanding,
                                Qt.SmoothTransformation)
                )

    def closeEvent(self, event):
        self.portDisconnect()
        event.accept()
    
    
        
    def closeEvent(self, event):
        self.serialPort.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Ui_MotorControl()
    window.showMaximized()
    window.show()
    sys.exit(app.exec_())