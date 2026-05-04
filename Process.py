"""
LIMA Process Screen (Refactored)
=================================
Tüm komut gönderim ve veri alım işlemleri modüler yapıda.
Seri iletişim: CommandManager → SerialManager → Binary Protocol
ASCII spagetti kod yapısından Binary modüler sisteme geçiş yapıldı.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QTextEdit, QPushButton, QLineEdit, QMessageBox, QGridLayout, QLabel,
    QLCDNumber, QProgressBar, QSlider, QFrame, QSizePolicy, QComboBox)
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import (QIODevice, pyqtSignal, QObject, Qt, QThread,
    QCoreApplication, QMetaObject, QPoint, QSize, QUrl, QRect, QTimer)
from PyQt5.QtGui import QImage, QPixmap, QPalette, QImageWriter
import sys, time, os
import cv2
import numpy as np
from datetime import datetime

from protocol import LimaCommand
from serial_manager import serial_mgr
from command_manager import cmd_mgr
from portopen import portConnect
from StateManager import manager
from camera import Camera
from camera2 import Camera2
from nav_bar import NavBar
from styles.theme import ThemeManager







# ── Worker Thread (Binary Protocol) ──
class MyWorkerThread(QThread):
    finished = pyqtSignal()

    def run(self):
        time.sleep(5)
        cmd_mgr.align_check_back(3)
        self.finished.emit()

    def msg_box_port(self):
        pass

    def msg_box_port2(self):
        pass


class Ui_ProcessScreen(object):

        def __init__(self):
                super().__init__()

                self.comboBox = QComboBox()
                self.serialPort = manager.serialPort

                self.camera = Camera()
                self.camera2 = Camera2()
                self.start_camera()
                self.start_camera2()

                self.serialPort.clear()
                self.rx_buffer = bytearray()  # Binary veri havuzu

                self.is_forward = False
                self.MASKVAC1 = 0
                self.SAMPFVAC1 = 0
                self.currentValue = 1

                # UI pozisyon buffer'ları (QTextEdit)
                self.bufferMLZ = QtWidgets.QTextEdit()
                self.bufferMLeft = QtWidgets.QTextEdit()
                self.bufferMLeftY = QtWidgets.QTextEdit()
                self.bufferSampleXY = QtWidgets.QTextEdit()
                self.bufferSampleY = QtWidgets.QTextEdit()
                self.bufferTheta = QtWidgets.QTextEdit()
                self.bufferMRight = QtWidgets.QTextEdit()
                self.bufferMRightY = QtWidgets.QTextEdit()
                self.bufferMRZ = QtWidgets.QTextEdit()
                self.bufferMLXPOS = QtWidgets.QTextEdit()
                self.bufferMLYPOS = QtWidgets.QTextEdit()
                self.bufferMRZPOS = QtWidgets.QTextEdit()
                self.bufferMLZPOS = QtWidgets.QTextEdit()
                self.bufferSZPOS = QtWidgets.QTextEdit()
                self.bufferTxt = QtWidgets.QTextEdit()

                self.slider_value = 0

                self.button_style = ThemeManager.motor_button_style()
                self._active_style = ThemeManager.active_button_style()

                # Timer'lar
                self.timer_parent = QObject()
                self.timer = QTimer(self.timer_parent)
                self.timer_parent2 = QObject()
                self.timer2 = QTimer(self.timer_parent2)
                self.timer_parent3 = QObject()
                self.timer3 = QTimer(self.timer_parent2)
                self.timer_parent4 = QObject()
                self.timer4 = QTimer(self.timer_parent4)
                self.timer_parent5 = QObject()
                self.timerMicleftPoss1 = QTimer(self.timer_parent5)
                self.timer_parent6 = QObject()
                self.timerMicleftPoss2 = QTimer(self.timer_parent6)
                self.timer_parent7 = QObject()
                self.timerMicleftDis1 = QTimer(self.timer_parent7)
                self.timer_parent8 = QObject()
                self.timerMicleftDis2 = QTimer(self.timer_parent8)
                self.timer_parent9 = QObject()
                self.timerMicRightPoss1 = QTimer(self.timer_parent9)
                self.timer_parent10 = QObject()
                self.timerMicRightPoss2 = QTimer(self.timer_parent10)
                self.timer_parent11 = QObject()
                self.timerMicRightDis1 = QTimer(self.timer_parent11)
                self.timer_parent12 = QObject()
                self.timerMicRightDis2 = QTimer(self.timer_parent12)

                # Timer bağlantıları
                self.timer.timeout.connect(self.trigerboing)
                self.timer2.timeout.connect(self.TrigerProcess)
                self.timer3.timeout.connect(self.triggerstart_exposure)
                self.timer4.timeout.connect(self.ProxymityContmode)
                self.timerMicleftPoss1.timeout.connect(self.MicleftYPNext)
                self.timerMicleftPoss2.timeout.connect(self.MicleftYPNext2)
                self.timerMicleftDis1.timeout.connect(self.MicleftYPDistance1)
                self.timerMicleftDis2.timeout.connect(self.MicleftYPDistance2)
                self.timerMicRightPoss1.timeout.connect(self.MicRightYPPoss1)
                self.timerMicRightPoss2.timeout.connect(self.MicRightYPposs2)
                self.timerMicRightDis1.timeout.connect(self.MicRightYPDis1)
                self.timerMicRightDis2.timeout.connect(self.MicRightYPDis2)

                # Soft contact varsayılan
                self.timer_parentx = QObject()
                timerx = QTimer(self.timer_parentx)
                timerx.singleShot(1000, self.setButtonChecked)

                # cmd_mgr log callback
                cmd_mgr.log_callback = self._on_cmd_sent

                self.portConnectfn()

        def portConnectfn(self):
                portConnect(self)

        # ═══════════ Merkezi Yardımcı Fonksiyonlar ═══════════

        def _on_cmd_sent(self, msg):
                self._log_message("OUT", msg)

        def _send_cmd(self, cmd_name, value=1):
                """Tek satırda komut gönderir."""
                cmd_mgr.send(cmd_name, value)

        def _log_message(self, direction, msg):
                import html as html_lib
                if not hasattr(self, 'mainLogBox'):
                        return
                time_str = QtCore.QTime.currentTime().toString("HH:mm:ss.zzz")
                prefix = "&gt;&gt; OUT:" if direction == "OUT" else "&lt;&lt; IN:"
                color = "#00bbff" if direction == "OUT" else "#00ee00"
                safe_msg = html_lib.escape(str(msg))
                html_str = f'<span style="color:{color}; font-weight:bold;">[{time_str}] {prefix} {safe_msg}</span>'
                self.mainLogBox.append(html_str)
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

        def _jog_handler(self, button, axis, direction, icon_active, icon_inactive):
                """Jog buton handler: basılı→hareket, bırakılı→STOP."""
                if button.isChecked():
                        if direction == 'P':
                                cmd_mgr.jog_positive(axis)
                        else:
                                cmd_mgr.jog_negative(axis)
                        button.setIcon(QtGui.QIcon(manager.get_image_path(icon_active)))
                else:
                        cmd_mgr.stop()
                        button.setIcon(QtGui.QIcon(manager.get_image_path(icon_inactive)))



                
                        


        


        def showbox (self):
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Critical)
                        msg_box.setWindowTitle("Warning")
                        msg_box.setText("Camera Not Opened! Please Check")
                        msg_box.setInformativeText("")
                        msg_box.setDetailedText("One or more of the cameras is not active. please check and retry")
                        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel | QMessageBox.Retry)

                        result = msg_box.exec_()

                        if result == QMessageBox.Ok:
                                pass
                        elif result == QMessageBox.Cancel:
                                QApplication.quit()
                        elif result == QMessageBox.Retry:
                                self.thread.start()

        def sender(self):
                return

        def update_progress_bar(self,value):
                sender = self.sender()
                if isinstance(sender, QSlider):
                        if sender.isSliderDown():               
                                self.slider_value = value
                        else:
                                if sender == self.slider_3:
                                        self.progress_bar_3.setValue(self.slider_value)
                                        print("Slider 3 değeri gönderildi:", self.slider_value)
                                elif sender == self.slider_4:
                                        self.progress_bar_4.setValue(self.slider_value)
                                        print("Slider 4 değeri gönderildi:", self.slider_value)
                                elif sender == self.slider_Light:
                                        self.progress_bar_Light.setValue(self.slider_value)
                                        print("Slider Light değeri gönderildi:", self.slider_value)
                                elif sender == self.slider_ZedSpeed:
                                        self.progress_bar_ZedSpeed.setValue(self.slider_value)
                                        print("Slider Speed değeri gönderildi:", self.slider_value)

                


        def update_motor_speed4(self, value):
                revers_value = 100 - value
                self.progress_bar_4.setValue(revers_value)
                cmd_mgr.set_speed('SXY', revers_value * 0x64 // 100)

        def update_motor_speed3(self, value):
                revers_value = 100 - value
                self.progress_bar_3.setValue(revers_value)
                cmd_mgr.set_speed('MIC', revers_value * 0x64 // 100)

        def update_Light_degree(self, value):
                revers_value = 100 - value
                self.progress_bar_Light.setValue(revers_value)
                cmd_mgr.set_light(revers_value * 0x64 // 100)

        def update_Zed_Speed(self, value):
                revers_value = 100 - value
                self.progress_bar_ZedSpeed.setValue(revers_value)
                cmd_mgr.set_speed('FOCUS', revers_value * 0x64 // 100)



        def mouse_callback(self,event):
                if event.button()== 1:
                        x = event.x()
                        y= event.y()
                        print(f"x={x},y={y}")
                        self.coordinates_label.setText(f"Clicked at : (x={x}, y={y})")


        def check_condition(coordinates_array):
                # Belirli bir koşulu kontrol et (örneğin, koordinatların ortalamasının belirli bir değer aralığında olup olmadığını kontrol edebilirsiniz)
                average_x = np.mean([coord[0] for coord in coordinates_array])
                average_y = np.mean([coord[1] for coord in coordinates_array])
                # Bu örnekte koordinatların ortalamasının 50-70 aralığında olmasını kontrol ediyoruz
                return 9 <= average_x <= 10 and 9 <= average_y <= 10


        
        
        def update_threshold(self):
                threshold_value = self.threshold_slider.value()
                self.camera.setThreshold(threshold_value)

        def update_threshold2(self):
                threshold_value2 = self.threshold_slider2.value()
                self.camera.setThreshold2(threshold_value2)
        #BRIGHTNESS
        def update_brightness(self):
                new_brightness_value = self.sliders["BRIGHTNESS"].value()
                self.camera.setBrightness(new_brightness_value)
        #CONTRAST
        def update_CONTRAST(self):
                new_contrast_value = self.sliders["CONTRAST"].value()
                self.camera.setCONTRAST(new_contrast_value)
        #SHARPNESS
        def update_SHARPNESS(self):
                new_sharpness_value = self.sliders["SHARPNESS"].value()
                self.camera.setSHARPNESS(new_sharpness_value)

        
                        



   

        



# ═══════════ Contact Mode Butonları ═══════════

        def SendVacuumContact(self):
                if self.VacuumContact.isChecked():
                        cmd_mgr.set_contact_mode(2)
                        self.VacuumContact.setStyleSheet(self._active_style)
                else:
                        self.VacuumContact.setStyleSheet(self.button_style)

        def SendSoftContact(self):
                if self.SoftContact.isChecked():
                        cmd_mgr.set_contact_mode(1)
                        self.SoftContact.setStyleSheet(self._active_style)
                else:
                        self.SoftContact.setStyleSheet(self.button_style)

        def SendProxymity(self):
                if self.Proxymity.isChecked():
                        val = self._get_input_value(self.lineEditSendDataProxymity, "Proxymity")
                        cmd_mgr.set_proximity_contact(val)
                        self.Proxymity.setStyleSheet(self._active_style)
                        self.timer4.start(1000)
                        self.timer4.setSingleShot(True)
                else:
                        self.Proxymity.setStyleSheet(self.button_style)

        def ProxymityContmode(self):
                cmd_mgr.set_contact_mode(3)
                self.Proxymity.setStyleSheet(self._active_style)

        def SendHardContact(self):
                if self.HardContact.isChecked():
                        cmd_mgr.set_contact_mode(1)
                        self.HardContact.setStyleSheet(self._active_style)
                else:
                        self.HardContact.setStyleSheet(self.button_style)

# ═══════════ Speed Butonları (Eski — yorum dışı) ═══════════

        def SendMicroSpeed(self):
                if hasattr(self, 'MicroSpeed'):
                        cmd_mgr.set_speed('MICRO', 1 if self.MicroSpeed.isChecked() else 0)

        def SendSampleSpeed(self):
                if hasattr(self, 'SampleSpeed'):
                        cmd_mgr.set_speed('SAMPLE', 1 if self.SampleSpeed.isChecked() else 0)


# ═══════════ Motor Toggle Butonları ═══════════

        def MLZ_button_clicked(self):
                visible = not self.MicLeftZedUP.isVisible()
                self.MicLeftZedUP.setVisible(visible)
                self.MicLeftZedDOWN.setVisible(visible)
                self.MicLeftZed.setStyleSheet(self._active_style if visible else self.button_style)

        def MRZ_button_clicked(self):
                visible = not self.MicRightZedUP.isVisible()
                self.MicRightZedUP.setVisible(visible)
                self.MicRightZedDOWN.setVisible(visible)
                self.MicRightZed.setStyleSheet(self._active_style if visible else self.button_style)

        def MicroL_button_clicked(self):
                visible = not self.MicLeftUP.isVisible()
                for btn in [self.MicLeftUP, self.MicLeftDOWN, self.MicLeftLEFT, self.MicLeftRIGHT]:
                        btn.setVisible(visible)
                self.MicLeft.setStyleSheet(self._active_style if visible else self.button_style)

        def MicroS_button_clicked(self):
                visible = not self.MicRightUP.isVisible()
                for btn in [self.MicRightUP, self.MicRightDOWN, self.MicRightLEFT, self.MicRightRIGHT]:
                        btn.setVisible(visible)
                self.MicRight.setStyleSheet(self._active_style if visible else self.button_style)

        def sample_button_clicked(self):
                visible = not self.SampleUP.isVisible()
                for btn in [self.SampleUP, self.SampleDOWN, self.SampleLEFT, self.SampleRIGHT]:
                        btn.setVisible(visible)
                self.SampleXY.setStyleSheet(self._active_style if visible else self.button_style)

        def Theta_button_clicked(self):
                visible = not self.ThetaRIGHT.isVisible()
                self.ThetaRIGHT.setVisible(visible)
                self.ThetaLEFT.setVisible(visible)
                self.Theta.setStyleSheet(self._active_style if visible else self.button_style)

# ═══════════ Micro Left Zed ═══════════

        def MicLeftZedYP(self):
                if self.possition_button.isChecked():
                        val = self._get_input_value(self.lineEditSendData)
                        cmd_mgr.move_to_position('MLZ', val)
                elif self.distance_button.isChecked():
                        val = self._get_input_value(self.lineEditSendData, "Distance")
                        cmd_mgr.go_distance('MLZ', val)
                else:
                        self._jog_handler(self.MicLeftZedUP, 'MLZ', 'P', "redup", "uparrow2")

        def MicLeftZedYN(self):
                self._jog_handler(self.MicLeftZedDOWN, 'MLZ', 'N', "reddown", "downarrow2")

# ═══════════ Micro Right Zed ═══════════

        def MicRightZedYP(self):
                if self.possition_button.isChecked():
                        val = self._get_input_value(self.lineEditSendData_2)
                        cmd_mgr.move_to_position('MRZ', val)
                elif self.distance_button.isChecked():
                        val = self._get_input_value(self.lineEditSendData_2, "Distance")
                        cmd_mgr.go_distance('MRZ', val)
                else:
                        self._jog_handler(self.MicRightZedUP, 'MRZ', 'P', "redup", "uparrow2")

        def MicRightZedYN(self):
                self._jog_handler(self.MicRightZedDOWN, 'MRZ', 'N', "reddown", "downarrow2")

# ═══════════ Micro Left XY ═══════════

        def MicLeftYP(self):
                if self.MicLeftUP.isChecked() and self.possition_button.isChecked():
                        cmd_mgr.set_mpos('MLY', self._get_input_value(self.lineEditSendData_2))
                        self.timerMicleftPoss1.start(1000)
                        self.timerMicleftPoss1.setSingleShot(True)
                elif self.MicLeftUP.isChecked() and self.distance_button.isChecked():
                        cmd_mgr.set_gpos('MLY', self._get_input_value(self.lineEditSendData_2, "Distance"))
                        self.timerMicleftDis1.start(1000)
                        self.timerMicleftDis1.setSingleShot(True)
                elif self.MicLeftUP.isChecked():
                        self._jog_handler(self.MicLeftUP, 'MLY', 'P', "redup", "uparrow2")
                else:
                        cmd_mgr.stop()
                        self.MicLeftUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))

        def MicleftYPNext(self):
                cmd_mgr.set_mpos('MLX', self._get_input_value(self.lineEditSendData))
                self.timerMicleftPoss2.start(1000)
                self.timerMicleftPoss2.setSingleShot(True)

        def MicleftYPNext2(self):
                cmd_mgr.move_to_position('ML', self._get_input_value(self.lineEditSendData))

        def MicleftYPDistance1(self):
                cmd_mgr.set_gpos('MLX', self._get_input_value(self.lineEditSendData, "Distance"))
                self.timerMicleftDis2.start(1000)
                self.timerMicleftDis2.setSingleShot(True)

        def MicleftYPDistance2(self):
                cmd_mgr.go_distance('ML', self._get_input_value(self.lineEditSendData))

        def MicLeftYN(self):
                self._jog_handler(self.MicLeftDOWN, 'MLY', 'N', "reddown", "downarrow2")

        def MicLeftXP(self):
                self._jog_handler(self.MicLeftRIGHT, 'MLX', 'P', "redright", "rightarrow2")

        def MicLeftXN(self):
                self._jog_handler(self.MicLeftLEFT, 'MLX', 'N', "redleft", "leftarrow2")

        def MicLeftPossX(self):
                cmd_mgr.set_mpos('MLX', self._get_input_value(self.lineEditSendData))

        def MicLeftPossY(self):
                cmd_mgr.set_mpos('MLY', self._get_input_value(self.lineEditSendData_2))

        def MicLeftDissX(self):
                cmd_mgr.set_gpos('MLX', self._get_input_value(self.lineEditSendData, "Distance"))

        def MicLeftDissY(self):
                cmd_mgr.set_gpos('MLY', self._get_input_value(self.lineEditSendData_2, "Distance"))

# ═══════════ Micro Right XY ═══════════

        def MicRightYP(self):
                if self.MicRightUP.isChecked() and self.possition_button.isChecked():
                        cmd_mgr.set_mpos('MRY', self._get_input_value(self.lineEditSendData_2))
                        self.timerMicRightPoss1.start(1000)
                        self.timerMicRightPoss1.setSingleShot(True)
                elif self.MicRightUP.isChecked() and self.distance_button.isChecked():
                        cmd_mgr.set_gpos('MRY', self._get_input_value(self.lineEditSendData_2, "Distance"))
                        self.timerMicRightDis1.start(1000)
                        self.timerMicRightDis1.setSingleShot(True)
                elif self.MicRightUP.isChecked():
                        self._jog_handler(self.MicRightUP, 'MRY', 'P', "redup", "uparrow2")
                else:
                        cmd_mgr.stop()
                        self.MicRightUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))

        def MicRightYPPoss1(self):
                cmd_mgr.set_mpos('MRX', self._get_input_value(self.lineEditSendData))
                self.timerMicRightPoss2.start(1000)
                self.timerMicRightPoss2.setSingleShot(True)

        def MicRightYPposs2(self):
                cmd_mgr.move_to_position('MR', self._get_input_value(self.lineEditSendData))

        def MicRightYPDis1(self):
                cmd_mgr.set_gpos('MRX', self._get_input_value(self.lineEditSendData, "Distance"))
                self.timerMicRightDis2.start(1000)
                self.timerMicRightDis2.setSingleShot(True)

        def MicRightYPDis2(self):
                cmd_mgr.go_distance('MR', self._get_input_value(self.lineEditSendData))

        def MicRightYN(self):
                self._jog_handler(self.MicRightDOWN, 'MRY', 'N', "reddown", "downarrow2")

        def MicRightXP(self):
                self._jog_handler(self.MicRightRIGHT, 'MRX', 'P', "redright", "rightarrow2")

        def MicroSXN(self):
                self._jog_handler(self.MicRightLEFT, 'MRX', 'N', "redleft", "leftarrow2")

        def MicRightPossX(self):
                cmd_mgr.set_mpos('MRX', self._get_input_value(self.lineEditSendData))

        def MicRightPossY(self):
                cmd_mgr.set_mpos('MRY', self._get_input_value(self.lineEditSendData_2))

        def MicRightDissX(self):
                cmd_mgr.set_gpos('MRX', self._get_input_value(self.lineEditSendData, "Distance"))

        def MicRightDissY(self):
                cmd_mgr.set_gpos('MRY', self._get_input_value(self.lineEditSendData_2, "Distance"))

# ═══════════ Sample XY ═══════════

        def SampleYP(self):
                if self.SampleUP.isChecked() and self.possition_buttonSample.isChecked():
                        cmd_mgr.set_mpos('SY', self._get_input_value(self.lineEditSendData_2tab6))
                        cmd_mgr.set_mpos('SX', self._get_input_value(self.lineEditSendDatatab6))
                        cmd_mgr.move_to_position('SXY', self._get_input_value(self.lineEditSendDatatab6))
                elif self.SampleUP.isChecked() and self.distance_buttonSample.isChecked():
                        cmd_mgr.set_gpos('SY', self._get_input_value(self.lineEditSendData_2tab6, "Distance"))
                        cmd_mgr.set_gpos('SX', self._get_input_value(self.lineEditSendDatatab6, "Distance"))
                        cmd_mgr.send('GOSXY', self._get_input_value(self.lineEditSendDatatab6))
                elif self.SampleUP.isChecked():
                        self._jog_handler(self.SampleUP, 'SY', 'P', "redup", "uparrow2")
                else:
                        cmd_mgr.stop()
                        self.SampleUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))

        def SampleYN(self):
                self._jog_handler(self.SampleDOWN, 'SY', 'N', "reddown", "downarrow2")

        def SampleXP(self):
                self._jog_handler(self.SampleRIGHT, 'SX', 'P', "redright", "rightarrow2")

        def SampleXN(self):
                self._jog_handler(self.SampleLEFT, 'SX', 'N', "redleft", "leftarrow2")

        def SamplePossXdata(self):
                cmd_mgr.set_mpos('SX', self._get_input_value(self.lineEditSendDatatab6))

        def SamplePossYdata(self):
                cmd_mgr.set_mpos('SY', self._get_input_value(self.lineEditSendData_2tab6))

        def SampleDissXdata(self):
                cmd_mgr.set_gpos('SX', self._get_input_value(self.lineEditSendDatatab6, "Distance"))

        def SampleDissYdata(self):
                cmd_mgr.set_gpos('SY', self._get_input_value(self.lineEditSendData_2tab6, "Distance"))

# ═══════════ Theta ═══════════

        def ThetaXP(self):
                if self.Theta.isChecked() and self.possition_buttonSample.isChecked():
                        cmd_mgr.move_to_position('STH', self._get_input_value(self.lineEditSendDatatab6))
                elif self.Theta.isChecked() and self.distance_buttonSample.isChecked():
                        cmd_mgr.go_distance('STH', self._get_input_value(self.lineEditSendDatatab6, "Distance"))
                else:
                        self._jog_handler(self.ThetaRIGHT, 'STH', 'P', "redright", "rightarrow2")

        def ThetaXN(self):
                if self.Theta.isChecked() and self.possition_buttonSample.isChecked():
                        cmd_mgr.move_to_position('STH', self._get_input_value(self.lineEditSendDatatab6))
                elif self.Theta.isChecked() and self.distance_buttonSample.isChecked():
                        cmd_mgr.go_distance('STH', self._get_input_value(self.lineEditSendDatatab6, "Distance"))
                else:
                        self._jog_handler(self.ThetaLEFT, 'STH', 'N', "redleft", "leftarrow2")

        def ThetaPossMove(self):
                cmd_mgr.move_to_position('STH', self._get_input_value(self.lineEditSendDatatab6))

        def ThetaDissGo(self):
                cmd_mgr.go_distance('STH', self._get_input_value(self.lineEditSendDatatab6, "Distance"))

# ═══════════ Zed (Sample Z) ═══════════

        def SendDataZedYP(self):
                if self.UpButton.isChecked():
                        cmd_mgr.jog_positive('SZ')
                        self.UpButton.setIcon(QtGui.QIcon(manager.get_image_path("redup")))
                else:
                        cmd_mgr.stop()
                        self.UpButton.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2")))

        def SendDataZedYN(self):
                if self.DownButton.isChecked():
                        cmd_mgr.jog_negative('SZ')
                        self.DownButton.setIcon(QtGui.QIcon(manager.get_image_path("reddown")))
                else:
                        cmd_mgr.stop()
                        self.DownButton.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2")))

# ═══════════ Gap & Exposure ═══════════

        def GapDataSend(self):
                if self.GapButton.isChecked():
                        val = self._get_input_value(self.lineEditSendDataGap, "Gap")
                        cmd_mgr.set_gap(val)

        def ExpoSendData(self):
                if self.ExposureButton.isChecked():
                        val = self._get_input_value(self.lineEditSendDataExposure, "Exposure")
                        cmd_mgr.set_exposure_dose(val)
                        self.ExposureButton.setStyleSheet(self._active_style)
                else:
                        self.ExposureButton.setStyleSheet(self.button_style)

        def triggerstart_exposure(self):
                cmd_mgr.set_exposure(1)

# ═══════════ Mask & Valve ═══════════

        def SendMaskLoad(self):
                if self.MaskLoad.isChecked():
                        cmd_mgr.send('MASKVSEL', 1)
                        self.MaskLoad.setStyleSheet(self._active_style)
                else:
                        cmd_mgr.send('MASKVSEL', 0)
                        self.MaskLoad.setStyleSheet(self.button_style)

        def SendMaskHolderLock(self):
                pass  # Devre dışı bırakılmış fonksiyon

        def SendMaskVacuum(self):
                if self.MaskVacuum.isChecked():
                        cmd_mgr.valve_select('MASK', 1)
                        self.MaskVacuum.setStyleSheet(self._active_style)
                else:
                        cmd_mgr.valve_select('MASK', 0)
                        self.MaskVacuum.setStyleSheet(self.button_style)

        def SendSampleVacuum(self):
                if self.SampleVacuum.isChecked():
                        cmd_mgr.valve_select('SAMP', 1)
                        self.SampleVacuum.setStyleSheet(self._active_style)
                else:
                        cmd_mgr.valve_select('SAMP', 0)
                        self.SampleVacuum.setStyleSheet(self.button_style)

# ═══════════ Alignment ═══════════

        def SendAlignCheck(self):
                if self.AlignCheck.isChecked():
                        cmd_mgr.align_check(1)
                        self.AlignCheck.setStyleSheet(self._active_style)
                        self.AlignCheck.setText("AlignCheck Cancel")
                        self.timer.start(5000)
                        self.timer.setSingleShot(True)
                else:
                        cmd_mgr.align_check_back(1)
                        self.AlignCheck.setStyleSheet(self.button_style)
                        self.AlignCheck.setText("AlignCheck")

        def trigerboing(self):
                cmd_mgr.send('ALIGNCHKBACK', 3)

        def SendAutoAlignment(self):
                if self.AutoAlignment.isChecked():
                        cmd_mgr.send('AUTOALIGN', 1)
                        self.AutoAlignment.setStyleSheet(self._active_style)
                else:
                        cmd_mgr.send('AUTOALIGN', 0)
                        self.AutoAlignment.setStyleSheet(self.button_style)

        def SendAutoFocus(self):
                if self.AutoFocus.isChecked():
                        cmd_mgr.send('AUTOFOCUS', 1)
                        self.AutoFocus.setStyleSheet(self._active_style)
                else:
                        cmd_mgr.send('AUTOFOCUS', 0)
                        self.AutoFocus.setStyleSheet(self.button_style)

        def SendStartExposure(self):
                if self.StartExposure.isChecked():
                        cmd_mgr.set_exposure(1)
                        self.StartExposure.setStyleSheet(self._active_style)
                        self.StartExposure.setText("Cancel Exposure")
                        self.timer3.start(5000)
                        self.timer3.setSingleShot(True)
                else:
                        cmd_mgr.set_exposure(0)
                        self.StartExposure.setStyleSheet(self.button_style)
                        self.StartExposure.setText("Start Exposure")

        def AlignBack(self):
                cmd_mgr.align_back(1)

        def AlignStop(self):
                cmd_mgr.align_stop(1)

        def AlignCheckBack(self):
                cmd_mgr.align_check_back(1)

        def AlignJoyModeBack(self):
                cmd_mgr.joy_mode_back(1)






# ═══════════ Process & System ═══════════

        def StartProcessButton(self):
                if self.StartProcess.isChecked():
                        if hasattr(self, 'button_joymode') and self.button_joymode.isChecked():
                                self.button_testmode_back.click()
                        if hasattr(self, 'button_testmode_back') and self.button_testmode_back.isChecked():
                                self.button_joymode.click()
                        cmd_mgr.align(1)
                        self.StartProcess.setText("Cancel Process")
                        self.StartProcess.setStyleSheet(self._active_style)
                        self.timer2.start(1000)
                        self.timer2.setSingleShot(True)
                else:
                        cmd_mgr.align_back(1)
                        self.StartProcess.setStyleSheet(self.button_style)
                        self.StartProcess.setText("Start Process")

        def TrigerProcess(self):
                cmd_mgr.send('ALIGNCHKBACK', 3)

        def EmergencyStoped(self):
                cmd_mgr.stop()
                cmd_mgr.align_stop(1)
                self.StartProcess.setStyleSheet(self.button_style)
                self.StartProcess.setText("Start Process")
                self.StartProcess.setChecked(False)

        def send_Testmode_back(self):
                if hasattr(self, 'button_testmode_back'):
                        if self.button_testmode_back.isChecked():
                                cmd_mgr.test_mode(1)
                                self.button_testmode_back.setStyleSheet(self._active_style)
                        else:
                                cmd_mgr.test_mode_back(1)
                                self.button_testmode_back.setStyleSheet(self.button_style)

        def send_Joymode(self):
                if hasattr(self, 'button_joymode'):
                        if self.button_joymode.isChecked():
                                cmd_mgr.joy_mode(1)
                                self.button_joymode.setStyleSheet(self._active_style)
                        else:
                                cmd_mgr.joy_mode_back(1)
                                self.button_joymode.setStyleSheet(self.button_style)

# ═══════════ Veri Alma (Binary) ═══════════

        def _process_binary_command(self, cmd, value):
                cmd_name = cmd.name if hasattr(cmd, 'name') else str(cmd)
                
                self._log_message("IN", f"{cmd_name} (Value: {value})")

                # Pozisyon güncelleme
                POS_MAP = {
                        'MLZPOS': self.bufferMLZ, 'MLXPOS': self.bufferMLeft,
                        'MLYPOS': self.bufferMLeftY, 'SXPOS': self.bufferSampleXY,
                        'SYPOS': self.bufferSampleY, 'STPOS': self.bufferTheta,
                        'MRXPOS': self.bufferMRight, 'MRYPOS': self.bufferMRightY,
                        'MRZPOS': self.bufferMRZ, 'SZPOS': self.bufferSZPOS,
                }
                if cmd_name in POS_MAP:
                        POS_MAP[cmd_name].setPlainText(str(value))
                        return

                _PROC_CMD_TRANSLATE = {
                        'MASKVSEL':  'MASKVAC',
                        'SAMPFVSEL': 'SAMPFVAC',
                        'SAMPHVSEL': 'SAMPHVAC',
                        'CONVSEL':   'CONTVAC',
                        'WECLSEL':   'WECLOCK',
                        # OPTICSEL ve RINGSEL zaten aynı isimle dönüyor, çeviriye gerek yok
                        }       

                if cmd_name == 'CONTMODE':
                        pix_green = manager.get_image_path("green")   # .png uzantısı kaldırıldı
                        pix_red   = manager.get_image_path("red")     # .png uzantısı kaldırıldı
                        self.image_SoftContact.setPixmap(QtGui.QPixmap(pix_green if value == 1 else pix_red))
                        self.image_VacuumContact.setPixmap(QtGui.QPixmap(pix_green if value == 2 else pix_red))
                        self.image_proxymity.setPixmap(QtGui.QPixmap(pix_green if value == 3 else pix_red))
                        self.image_HardContact.setPixmap(QtGui.QPixmap(pix_green if value == 1 else pix_red))
                        return

                # cmd_name'i önce çevir, sonra STATUS_MAP'te ara
                lookup_name = _PROC_CMD_TRANSLATE.get(cmd_name, cmd_name)
        
                # Status indicator (yeşil/kırmızı)
                STATUS_MAP = {
                        'MASKHSTAT': (self.image_MaskLU, self.msg_box_MASKHSTAT1),
                        'SRAILSTAT': (None, self.msg_box_SRAILSTAT1),
                        'SAMPFVAC':  (self.image_SampleVacuum, None),   # artık lookup_name ile eşleşir
                        'MASKVAC':   (self.image_MaskVacuum, None),     # artık lookup_name ile eşleşir
                        'AUTOALIGN': (self.image_AutoAllingment, None),
                        'EXPOSURE':  (self.image_StartExposure, None),
                        'ALIGNCHK':  (self.image_Aligncheck, None),
                        'ALIGNCHKBACK': (self.image_Aligncheck, None),
                        'AUTOFOCUS': (self.image_AutoFocus, None),
                }
                if lookup_name in STATUS_MAP:
                        img_label, msg_fn = STATUS_MAP[lookup_name]
                        if img_label:
                                pix = manager.get_image_path("green" if value == 1 else "red")  # .png kaldırıldı
                                img_label.setPixmap(QPixmap(pix))
                                img_label.setAlignment(Qt.AlignCenter)
                        if value == 1 and msg_fn:
                                msg_fn()
                                self.StartProcessReset()
                        if lookup_name == 'MASKVAC' and value == 1:
                                self.MASKVAC1 = 1
                        if lookup_name == 'SAMPFVAC' and value == 1:
                                self.SAMPFVAC1 = 1
                        if self.SAMPFVAC1 == 1 and self.MASKVAC1 == 1:
                                self.StartProcess.setEnabled(True)
                        return

                # Contact mode status
                CONTACT_MAP = {
                        'VacuumContact': self.image_VacuumContact,
                        'SoftContact': self.image_SoftContact,
                        'Proxymity': self.image_proxymity,
                        'HardContact': self.image_HardContact,
                }
                if cmd_name in CONTACT_MAP:
                        pix = manager.get_image_path("green.png" if value == 1 else "red.png")
                        CONTACT_MAP[cmd_name].setPixmap(QPixmap(pix))
                        CONTACT_MAP[cmd_name].setAlignment(Qt.AlignCenter)
                        return

                # Mask status
                MASK_STATUS = {
                        'MASK LOAD': self.image_MaskLU,
                        'MASK HOLDER LOAD': self.image_SampleHolderLoad,
                }
                if cmd_name in MASK_STATUS:
                        pix = manager.get_image_path("green.png" if value == 1 else "red.png")
                        MASK_STATUS[cmd_name].setPixmap(QPixmap(pix))
                        MASK_STATUS[cmd_name].setAlignment(Qt.AlignCenter)
                        return

                # Align status
                ALIGN_MAP = {
                        'ALIGN CHECK': (self.image_Aligncheck, self.AlignCheckReset if value == 1 else None),
                        'AUTO ALLİGNMENT': (self.image_AutoAllingment, None),
                        'AUTO FOCUS': (self.image_AutoFocus, None),
                        'START EXPOSURE': (self.image_StartExposure, None),
                }
                if cmd_name in ALIGN_MAP:
                        img, callback = ALIGN_MAP[cmd_name]
                        pix = manager.get_image_path("green.png" if value == 1 else "red.png")
                        img.setPixmap(QPixmap(pix))
                        img.setAlignment(Qt.AlignCenter)
                        if callback:
                                callback()
                        return

                # ALIGNSTAT
                if cmd_name == 'ALIGNSTAT':
                        if value == 0:
                                self.msg_box_ALIGNSTAT0()
                                self.StartProcessReset()
                                self.StartAligReset()
                                self.StartExposureReset()
                        elif value == 1:
                                self.msg_box_ALIGNSTAT1()
                                self.tab_Align.setEnabled(True)
                                self.tabWidget.setCurrentIndex(3)
                                self.StartProcessReset()
                                self.StartAligReset()
                                self.StartExposureReset()
                        return

                if cmd_name == 'PROCESSCOMP':
                        if value == 0:
                                self.msg_box_PROCESSCOMP0()
                                self.StartProcessReset()
                        return

                if cmd_name == 'EXPCOMP':
                        if value == 0:
                                self.msg_box_EXPCOMP0()
                        elif value == 1:
                                self.msg_box_EXPCOMP1()
                        self.StartProcessReset()
                        self.StartAligReset()
                        self.StartExposureReset()
                        return

                if cmd_name == 'SAMPHHOLD':
                        if value == 0:
                                self.msg_box_SAMPHHOLD0()
                                self.StartProcessReset()
                        return

                if cmd_name == 'WECCONTSTAT':
                        if value == 0:
                                self.msg_box_WECCONTSTAT0()
                                self.StartProcessReset()
                        return

        def append_log(self, text):
                if hasattr(self, 'textEditReciveData'):
                        self.textEditReciveData.append(text)

# ═══════════ Reset Fonksiyonları ═══════════

        def StartProcessReset(self):
                self.StartProcess.setChecked(False)
                self.StartProcess.setStyleSheet(self.button_style)
                self.StartProcess.setText("Start Process")

        def StartAligReset(self):
                self.AlignCheck.setChecked(False)
                self.AlignCheck.setStyleSheet(self.button_style)
                self.AlignCheck.setText("AlignCheck")

        def StartExposureReset(self):
                self.StartExposure.setChecked(False)
                self.StartExposure.setStyleSheet(self.button_style)
                self.StartExposure.setText("Start Exposure")

        def AlignCheckReset(self):
                self.AlignCheck.setChecked(False)
                self.AlignCheck.setStyleSheet(self.button_style)
                self.AlignCheck.setText("AlignCheck")

# ═══════════ UI Yardımcı Fonksiyonlar ═══════════

        def listSerialPorts(self):
                serialPortInfo = QSerialPortInfo()
                for serialPort in serialPortInfo.availablePorts():
                        self.comboBox.addItem(serialPort.portName())

        def button_check_Move(self):
                buttons = [self.distance_button, self.possition_button, self.distance_buttonSample, self.possition_buttonSample]
                selected_button = None
                for button in buttons:
                        if button.isChecked():
                                selected_button = button
                                break
                for button in buttons:
                        if button == selected_button:
                                button.setEnabled(True)
                        else:
                                button.setEnabled(False)
                                if not selected_button:
                                        button.setEnabled(True)

        def button_check(self):
                pass

        def button_disableway(self):
                buttons = [self.MicLeftZedUP, self.MicLeftZedDOWN, self.MicRightZedDOWN, self.MicRightZedUP,
                        self.SampleDOWN, self.SampleLEFT, self.SampleUP, self.SampleRIGHT,
                        self.ThetaRIGHT, self.ThetaLEFT, self.MicLeftDOWN, self.MicLeftLEFT, self.MicLeftRIGHT,
                        self.MicRightDOWN, self.MicRightLEFT, self.MicRightUP, self.MicRightRIGHT,
                        self.MicLeftUP, self.UpButton, self.DownButton]
                selected_button = None
                for button in buttons:
                        if button.isChecked():
                                selected_button = button
                                break
                for button in buttons:
                        if button == selected_button:
                                button.setEnabled(True)
                        else:
                                button.setEnabled(False)
                                if not selected_button:
                                        button.setEnabled(True)

        def possitionhide(self):
                if self.possition_button.isChecked() or self.possition_buttonSample.isChecked():
                        self.possition_button.setVisible(True)
                        for btn in [self.MicLeftZedDOWN, self.MicRightZedDOWN, self.SampleDOWN, self.SampleLEFT, self.SampleRIGHT,
                                self.ThetaRIGHT, self.ThetaLEFT, self.MicLeftDOWN, self.MicLeftLEFT, self.MicLeftRIGHT,
                                self.MicRightDOWN, self.MicRightLEFT, self.MicRightRIGHT, self.SampleUP,
                                self.MicLeftZedUP, self.MicRightZedUP, self.MicRightUP, self.MicLeftUP]:
                                btn.setVisible(False)
                elif self.MicLeftZed.isChecked() and not self.possition_button.isChecked():
                        self.LeftZedPossition.setVisible(False)
                        self.MicLeftZedDOWN.setVisible(True)
                        self.MicLeftZedUP.setVisible(True)
                elif self.MicRightZed.isChecked() and not self.possition_button.isChecked():
                        self.RightZedPossition.setVisible(False)
                        self.MicRightZedDOWN.setVisible(True)
                        self.MicRightZedUP.setVisible(True)
                elif self.MicLeft.isChecked() and not self.possition_button.isChecked():
                        self.MicLeftPossitionX.setVisible(False)
                        self.MicLeftPossitionY.setVisible(False)
                        self.MicLeftPossitionMOVEXY.setVisible(False)
                        self.MicLeftDOWN.setVisible(True)
                        self.MicLeftLEFT.setVisible(True)
                        self.MicLeftRIGHT.setVisible(True)
                        self.MicLeftUP.setVisible(True)
                elif self.MicRight.isChecked() and not self.possition_button.isChecked():
                        self.MicRightPossitionX.setVisible(False)
                        self.MicRightPossitionY.setVisible(False)
                        self.MicRightPossitionMOVEXY.setVisible(False)
                        self.MicRightDOWN.setVisible(True)
                        self.MicRightLEFT.setVisible(True)
                        self.MicRightRIGHT.setVisible(True)
                        self.MicRightUP.setVisible(True)
                elif self.SampleXY.isChecked() and not self.possition_buttonSample.isChecked():
                        self.SamplePossitionX.setVisible(False)
                        self.SamplePossitionY.setVisible(False)
                        self.SamplePossitionMOVEXY.setVisible(False)
                        self.SampleDOWN.setVisible(True)
                        self.SampleLEFT.setVisible(True)
                        self.SampleRIGHT.setVisible(True)
                        self.SampleUP.setVisible(True)
                elif self.Theta.isChecked() and not self.possition_buttonSample.isChecked():
                        self.ThetaPossitionY.setVisible(False)
                        self.ThetaPossitionX.setVisible(False)
                        self.ThetaRIGHT.setVisible(True)
                        self.ThetaLEFT.setVisible(True)

        def distancehide(self):
                if self.distance_button.isChecked() or self.distance_buttonSample.isChecked():
                        self.distance_button.setVisible(True)
                        for btn in [self.MicLeftZedDOWN, self.MicRightZedDOWN, self.SampleDOWN, self.SampleLEFT, self.SampleRIGHT,
                                self.ThetaRIGHT, self.ThetaLEFT, self.MicLeftDOWN, self.MicLeftLEFT, self.MicLeftRIGHT,
                                self.MicRightDOWN, self.MicRightLEFT, self.MicRightRIGHT, self.SampleUP,
                                self.MicLeftZedUP, self.MicRightZedUP, self.MicRightUP, self.MicLeftUP]:
                                btn.setVisible(False)
                elif self.MicLeftZed.isChecked() and not self.distance_button.isChecked():
                        self.LeftZedDistance.setVisible(False)
                        self.MicLeftZedDOWN.setVisible(True)
                        self.MicLeftZedUP.setVisible(True)
                elif self.MicRightZed.isChecked() and not self.distance_button.isChecked():
                        self.RightZedDistance.setVisible(False)
                        self.MicRightZedDOWN.setVisible(True)
                        self.MicRightZedUP.setVisible(True)
                elif self.MicLeft.isChecked() and not self.distance_button.isChecked():
                        self.MicLeftDistanceX.setVisible(False)
                        self.MicLeftDistanceY.setVisible(False)
                        self.MicLeftDistanceGOXY.setVisible(False)
                        self.MicLeftDOWN.setVisible(True)
                        self.MicLeftLEFT.setVisible(True)
                        self.MicLeftRIGHT.setVisible(True)
                        self.MicLeftUP.setVisible(True)
                elif self.MicRight.isChecked() and not self.distance_button.isChecked():
                        self.MicRightDistanceX.setVisible(False)
                        self.MicRightDistanceY.setVisible(False)
                        self.MicRightDistanceGOXY.setVisible(False)
                        self.MicRightDOWN.setVisible(True)
                        self.MicRightLEFT.setVisible(True)
                        self.MicRightRIGHT.setVisible(True)
                        self.MicRightUP.setVisible(True)
                elif self.SampleXY.isChecked() and not self.distance_buttonSample.isChecked():
                        self.SampleDistanceX.setVisible(False)
                        self.SampleDistanceY.setVisible(False)
                        self.SampleDistanceGOXY.setVisible(False)
                        self.SampleDOWN.setVisible(True)
                        self.SampleLEFT.setVisible(True)
                        self.SampleRIGHT.setVisible(True)
                        self.SampleUP.setVisible(True)
                elif self.Theta.isChecked() and not self.distance_buttonSample.isChecked():
                        self.ThetaDistanceX.setVisible(False)
                        self.ThetaDistanceY.setVisible(False)
                        self.ThetaDistanceGOXY.setVisible(False)
                        self.ThetaRIGHT.setVisible(True)
                        self.ThetaLEFT.setVisible(True)

        def distanceSample_command(self):
                pass

        def ButtonDisable(self):
                buttons = [self.MicLeftZed, self.MicRightZed, self.MicLeft, self.MicRight, self.SampleXY, self.Theta]
                selected_button = None
                for button in buttons:
                        if button.isChecked():
                                selected_button = button
                                break
                for button in buttons:
                        if button == selected_button:
                                button.setEnabled(True)
                        else:
                                button.setEnabled(False)
                                if not selected_button:
                                        button.setEnabled(True)

        def ContactDisable(self):
                if self.VacuumContact.isChecked():
                        for btn in [self.SoftContact, self.HardContact, self.Proxymity]:
                                if btn.isChecked():
                                        btn.click()

        def ContactDisable2(self):
                if self.HardContact.isChecked():
                        for btn in [self.SoftContact, self.VacuumContact, self.Proxymity]:
                                if btn.isChecked():
                                        btn.click()

        def ContactDisable3(self):
                if self.SoftContact.isChecked():
                        for btn in [self.HardContact, self.VacuumContact, self.Proxymity]:
                                if btn.isChecked():
                                        btn.click()

        def ContactDisable4(self):
                if self.Proxymity.isChecked():
                        for btn in [self.HardContact, self.VacuumContact, self.SoftContact]:
                                if btn.isChecked():
                                        btn.click()

        def MaskControl(self):
                pass

        def MaskControl2(self):
                pass

        def MaskControl3(self):
                pass

        def MaskControl4(self):
                pass

        def AlignControl(self):
                pass

        def AlignControl2(self):
                pass

        def AlignControl3(self):
                pass

        def AlignControl4(self):
                pass

        def msg_box_MASKHSTAT1(self):
                QMessageBox.warning(None, "MASK", "Mask Holder Stat: 1")

        def msg_box_SRAILSTAT1(self):
                QMessageBox.warning(None, "SRAIL", "Sample Rail Stat: Hata")

        def msg_box_SAMPHHOLD0(self):
                QMessageBox.warning(None, "SAMPH", "Sample Holder Yok")

        def msg_box_WECCONTSTAT0(self):
                QMessageBox.warning(None, "WEC", "WEC Contact Stat: 0")

        def msg_box_ALIGNSTAT0(self):
                QMessageBox.information(None, "ALIGN", "Alignment Başarısız")

        def msg_box_ALIGNSTAT1(self):
                QMessageBox.information(None, "ALIGN", "Alignment Başarılı")

        def msg_box_PROCESSCOMP0(self):
                QMessageBox.information(None, "PROCESS", "Process Tamamlanmadı")

        def msg_box_EXPCOMP0(self):
                QMessageBox.information(None, "EXPOSURE", "Exposure Tamamlanmadı")

        def msg_box_EXPCOMP1(self):
                QMessageBox.information(None, "EXPOSURE", "Exposure Tamamlandı")

        def msg_box_zero(self):
                QMessageBox.warning(None, "Warning", "Değer: 0")

        def msg_box_one(self):
                QMessageBox.information(None, "Info", "Değer: 1")

        def setupUi(self, ProcessScreen):
                ProcessScreen.setObjectName("ProcessScreen")
                ProcessScreen.resize(1920, 1080)
                ProcessScreen.showMaximized()
                self.centralwidget = QtWidgets.QWidget(ProcessScreen)
                ProcessScreen.setWindowIcon(QtGui.QIcon(manager.get_image_path("mainiconn.ico")))
                sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(ProcessScreen.sizePolicy().hasHeightForWidth())
                ProcessScreen.setSizePolicy(sizePolicy)
                ProcessScreen.setAutoFillBackground(False)
                bg_path = manager.get_image_path("558571.png").replace("\\", "/")
                ProcessScreen.setStyleSheet(f"background: url({bg_path})")
                ProcessScreen.setDocumentMode(False)
                ProcessScreen.setTabShape(QtWidgets.QTabWidget.Rounded)
                ProcessScreen.setDockNestingEnabled(False)
                ProcessScreen.setUnifiedTitleAndToolBarOnMac(False)
                self.centralwidget = QtWidgets.QWidget(ProcessScreen)
                self.centralwidget.setObjectName("centralwidget")
                self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
                self.tabWidget.setEnabled(True)
                self.tabWidget.setGeometry(QtCore.QRect(10, 660, 1031, 351))
                sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
                self.tabWidget.setSizePolicy(sizePolicy)
                self.tabWidget.setMaximumSize(QtCore.QSize(1031, 351))
                font = QtGui.QFont()
                font.setPointSize(10)
                font.setBold(False)
                font.setUnderline(False)
                font.setWeight(50)
                font.setStrikeOut(False)
                font.setKerning(True)
                font.setStyleStrategy(QtGui.QFont.PreferDefault)
                self.tabWidget.setFont(font)
                self.tabWidget.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                self.tabWidget.setTabletTracking(False)
                self.tabWidget.setFocusPolicy(QtCore.Qt.TabFocus)
                self.tabWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                self.tabWidget.setAcceptDrops(False)
                self.tabWidget.setToolTipDuration(-1)
                self.tabWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
                self.tabWidget.setAutoFillBackground(False)
                self.tabWidget.setStyleSheet("""
                        QTabWidget::pane {
                                background-color: rgba(0, 0, 0, 115);
                                border: 1px solid rgba(255, 255, 255, 0.15);
                                border-radius: 15px;
                                top: -1px;
                        }
                        QTabBar::tab {
                                background-color: rgba(45, 45, 60, 150);
                                color: #BBB;
                                border: 1px solid rgba(255, 255, 255, 0.1);
                                border-bottom: none;
                                border-top-left-radius: 10px;
                                border-top-right-radius: 10px;
                                padding: 8px 16px;
                                margin-right: 4px;
                        }
                        QTabBar::tab:selected {
                                background-color: rgba(0, 120, 212, 180);
                                color: white;
                                border: 1px solid rgba(0, 242, 255, 0.4);
                        }
                        QTabBar::tab:hover {
                                background-color: rgba(60, 60, 80, 180);
                                color: white;
                        }
                """)
                self.tabWidget.setTabPosition(QtWidgets.QTabWidget.North)
                self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
                self.tabWidget.setElideMode(QtCore.Qt.ElideNone)
                self.tabWidget.setDocumentMode(False)
                self.tabWidget.setTabsClosable(False)
                self.tabWidget.setMovable(False)
                self.tabWidget.setTabBarAutoHide(False)
                self.tabWidget.setObjectName("tabWidget")
                self.distance_button = QPushButton(self.centralwidget)
                self.distance_button.setToolTip('Distance Button')
                self.distance_button.setGeometry(QtCore.QRect(1300, 700, 131, 50))
                self.distance_button.setText("Distance")
                self.distance_button.setCheckable(True)
                self.distance_button.setFont(QtGui.QFont("Arial", 11))
                self.distance_button.setVisible(True)
                self.distance_button.setStyleSheet(self.button_style)
                self.distance_button.clicked.connect(self.distancehide)
                self.distance_button.clicked.connect(self.button_check_Move)

                self.possition_button = QPushButton(self.centralwidget)
                self.possition_button.setToolTip('Possition Button')
                self.possition_button.setGeometry(QtCore.QRect(1300, 760, 131, 50))
                self.possition_button.setText("Position")
                self.possition_button.setCheckable(True)
                self.possition_button.setFont(QtGui.QFont("Arial", 11))
                self.possition_button.setVisible(True)
                self.possition_button.setStyleSheet(self.button_style)
                self.possition_button.clicked.connect(self.possitionhide)
                self.possition_button.clicked.connect(self.button_check)

                self.distance_buttonSample = self.distance_button
                self.possition_buttonSample = self.possition_button


                

               


              



                self.button_testmode_back = QPushButton(self.centralwidget)
                self.button_testmode_back.setGeometry(QtCore.QRect(1670, 710, 100, 40))
                self.button_testmode_back.setText("Testmode")
                self.button_testmode_back.setCheckable(True)
                self.button_testmode_back.setFont(QtGui.QFont("Arial", 8))  
                self.button_testmode_back.clicked.connect(self.send_Testmode_back)
                self.button_testmode_back.setStyleSheet(self.button_style)
                self.button_testmode_back.setToolTip('Test Mode On/Off')




                self.button_joymode = QPushButton(self.centralwidget)
                self.button_joymode.setGeometry(QtCore.QRect(1670, 760, 100, 40))
                self.button_joymode.setText("Joy Mode")
                self.button_joymode.setCheckable(True)
                self.button_joymode.setFont(QtGui.QFont("Arial", 8)) 
                self.button_joymode.clicked.connect(self.send_Joymode)
                self.button_joymode.setStyleSheet(self.button_style)
                self.button_joymode.setToolTip('Joy Mode On/Off')

                self.coordinates_label = QLabel(self.centralwidget)
                self.coordinates_label.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.coordinates_label.setGeometry(1050, 760, 200, 20)
                self.coordinates_label.setToolTip("Camera's Coordinate Datas")

                self.back_button= QPushButton(self.centralwidget)
                self.back_button.setGeometry(QtCore.QRect(1050,950,70,30))
                self.back_button.setText("BACK")
                self.back_button.setFont(QtGui.QFont("Arial", 4))
                # self.back_button.clicked.connect(self.back_button_setup)
                self.back_button.clicked.connect(ProcessScreen.close)
                self.back_button.setStyleSheet(self.button_style)
                self.back_button.setToolTip('Return to main menu')

              

                self.threshold_input = QLineEdit(self.centralwidget)
                self.threshold_input.setGeometry(1050, 730, 200, 20)
                self.threshold_input.setText("177")  # Başlangıçta 177 değeriyle açılır
                self.threshold_input.returnPressed.connect(self.update_threshold)
                self.threshold_input.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.threshold_input.setVisible(False)

                self.threshold_slider = QSlider(Qt.Horizontal , self.centralwidget)
                self.threshold_slider.setGeometry(1050,700,200,20)
                self.threshold_slider.setMaximum(255)
                self.threshold_slider.setMinimum(0)
                self.threshold_slider.setValue(177)
                self.threshold_slider.setVisible(True)
                self.threshold_slider.sliderPressed.connect(self.update_threshold)
                self.threshold_slider.setStyleSheet(
                        "QSlider::groove:horizontal {"
                        "    border: 1px solid #999999;"
                        "    height: 8px;"
                        "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #666666, stop:1 #222222);"
                        "}"

                        "QSlider::handle:horizontal {"
                        "    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b1b1b1, stop:0.5 #888888, stop:1 #b1b1b1);"
                        "    border: 1px solid #5c5c5c;"
                        "    width: 14px;"
                        "    margin: -3px 0;"
                        "    border-radius: 5px;"
                        "}"
                        )

                self.threshold_slider2 = QSlider(Qt.Horizontal , self.centralwidget)
                self.threshold_slider2.setGeometry(1050,730,200,20)
                self.threshold_slider2.setMaximum(255)
                self.threshold_slider2.setMinimum(0)
                self.threshold_slider2.setValue(177)
                self.threshold_slider2.setVisible(True)
                self.threshold_slider2.sliderPressed.connect(self.update_threshold2)
                self.threshold_slider2.setStyleSheet(
                        "QSlider::groove:horizontal {"
                        "    border: 1px solid #999999;"
                        "    height: 8px;"
                        "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #666666, stop:1 #222222);"
                        "}"

                        "QSlider::handle:horizontal {"
                        "    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b1b1b1, stop:0.5 #888888, stop:1 #b1b1b1);"
                        "    border: 1px solid #5c5c5c;"
                        "    width: 14px;"
                        "    margin: -3px 0;"
                        "    border-radius: 5px;"
                        "}"
                        )                                  

                self.camera_button = QPushButton(self.centralwidget)
                self.camera_button.setGeometry(QtCore.QRect(1700,700,60,90))
                self.camera_button.setText("")
                self.camera_button.setFont(QtGui.QFont("Arial", 8))
                self.camera_button.clicked.connect(self.open_camera)
                self.camera_button.setStyleSheet("background-color: transparent; color: #FFFFFF;")
                self.camera_button.setIcon(QtGui.QIcon(manager.get_image_path("Camera.png")))
                self.camera_button.setIconSize(QtCore.QSize(100, 100))
                self.camera_button.setVisible(False)


                # self.camera2_button = QPushButton(self.centralwidget)
                # self.camera2_button.setGeometry(QtCore.QRect(1300,800,60,90))
                # self.camera2_button.setText("")
                # self.camera2_button.setFont(QtGui.QFont("Arial", 8))
                # self.camera2_button.clicked.connect(self.open_camera2)
                # self.camera2_button.setStyleSheet("background-color: transparent; color: #FFFFFF;")
                # self.camera2_button.setIcon(QtGui.QIcon(manager.get_image_path("Camera.png")))
                # self.camera2_button.setIconSize(QtCore.QSize(100, 100))
                # self.camera2_button.setVisible(False)



                self.tab = QtWidgets.QWidget()
                self.tab.setObjectName("tab")
#TAB 1 BUTTONLAR  ################################################################################################################################################################################################

                self.ContactMode = QtWidgets.QLabel(self.tab)
                self.ContactMode.setGeometry(QtCore.QRect(440, 20, 111, 31))
                font = QtGui.QFont()
                font.setPointSize(10)
                self.ContactMode.setFont(font)
                self.ContactMode.setStyleSheet("background: transparent")
                self.ContactMode.setObjectName("ContactMode")
                self.tab.setToolTip('Contact Mode Tab')


                self.verticalLayoutWidgetProxymity = QtWidgets.QWidget(self.tab)
                self.verticalLayoutWidgetProxymity.setGeometry(QtCore.QRect(570,190,50,50))
                self.verticalLayoutWidgetProxymity.setObjectName("verticalLayoutWidgetProxymity")
                self.verticalLayoutWidgetProxymity.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                           #Proxymity
                self.verticalLayoutProxymity = QtWidgets.QVBoxLayout(self.verticalLayoutWidgetProxymity)
                self.verticalLayoutProxymity.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutProxymity.setObjectName("verticalLayoutProxymity")
                self.image_proxymity = QtWidgets.QLabel(self.verticalLayoutWidgetProxymity)
                self.image_proxymity.setObjectName("image_proxymity")
                self.image_proxymity.setStyleSheet("background: transparent")
                self.image_proxymity.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_proxymity.setVisible(True)
                self.image_proxymity.setScaledContents(True)
                self.verticalLayoutProxymity.addWidget(self.image_proxymity)

                self.verticalLayoutVC = QtWidgets.QWidget(self.tab)
                self.verticalLayoutVC.setGeometry(QtCore.QRect(130,190,50,50))
                self.verticalLayoutVC.setObjectName("verticalLayoutVC")
                self.verticalLayoutVC.setStyleSheet("background: transparent")                                   #Vacuum contact
                self.verticalLayoutVacuumCont = QtWidgets.QVBoxLayout(self.verticalLayoutVC)
                self.verticalLayoutVacuumCont.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutVacuumCont.setObjectName("verticalLayoutVacuumCont")
                self.image_VacuumContact = QtWidgets.QLabel(self.verticalLayoutVC)
                self.image_VacuumContact.setObjectName("image_VacuumContact")
                self.image_VacuumContact.setObjectName("image_VacuumContact")
                self.image_VacuumContact.setStyleSheet("background: transparent")
                self.image_VacuumContact.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_VacuumContact.setVisible(True)
                self.image_VacuumContact.setScaledContents(True)
                self.verticalLayoutVacuumCont.addWidget(self.image_VacuumContact)
                

                

                

                self.verticalLayoutSC = QtWidgets.QWidget(self.tab)
                self.verticalLayoutSC.setGeometry(QtCore.QRect(350,190,50,50))
                self.verticalLayoutSC.setObjectName("verticalLayoutSC")
                self.verticalLayoutSC.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #Soft Contact
                self.verticalLayoutSoftCont = QtWidgets.QVBoxLayout(self.verticalLayoutSC)
                self.verticalLayoutSoftCont.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutSoftCont.setObjectName("verticalLayoutSoftCont")
                self.image_SoftContact = QtWidgets.QLabel(self.verticalLayoutSC)
                self.image_SoftContact.setObjectName("image_SoftContact")
                self.image_SoftContact.setStyleSheet("background: transparent")
                self.image_SoftContact.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_SoftContact.setVisible(True)
                self.image_SoftContact.setScaledContents(True)
                self.verticalLayoutSoftCont.addWidget(self.image_SoftContact)

                self.verticalLayoutHC = QtWidgets.QWidget(self.tab)
                self.verticalLayoutHC.setGeometry(QtCore.QRect(780,190,50,50))
                self.verticalLayoutHC.setObjectName("verticalLayoutHC")
                self.verticalLayoutHC.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #Hard contact
                self.verticalLayoutHardCont = QtWidgets.QVBoxLayout(self.verticalLayoutHC)
                self.verticalLayoutHardCont.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutHardCont.setObjectName("verticalLayoutHardCont")
                self.image_HardContact = QtWidgets.QLabel(self.verticalLayoutHC)
                self.image_HardContact.setObjectName("image_HardContact")
                self.image_HardContact.setStyleSheet("background: transparent")
                self.image_HardContact.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_HardContact.setVisible(True)
                self.image_HardContact.setScaledContents(True)
                self.verticalLayoutHardCont.addWidget(self.image_HardContact)




                self.Proxymity = QtWidgets.QPushButton(self.tab)
                self.Proxymity.setGeometry(QtCore.QRect(520, 60, 161, 81))             #Proxymity btton
                self.Proxymity.setObjectName("Proxymity")
                self.Proxymity.setCheckable(True)
                self.Proxymity.setStyleSheet(self.button_style)
                self.Proxymity.clicked.connect(self.SendProxymity)
                self.ProxymityStatus = QtWidgets.QLabel(self.tab)
                self.ProxymityStatus.setGeometry(QtCore.QRect(520, 240, 181, 21))
                self.ProxymityStatus.setFont(font)
                self.ProxymityStatus.setStyleSheet("background: transparent")
                self.ProxymityStatus.setObjectName("ProxymityStatus")
                self.Proxymity.clicked.connect(self.ContactDisable4)
                self.Proxymity.setToolTip('Proxymity Button')

                self.verticalLayoutWidget = QtWidgets.QWidget(self.tab)
                self.verticalLayoutWidget.setGeometry(QtCore.QRect(520, 140, 161, 31))
                self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
                self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
                self.verticalLayout.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout.setObjectName("verticalLayout")
                self.lineEditSendDataProxymity = QtWidgets.QLineEdit(self.verticalLayoutWidget)                #exposure dos değeri girilen cubuk
                self.lineEditSendDataProxymity.setObjectName("lineEditSendData")
                self.lineEditSendDataProxymity.setText("20")
                self.verticalLayout.addWidget(self.lineEditSendDataProxymity)
                self.verticalLayoutWidget.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius : 5px;")



                self.line_5 = QtWidgets.QFrame(self.tab)
                self.line_5.setGeometry(QtCore.QRect(80, 170, 821, 21))
                self.line_5.setStyleSheet("background: transparent")
                self.line_5.setFrameShadow(QtWidgets.QFrame.Plain)
                self.line_5.setLineWidth(2)
                self.line_5.setFrameShape(QtWidgets.QFrame.HLine)
                self.line_5.setObjectName("line_5")

                self.VacuumContact = QtWidgets.QPushButton(self.tab)
                self.VacuumContact.setGeometry(QtCore.QRect(80, 60, 161, 81))            #Vacuum Contact Button
                self.VacuumContact.setObjectName("VacuumContact")
                self.VacuumContact.setCheckable(True)
                self.VacuumContact.setStyleSheet(self.button_style)
                self.VacuumContact.clicked.connect(self.SendVacuumContact)
                self.VacuumContactStatus = QtWidgets.QLabel(self.tab)
                self.VacuumContactStatus = QtWidgets.QLabel(self.tab)
                self.VacuumContactStatus.setGeometry(QtCore.QRect(80, 240, 181, 21))
                self.VacuumContactStatus.setFont(font)
                self.VacuumContactStatus.setStyleSheet("background: transparent")
                self.VacuumContactStatus.setObjectName("VacuumContactStatus")
                self.VacuumContact.clicked.connect(self.ContactDisable)
                self.VacuumContact.setToolTip('Vacuum Contact Button')



                self.SoftContact = QtWidgets.QPushButton(self.tab)
                self.SoftContact.setGeometry(QtCore.QRect(300, 60, 161, 81))              #Soft Cont
                self.SoftContact.setObjectName("SoftContact")
                self.SoftContact.setCheckable(True)
                self.SoftContact.setStyleSheet(self.button_style)
                self.SoftContact.clicked.connect(self.SendSoftContact)
                self.SoftContactStatus = QtWidgets.QLabel(self.tab)
                self.SoftContactStatus = QtWidgets.QLabel(self.tab)
                self.SoftContactStatus.setGeometry(QtCore.QRect(300, 240, 181, 21))
                self.SoftContactStatus.setFont(font)
                self.SoftContactStatus.setStyleSheet("background: transparent")
                self.SoftContactStatus.setObjectName("SoftContactStatus")
                self.SoftContact.clicked.connect(self.ContactDisable3)
                self.SoftContact.setToolTip("Soft Contact Button")
                self.SoftContact.setChecked(True)


                self.HardContact = QtWidgets.QPushButton(self.tab)
                self.HardContact.setGeometry(QtCore.QRect(730, 60, 161, 81))           #Hard cont
                self.HardContact.setObjectName("HardContact")
                self.HardContact.setCheckable(True)
                self.HardContact.setStyleSheet(self.button_style)
                self.HardContact.clicked.connect(self.SendHardContact)
                self.HardContactStatus = QtWidgets.QLabel(self.tab)
                self.HardContactStatus = QtWidgets.QLabel(self.tab)
                self.HardContactStatus.setGeometry(QtCore.QRect(730, 240, 181, 21))
                self.HardContactStatus.setFont(font)
                self.HardContactStatus.setStyleSheet("background: transparent")
                self.HardContactStatus.setObjectName("HardContactStatus")
                self.HardContact.clicked.connect(self.ContactDisable2)
                self.HardContact.setToolTip('Hard Contact Button')



                self.tabWidget.addTab(self.tab, "")

#TAB 2 Buttonlar################################################################################################################################################################################################
                self.tab_2 = QtWidgets.QWidget()
                self.tab_2.setObjectName("tab_2")
                self.tab_2.setToolTip('Settings Tab')


                 #LOG Kayıtları
                self.verticalLayoutWidgetlog = QtWidgets.QWidget(self.tab_2)
                self.verticalLayoutWidgetlog.setToolTip('LOG')
                self.verticalLayoutWidgetlog.setGeometry(QtCore.QRect(400, 180, 350, 100))
                self.verticalLayoutWidgetlog.setObjectName("verticalLayoutWidgetlog")
                self.verticalLayoutWidgetlog.setVisible(True)
                self.verticalLayoutWidgetlog.setStyleSheet("background-color: transparent;  border: 1px solid black; border-radius : 5px;")
                layoutlog = QtWidgets.QVBoxLayout(self.verticalLayoutWidgetlog) #layout oluşturma
                self.logTextEdit = QtWidgets.QTextEdit()
                self.logTextEdit.setReadOnly(True)
                log_layout = QtWidgets.QVBoxLayout()
                log_layout.addWidget(self.logTextEdit)
                layoutlog.addLayout(log_layout)

                self.label = QtWidgets.QLabel(str(self.currentValue), self.tab_2)
                self.label.setAlignment(QtCore.Qt.AlignCenter)
                self.label.setGeometry(QtCore.QRect(220, 60, 20, 20))

                self.plusButton = QtWidgets.QPushButton('+', self.tab_2)
                self.plusButton.clicked.connect(self.incrementValue)
                self.plusButton.setGeometry(QtCore.QRect(190, 60, 20, 20))
                
                self.minusButton = QtWidgets.QPushButton('-', self.tab_2)
                self.minusButton.clicked.connect(self.decrementValue)
                self.minusButton.setGeometry(QtCore.QRect(250, 60, 20, 20))
                        

                self.UpButton = QtWidgets.QPushButton(self.tab_2)
                self.UpButton.setGeometry(QtCore.QRect(60, 40, 121, 101))      #Zed Up butonu
                self.UpButton.setStyleSheet("background: transparent")
                self.UpButton.setObjectName("UpButton")
                self.UpButton.clicked.connect(self.SendDataZedYP)
                self.UpButton.clicked.connect(self.button_disableway)
                self.UpButton.setCheckable(True)
                self.UpButton.setFont(QtGui.QFont("Arial", 11))  
                self.UpButton.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2.png")))
                self.UpButton.setIconSize(QtCore.QSize(100, 100))
                self.UpButton.setToolTip('Zed Up Button')

                self.DownButton = QtWidgets.QPushButton(self.tab_2)
                self.DownButton.setGeometry(QtCore.QRect(60, 180, 121, 101))  #ZED down butonu
                self.DownButton.setStyleSheet("background: transparent")
                self.DownButton.setObjectName("DownButton")
                self.DownButton.clicked.connect(self.SendDataZedYN)
                self.DownButton.clicked.connect(self.button_disableway)
                self.DownButton.setCheckable(True)
                self.DownButton.setFont(QtGui.QFont("Arial", 11))  
                self.DownButton.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2.png")))
                self.DownButton.setIconSize(QtCore.QSize(100, 100)) 
                self.DownButton.setToolTip('Zed Down Button')

                self.um = QtWidgets.QLabel(self.tab_2)
                self.um.setGeometry(QtCore.QRect(820, 70, 55, 16))
                font = QtGui.QFont()
                font.setPointSize(10)
                self.um.setFont(font)
                self.um.setStyleSheet("background: transparent")
                self.um.setObjectName("um")
                self.mWcm = QtWidgets.QLabel(self.tab_2)
                self.mWcm.setGeometry(QtCore.QRect(820, 140, 91, 16))
                font = QtGui.QFont()
                font.setPointSize(10)
                self.mWcm.setFont(font)
                self.mWcm.setStyleSheet("background: transparent")
                self.mWcm.setObjectName("mWcm")
                self.Gap = QtWidgets.QLabel(self.tab_2)
                self.Gap.setGeometry(QtCore.QRect(480, 60, 71, 21))
                font = QtGui.QFont()
                font.setPointSize(12)
                self.Gap.setFont(font)
                self.Gap.setStyleSheet("background: transparent")
                self.Gap.setObjectName("Gap")
                


                

                self.GapButton = QtWidgets.QPushButton(self.tab_2)
                self.GapButton.setGeometry(QtCore.QRect(330, 50, 120, 40))      #Gap Up butonu
                self.GapButton.setStyleSheet(self.button_style)
                self.GapButton.setObjectName("GapButton")
                self.GapButton.setCheckable(True)
                self.GapButton.clicked.connect(self.GapDataSend)
                self.GapButton.setFont(QtGui.QFont("Arial", 10))
                self.GapButton.setToolTip('Setting the Gap value')


                self.ExposureButton = QtWidgets.QPushButton(self.tab_2)
                self.ExposureButton.setGeometry(QtCore.QRect(330, 120, 120, 40))  #Expo down butonu
                self.ExposureButton.setObjectName("ExposureButton")
                self.ExposureButton.setCheckable(True)
                self.ExposureButton.clicked.connect(self.ExpoSendData)
                self.ExposureButton.setFont(QtGui.QFont("Arial", 8))
                self.ExposureButton.setToolTip('Setting the Exposure Dose value')


        

                self.verticalLayoutWidget = QtWidgets.QWidget(self.tab_2)
                self.verticalLayoutWidget.setToolTip("Exposure Data, Default Value '5' ")
                self.verticalLayoutWidget.setGeometry(QtCore.QRect(620, 130, 181, 31))
                self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
                self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
                self.verticalLayout.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout.setObjectName("verticalLayout")
                self.lineEditSendDataExposure = QtWidgets.QLineEdit(self.verticalLayoutWidget)                #exposure dos değeri girilen cubuk
                self.lineEditSendDataExposure.setObjectName("lineEditSendData")
                self.lineEditSendDataExposure.setText("5")
                self.verticalLayout.addWidget(self.lineEditSendDataExposure)
                self.verticalLayoutWidget.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius : 5px;")

                self.verticalLayoutWidget = QtWidgets.QWidget(self.tab_2)
                self.verticalLayoutWidget.setToolTip("Gap Data, Default Value '2        0'")
                self.verticalLayoutWidget.setGeometry(QtCore.QRect(620, 60, 181, 31))
                self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
                self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
                self.verticalLayout.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout.setObjectName("verticalLayout")
                self.lineEditSendDataGap = QtWidgets.QLineEdit(self.verticalLayoutWidget)                #Gap değeri girilen cubuk
                self.lineEditSendDataGap.setObjectName("lineEditSendData")
                self.lineEditSendDataGap.setText("20")
                self.verticalLayout.addWidget(self.lineEditSendDataGap)
                self.verticalLayoutWidget.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius : 5px;")


                self.ExposureDose = QtWidgets.QLabel(self.tab_2)
                self.ExposureDose.setGeometry(QtCore.QRect(480, 130, 121, 20))
                font = QtGui.QFont()
                font.setPointSize(12)
                self.ExposureDose.setFont(font)
                self.ExposureButton.setStyleSheet(self.button_style)
                self.ExposureDose.setObjectName("ExposureDose")


                # self.MicroSpeed = QtWidgets.QPushButton(self.tab_2)
                # self.MicroSpeed.setGeometry(QtCore.QRect(540, 190, 161, 81))    #micspeed butonu
                # self.MicroSpeed.setObjectName("MicroSpeed")
                # self.MicroSpeed.setCheckable(True)
                # self.MicroSpeed.setStyleSheet("border : 1px solid black; border-radius :5px;")
                # self.MicroSpeed.clicked.connect(self.SendMicroSpeed)
              

                # self.SampleSpeed = QtWidgets.QPushButton(self.tab_2)
                # self.SampleSpeed.setGeometry(QtCore.QRect(710, 190, 161, 81))   #Speed butonu
                # self.SampleSpeed.setObjectName("SampleSpeed")
                # self.SampleSpeed.setCheckable(True)
                # self.SampleSpeed.setStyleSheet("border : 1px solid black; border-radius :5px;")
                # self.SampleSpeed.clicked.connect(self.SendSampleSpeed)


            


                self.line_9 = QtWidgets.QFrame(self.tab_2)
                self.line_9.setGeometry(QtCore.QRect(90, 410, 821, 20))
                self.line_9.setFrameShape(QtWidgets.QFrame.HLine)
                self.line_9.setFrameShadow(QtWidgets.QFrame.Sunken)
                self.line_9.setObjectName("line_9")
                self.textBrowser_2 = QtWidgets.QTextBrowser(self.tab_2)
                self.textBrowser_2.setGeometry(QtCore.QRect(660, 340, 191, 41))
                self.textBrowser_2.setObjectName("textBrowser_2")
                self.line_6 = QtWidgets.QFrame(self.tab_2)
                self.line_6.setGeometry(QtCore.QRect(90, 300, 861, 21))
                self.line_6.setFrameShadow(QtWidgets.QFrame.Plain)
                self.line_6.setLineWidth(2)
                self.line_6.setFrameShape(QtWidgets.QFrame.HLine)
                self.line_6.setObjectName("line_6")
                self.tabWidget.addTab(self.tab_2, "")


             

#TAB 4 ALANI
                self.tab_4 = QtWidgets.QWidget()
                self.tab_4.setObjectName("tab_4")

                self.verticalLayoutMaskLU = QtWidgets.QWidget(self.tab_4)
                self.verticalLayoutMaskLU.setGeometry(QtCore.QRect(290,60,50,50))
                self.verticalLayoutMaskLU.setObjectName("verticalLayoutMaskLU")
                self.verticalLayoutMaskLU.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #MASK LOAD UNLOAD
                self.verticalLayoutMaskLoadU = QtWidgets.QVBoxLayout(self.verticalLayoutMaskLU)
                self.verticalLayoutMaskLoadU.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutMaskLoadU.setObjectName("verticalLayoutMaskLoadU")
                self.image_MaskLU = QtWidgets.QLabel(self.verticalLayoutMaskLU)
                self.image_MaskLU.setObjectName("image_MaskLU")
                self.image_MaskLU.setStyleSheet("background: transparent")
                self.image_MaskLU.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_MaskLU.setVisible(True)
                self.image_MaskLU.setScaledContents(True)
                self.verticalLayoutMaskLoadU.addWidget(self.image_MaskLU)

                self.verticalLayoutWidget_SampleHLoad = QtWidgets.QWidget(self.tab_4)
                self.verticalLayoutWidget_SampleHLoad.setGeometry(QtCore.QRect(630,60,50,50))
                self.verticalLayoutWidget_SampleHLoad.setObjectName("verticalLayoutWidget_SampleHLoad")
                self.verticalLayoutWidget_SampleHLoad.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #Sample Holder LOad / Unload
                self.verticalLayout_SHLoad = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_SampleHLoad)
                self.verticalLayout_SHLoad.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout_SHLoad.setObjectName("verticalLayout_SHLoad")
                self.image_SampleHolderLoad = QtWidgets.QLabel(self.verticalLayoutWidget_SampleHLoad)
                self.image_SampleHolderLoad.setObjectName("image_SampleHolderLoad")
                self.image_SampleHolderLoad.setStyleSheet("background: transparent")
                self.image_SampleHolderLoad.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_SampleHolderLoad.setVisible(True)
                self.image_SampleHolderLoad.setScaledContents(True)
                self.verticalLayout_SHLoad.addWidget(self.image_SampleHolderLoad)

                self.verticalLayoutWidget_MaskHolderV = QtWidgets.QWidget(self.tab_4)
                self.verticalLayoutWidget_MaskHolderV.setGeometry(QtCore.QRect(130,210,50,50))
                self.verticalLayoutWidget_MaskHolderV.setObjectName("verticalLayoutWidget_MaskHolderV")
                self.verticalLayoutWidget_MaskHolderV.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #MAsk Holder Vacuum
                self.verticalLayout_MaskHV = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_MaskHolderV)
                self.verticalLayout_MaskHV.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout_MaskHV.setObjectName("verticalLayout_MaskHV")
                self.image_MaskHolderVacuum = QtWidgets.QLabel(self.verticalLayoutWidget_MaskHolderV)
                self.image_MaskHolderVacuum.setObjectName("image_MaskHolderVacuum")
                self.image_MaskHolderVacuum.setStyleSheet("background: transparent")
                self.image_MaskHolderVacuum.setPixmap(QtGui.QPixmap(""))
                self.image_MaskHolderVacuum.setVisible(True)
                self.image_MaskHolderVacuum.setScaledContents(True)
                self.verticalLayout_MaskHV.addWidget(self.image_MaskHolderVacuum)

                self.verticalLayoutWidget_MaskVacuum = QtWidgets.QWidget(self.tab_4)
                self.verticalLayoutWidget_MaskVacuum.setGeometry(QtCore.QRect(130,210,50,50))
                self.verticalLayoutWidget_MaskVacuum.setObjectName("verticalLayoutWidget_MaskVacuum")
                self.verticalLayoutWidget_MaskVacuum.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #Mask Vacuum
                self.verticalLayoutMaskVacuum = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_MaskVacuum)
                self.verticalLayoutMaskVacuum.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutMaskVacuum.setObjectName("verticalLayoutMaskVacuum")
                self.image_MaskVacuum = QtWidgets.QLabel(self.verticalLayoutWidget_MaskVacuum)
                self.image_MaskVacuum.setObjectName("image_MaskVacuum")
                self.image_MaskVacuum.setStyleSheet("background: transparent")
                self.image_MaskVacuum.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_MaskVacuum.setVisible(True)
                self.image_MaskVacuum.setScaledContents(True)
                self.verticalLayoutMaskVacuum.addWidget(self.image_MaskVacuum)

                self.verticalLayoutWidget_SampleVacuum = QtWidgets.QWidget(self.tab_4)
                self.verticalLayoutWidget_SampleVacuum.setGeometry(QtCore.QRect(820,210,50,50))
                self.verticalLayoutWidget_SampleVacuum.setObjectName("verticalLayoutWidget_SampleVacuum")
                self.verticalLayoutWidget_SampleVacuum.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #Sample Vacuum
                self.verticalLayoutSampleVacuum = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_SampleVacuum)
                self.verticalLayoutSampleVacuum.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutSampleVacuum.setObjectName("verticalLayoutSampleVacuum")
                self.image_SampleVacuum = QtWidgets.QLabel(self.verticalLayoutWidget_SampleVacuum)
                self.image_SampleVacuum.setObjectName("image_SampleVacuum")
                self.image_SampleVacuum.setStyleSheet("background: transparent")
                self.image_SampleVacuum.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_SampleVacuum.setVisible(True)
                self.image_SampleVacuum.setScaledContents(True)
                self.verticalLayoutSampleVacuum.addWidget(self.image_SampleVacuum)

                self.MaskLoad = QtWidgets.QPushButton(self.tab_4)
                self.MaskLoad.setToolTip('İşlevsiz')
                self.MaskLoad.setGeometry(QtCore.QRect(420, 20, 151, 71))
                self.MaskLoad.setObjectName("MaskLoad")
                self.MaskLoad.setCheckable(True)
                self.MaskLoad.setStyleSheet(self.button_style)
                self.MaskLoad.clicked.connect(self.SendMaskLoad)
                self.MaskLoadStatus = QtWidgets.QLabel(self.tab_4)
                self.MaskLoadStatus.setGeometry(QtCore.QRect(520, 240, 181, 21))
                self.MaskLoadStatus.setFont(font)
                self.MaskLoadStatus.setStyleSheet("background: transparent")
                self.MaskLoadStatus.setObjectName("MaskLoadStatus")
                self.MaskLoad.clicked.connect(self.MaskControl)





                # self.MaskHolderLock = QtWidgets.QPushButton(self.tab_4)
                # self.MaskHolderLock.setGeometry(QtCore.QRect(80, 130, 151, 61))
                # self.MaskHolderLock.setObjectName("MaskHolderLock")
                # self.MaskHolderLock.setCheckable(True)
                # self.MaskHolderLock.setStyleSheet("border : 1px solid black; border-radius :5px;")
                # self.MaskHolderLock.clicked.connect(self.SendMaskHolderLock)
                # self.MaskHolderLocktatus = QtWidgets.QLabel(self.tab_4)
                # self.MaskHolderLocktatus.setGeometry(QtCore.QRect(520, 240, 181, 21))
                # self.MaskHolderLocktatus.setFont(font)
                # self.MaskHolderLocktatus.setStyleSheet("background: transparent")
                # self.MaskHolderLocktatus.setObjectName("MaskHolderLocktatus")
                # self.MaskHolderLock.clicked.connect(self.MaskControl2)


        


                self.MaskVacuum = QtWidgets.QPushButton(self.tab_4)
                self.MaskVacuum.setToolTip('Mask Vacuum Button')
                self.MaskVacuum.setGeometry(QtCore.QRect(100, 130, 151, 61))
                self.MaskVacuum.setObjectName("MaskVacuum")
                self.MaskVacuum.setCheckable(True)
                self.MaskVacuum.setStyleSheet(self.button_style)
                self.MaskVacuum.clicked.connect(self.SendMaskVacuum)
                self.MaskVacuumStatus = QtWidgets.QLabel(self.tab_4)
                self.MaskVacuumStatus.setGeometry(QtCore.QRect(90, 260, 200, 21))
                self.MaskVacuumStatus.setFont(font)
                self.MaskVacuumStatus.setStyleSheet("background: transparent")
                self.MaskVacuumStatus.setObjectName("MaskVacuumStatus")
                self.MaskVacuum.clicked.connect(self.MaskControl3)


                self.SampleVacuum = QtWidgets.QPushButton(self.tab_4)
                self.SampleVacuum.setToolTip('Sample Vacuum Button')
                self.SampleVacuum.setGeometry(QtCore.QRect(770, 130, 151, 61))
                self.SampleVacuum.setObjectName("SampleVacuum")
                self.SampleVacuum.setCheckable(True)
                self.SampleVacuum.setStyleSheet(self.button_style)
                self.SampleVacuum.clicked.connect(self.SendSampleVacuum)
                self.SampleVacuumStatus = QtWidgets.QLabel(self.tab_4)
                self.SampleVacuumStatus.setGeometry(QtCore.QRect(760, 260, 210, 21))
                self.SampleVacuumStatus.setFont(font)
                self.SampleVacuumStatus.setStyleSheet("background: transparent")
                self.SampleVacuumStatus.setObjectName("SampleVacuumStatus")
                self.SampleVacuum.clicked.connect(self.MaskControl4)


                self.MaskHolderVacuumStatus = QtWidgets.QLabel(self.tab_4)
                self.MaskHolderVacuumStatus.setGeometry(QtCore.QRect(80, 240, 161, 21))
                font = QtGui.QFont()
                font.setPointSize(10)
                self.MaskHolderVacuumStatus.setFont(font)
                self.MaskHolderVacuumStatus.setStyleSheet("background: transparent")
                self.MaskHolderVacuumStatus.setObjectName("MaskHolderVacuumStatus")
                self.line_8 = QtWidgets.QFrame(self.tab_4)
                self.line_8.setGeometry(QtCore.QRect(80, 200, 841, 21))
                self.line_8.setStyleSheet("background: transparent")
                self.line_8.setFrameShadow(QtWidgets.QFrame.Plain)
                self.line_8.setLineWidth(2)
                self.line_8.setFrameShape(QtWidgets.QFrame.HLine)
                self.line_8.setObjectName("line_8")
                self.MaskLoad_2 = QtWidgets.QLabel(self.tab_4)
                self.MaskLoad_2.setGeometry(QtCore.QRect(240, 20, 151, 61))
                font = QtGui.QFont()
                font.setPointSize(10)
                self.MaskLoad_2.setFont(font)
                self.MaskLoad_2.setStyleSheet("background: transparent")
                self.MaskLoad_2.setObjectName("MaskLoad_2")
                self.SampleHolderLoad = QtWidgets.QLabel(self.tab_4)
                self.SampleHolderLoad.setGeometry(QtCore.QRect(580, 20, 211, 61))
                font = QtGui.QFont()
                font.setPointSize(10)
                self.SampleHolderLoad.setFont(font)
                self.SampleHolderLoad.setStyleSheet("background: transparent")
                self.SampleHolderLoad.setObjectName("SampleHolderLoad")
                self.tabWidget.addTab(self.tab_4, "")


#Tab 5                 
                self.tab_Align = QtWidgets.QWidget()
                self.tab_Align.setObjectName("tab_5")
                self.tab_Align.setEnabled(True)

                inner_inner_tab_widget = QtWidgets.QTabWidget(self.tab_Align)
                inner_inner_tab_widget.setGeometry(QtCore.QRect(0, 0, 1200, 400))  # İç içe sekmenin boyutu ve konumu
                inner_inner_tab_widget.setObjectName("inner_inner_tab_widget")
                inner_inner_tab_widget.setStyleSheet("""
                        QTabWidget::pane {
                                background-color: rgba(0, 0, 0, 100);
                                border: 1px solid rgba(255, 255, 255, 0.1);
                                border-radius: 12px;
                                top: -1px;
                        }
                        QTabBar::tab {
                                background-color: rgba(40, 40, 50, 130);
                                color: #999;
                                border: 1px solid rgba(255, 255, 255, 0.05);
                                border-bottom: none;
                                border-top-left-radius: 8px;
                                border-top-right-radius: 8px;
                                padding: 6px 12px;
                                margin-right: 3px;
                                font-size: 9pt;
                        }
                        QTabBar::tab:selected {
                                background-color: rgba(0, 120, 212, 160);
                                color: white;
                                border: 1px solid rgba(0, 242, 255, 0.3);
                        }
                """)

                inner_inner_tab1 = QtWidgets.QWidget()
                inner_inner_tab_widget.addTab(inner_inner_tab1, "Sample Process")

                self.verticalLayoutWidget = QtWidgets.QWidget(inner_inner_tab1)
                self.verticalLayoutWidget.setToolTip('Send X Data (THETA)')
                self.verticalLayoutWidget.setGeometry(QtCore.QRect(515, 60, 120, 23))
                self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
                self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
                self.verticalLayout.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout.setObjectName("verticalLayout")
                self.lineEditSendDatatab6 = QtWidgets.QLineEdit(self.verticalLayoutWidget)
                self.lineEditSendDatatab6.setObjectName("lineEditSendDatatab6")
                self.verticalLayout.addWidget(self.lineEditSendDatatab6)
                self.verticalLayoutWidget.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius : 5px;")

                #send data2
                self.verticalLayoutWidget_8 =QtWidgets.QWidget(inner_inner_tab1)
                self.verticalLayoutWidget_8.setToolTip('Send Y Data')
                self.verticalLayoutWidget_8.setGeometry(QtCore.QRect(515, 20, 120, 23))
                self.verticalLayoutWidget_8.setObjectName("verticalLayoutWidget")
                self.verticalLayoutWidget_8.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius : 5px;")
                self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_8)
                self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout_8.setObjectName("verticalLayout")
                self.lineEditSendData_2tab6 = QtWidgets.QLineEdit(self.verticalLayoutWidget_8)
                self.lineEditSendData_2tab6.setObjectName("lineEditSendData_2tab6")
                self.verticalLayout_8.addWidget(self.lineEditSendData_2tab6)

                self.Theta = QtWidgets.QPushButton(inner_inner_tab1)
                self.Theta.setToolTip('Theta Button')
                self.Theta.setGeometry(QtCore.QRect(80, 20, 131, 81))
                self.Theta.setObjectName("Theta")
                self.Theta.setCheckable(True)
                self.Theta.clicked.connect(self.Theta_button_clicked)
                self.Theta.clicked.connect(self.ButtonDisable)
                self.Theta.setStyleSheet(self.button_style)

                


                self.SampleXY = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleXY.setToolTip('Sample X/Y Button')
                self.SampleXY.setGeometry(QtCore.QRect(280, 20, 131, 81))
                self.SampleXY.setObjectName("SampleXY")
                self.SampleXY.setCheckable(True)
                self.SampleXY.clicked.connect(self.sample_button_clicked)
                self.SampleXY.clicked.connect(self.ButtonDisable)
                self.SampleXY.setStyleSheet(self.button_style)


                #Sample X Y Butons

                self.SampleUP = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleUP.setGeometry(QtCore.QRect(800, 10, 101, 91))
                self.SampleUP.setStyleSheet("background:transparent")
                self.SampleUP.setText("")
                self.SampleUP.setObjectName("UpButton_2")
                self.SampleUP.setVisible(False)
                self.SampleUP.clicked.connect(self.button_disableway)
                self.SampleUP.clicked.connect(self.SampleYP)
                self.SampleUP.setCheckable(True)
                self.SampleUP.setFont(QtGui.QFont("Arial", 11))  
                self.SampleUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2.png")))
                self.SampleUP.setIconSize(QtCore.QSize(100, 100))


                self.SampleDOWN = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleDOWN.setGeometry(QtCore.QRect(800, 180, 101, 91))
                self.SampleDOWN.setStyleSheet("background:transparent")
                self.SampleDOWN.setText("")
                self.SampleDOWN.clicked.connect(self.button_disableway)
                self.SampleDOWN.setObjectName("DownButton_2")
                self.SampleDOWN.setVisible(False)
                self.SampleDOWN.clicked.connect(self.SampleYN)
                self.SampleDOWN.setCheckable(True)
                self.SampleDOWN.setFont(QtGui.QFont("Arial", 11))  
                self.SampleDOWN.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2.png")))
                self.SampleDOWN.setIconSize(QtCore.QSize(100, 100))




                self.SampleRIGHT = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleRIGHT.setGeometry(QtCore.QRect(900, 90, 101, 91))
                self.SampleRIGHT.setStyleSheet("background:transparent")
                self.SampleRIGHT.setText("")
                self.SampleRIGHT.clicked.connect(self.button_disableway)
                self.SampleRIGHT.setObjectName("RightButton")
                self.SampleRIGHT.setVisible(False)
                self.SampleRIGHT.clicked.connect(self.SampleXP)
                self.SampleRIGHT.setCheckable(True)
                self.SampleRIGHT.setFont(QtGui.QFont("Arial", 11))  
                self.SampleRIGHT.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2.png")))
                self.SampleRIGHT.setIconSize(QtCore.QSize(100, 100))




                self.SampleLEFT = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleLEFT.setGeometry(QtCore.QRect(700, 90, 101, 91))
                self.SampleLEFT.setStyleSheet("background:transparent")
                self.SampleLEFT.setText("")
                self.SampleLEFT.clicked.connect(self.button_disableway)
                self.SampleLEFT.setObjectName("LeftButton")
                self.SampleLEFT.setVisible(False)
                self.SampleLEFT.clicked.connect(self.SampleXN)
                self.SampleLEFT.setCheckable(True)
                self.SampleLEFT.setFont(QtGui.QFont("Arial", 11))  
                self.SampleLEFT.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2.png")))
                self.SampleLEFT.setIconSize(QtCore.QSize(100, 100))


                self.SampleDistanceX = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleDistanceX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.SampleDistanceX.setStyleSheet(self.button_style)
                self.SampleDistanceX.clicked.connect(self.button_disableway)
                self.SampleDistanceX.setVisible(False)
                self.SampleDistanceX.clicked.connect(self.SampleDissXdata)
                self.SampleDistanceX.setObjectName("X Button")
                self.SampleDistanceX.setCheckable(False)
                self.SampleDistanceX.setFont(QtGui.QFont("Arial", 8))

                self.SampleDistanceY = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleDistanceY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.SampleDistanceY.setStyleSheet(self.button_style)
                self.SampleDistanceY.clicked.connect(self.button_disableway)
                self.SampleDistanceY.setVisible(False)
                self.SampleDistanceY.clicked.connect(self.SampleDissYdata)
                self.SampleDistanceY.setObjectName("Y Button")
                self.SampleDistanceY.setCheckable(False)
                self.SampleDistanceY.setFont(QtGui.QFont("Arial", 8)) 

                self.SampleDistanceGOXY = QtWidgets.QPushButton(inner_inner_tab1)
                self.SampleDistanceGOXY.setGeometry(QtCore.QRect(800, 170, 100, 70))
                self.SampleDistanceGOXY.setStyleSheet(self.button_style)
                self.SampleDistanceGOXY.clicked.connect(self.button_disableway)
                self.SampleDistanceGOXY.setVisible(False)
                self.SampleDistanceGOXY.clicked.connect(self.SampleYP)
                self.SampleDistanceGOXY.setObjectName("GOXY Button")
                self.SampleDistanceGOXY.setCheckable(False)
                self.SampleDistanceGOXY.setFont(QtGui.QFont("Arial", 8))

                #Sample Possition Buttons
                self.SamplePossitionX = QtWidgets.QPushButton(inner_inner_tab1)
                self.SamplePossitionX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.SamplePossitionX.setStyleSheet(self.button_style)
                self.SamplePossitionX.clicked.connect(self.button_disableway)
                self.SamplePossitionX.setVisible(False)
                self.SamplePossitionX.clicked.connect(self.SamplePossXdata)
                self.SamplePossitionX.setObjectName("X Button")
                self.SamplePossitionX.setCheckable(False)
                self.SamplePossitionX.setFont(QtGui.QFont("Arial", 8))

                self.SamplePossitionY = QtWidgets.QPushButton(inner_inner_tab1)
                self.SamplePossitionY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.SamplePossitionY.setStyleSheet(self.button_style)
                self.SamplePossitionY.clicked.connect(self.button_disableway)
                self.SamplePossitionY.setVisible(False)
                self.SamplePossitionY.clicked.connect(self.SamplePossYdata)
                self.SamplePossitionY.setObjectName("Y Button")
                self.SamplePossitionY.setCheckable(False)
                self.SamplePossitionY.setFont(QtGui.QFont("Arial", 8)) 

                self.SamplePossitionMOVEXY = QtWidgets.QPushButton(inner_inner_tab1)
                self.SamplePossitionMOVEXY.setGeometry(QtCore.QRect(800, 170, 100, 70))
                self.SamplePossitionMOVEXY.setStyleSheet(self.button_style)
                self.SamplePossitionMOVEXY.clicked.connect(self.button_disableway)
                self.SamplePossitionMOVEXY.setVisible(False)
                self.SamplePossitionMOVEXY.clicked.connect(self.SampleYP)
                self.SamplePossitionMOVEXY.setObjectName("MOVEXY Button")
                self.SamplePossitionMOVEXY.setCheckable(False)
                self.SamplePossitionMOVEXY.setFont(QtGui.QFont("Arial", 8))

#Theta Buttons





                self.ThetaRIGHT = QtWidgets.QPushButton(inner_inner_tab1)
                self.ThetaRIGHT.setGeometry(QtCore.QRect(900, 90, 101, 91))
                self.ThetaRIGHT.setStyleSheet("background:transparent")
                self.ThetaRIGHT.setText("")
                self.ThetaRIGHT.clicked.connect(self.button_disableway)
                self.ThetaRIGHT.setObjectName("RightButton")
                self.ThetaRIGHT.setVisible(False)
                self.ThetaRIGHT.clicked.connect(self.ThetaXP)
                self.ThetaRIGHT.setCheckable(True)
                self.ThetaRIGHT.setFont(QtGui.QFont("Arial", 11))  
                self.ThetaRIGHT.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2.png")))
                self.ThetaRIGHT.setIconSize(QtCore.QSize(100, 100))




                self.ThetaLEFT = QtWidgets.QPushButton(inner_inner_tab1)
                self.ThetaLEFT.setGeometry(QtCore.QRect(700, 90, 101, 91))
                self.ThetaLEFT.setStyleSheet("background:transparent")
                self.ThetaLEFT.setText("")
                self.ThetaLEFT.clicked.connect(self.button_disableway)
                self.ThetaLEFT.setObjectName("LeftButton")
                self.ThetaLEFT.setVisible(False)
                self.ThetaLEFT.clicked.connect(self.ThetaXN)
                self.ThetaLEFT.setCheckable(True)
                self.ThetaLEFT.setFont(QtGui.QFont("Arial", 11))  
                self.ThetaLEFT.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2.png")))
                self.ThetaLEFT.setIconSize(QtCore.QSize(100, 100))

                self.ThetaDistanceX = QtWidgets.QPushButton(inner_inner_tab1)
                self.ThetaDistanceX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.ThetaDistanceX.setStyleSheet(self.button_style)
                self.ThetaDistanceX.clicked.connect(self.button_disableway)
                self.ThetaDistanceX.setVisible(False)
                self.ThetaDistanceX.clicked.connect(self.ThetaDissGo)
                self.ThetaDistanceX.setObjectName("X Button")
                self.ThetaDistanceX.setCheckable(False)
                self.ThetaDistanceX.setFont(QtGui.QFont("Arial", 8))

                self.ThetaDistanceY = QtWidgets.QPushButton(inner_inner_tab1)
                self.ThetaDistanceY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.ThetaDistanceY.setStyleSheet(self.button_style)
                self.ThetaDistanceY.clicked.connect(self.button_disableway)
                self.ThetaDistanceY.setVisible(False)
                self.ThetaDistanceY.clicked.connect(self.ThetaDissGo)
                self.ThetaDistanceY.setObjectName("Y Button")
                self.ThetaDistanceY.setCheckable(False)
                self.ThetaDistanceY.setFont(QtGui.QFont("Arial", 8))

                self.ThetaPossitionX = QtWidgets.QPushButton(inner_inner_tab1)
                self.ThetaPossitionX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.ThetaPossitionX.setStyleSheet(self.button_style)
                self.ThetaPossitionX.clicked.connect(self.button_disableway)
                self.ThetaPossitionX.setVisible(False)
                self.ThetaPossitionX.clicked.connect(self.ThetaPossMove)
                self.ThetaPossitionX.setObjectName("X Button")
                self.ThetaPossitionX.setCheckable(False)
                self.ThetaPossitionX.setFont(QtGui.QFont("Arial", 8))

                self.ThetaPossitionY = QtWidgets.QPushButton(inner_inner_tab1)
                self.ThetaPossitionY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.ThetaPossitionY.setStyleSheet(self.button_style)
                self.ThetaPossitionY.clicked.connect(self.button_disableway)
                self.ThetaPossitionY.setVisible(False)
                self.ThetaPossitionY.clicked.connect(self.ThetaPossMove)
                self.ThetaPossitionY.setObjectName("Y Button")
                self.ThetaPossitionY.setCheckable(False)
                self.ThetaPossitionY.setFont(QtGui.QFont("Arial", 8)) 
                
                


                self.GapDoc_4 = QtWidgets.QLineEdit(inner_inner_tab1)
                self.GapDoc_4.setToolTip('Sample X Datas')
                self.GapDoc_4.setGeometry(QtCore.QRect(280, 110, 131, 31))
                self.GapDoc_4.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_4.setObjectName("Sample")
                self.GapDoc_layout4 = QtWidgets.QGridLayout(self.GapDoc_4)
                self.GapDoc_layout4.setObjectName("4")
                self.GapDoc_layout4.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout4.addWidget(self.bufferSampleXY)

                self.GapDoc_4 = QtWidgets.QLineEdit(inner_inner_tab1)
                self.GapDoc_4.setToolTip('Sample Y Datas')
                self.GapDoc_4.setGeometry(QtCore.QRect(280, 151, 131, 31))
                self.GapDoc_4.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_4.setObjectName("Sample")
                self.GapDoc_layout4 = QtWidgets.QGridLayout(self.GapDoc_4)
                self.GapDoc_layout4.setObjectName("4")
                self.GapDoc_layout4.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout4.addWidget(self.bufferSampleY)


                self.GapDoc_5 = QtWidgets.QLineEdit(inner_inner_tab1)
                self.GapDoc_5.setToolTip('Theta X Datas')
                self.GapDoc_5.setGeometry(QtCore.QRect(80, 110, 131, 31))
                self.GapDoc_5.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_5.setObjectName("Theta")
                self.GapDoc_layout5 = QtWidgets.QGridLayout(self.GapDoc_5)
                self.GapDoc_layout5.setObjectName("5")
                self.GapDoc_layout5.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout5.addWidget(self.bufferTheta)

                self.verticalLayoutWidget_4 = QtWidgets.QWidget(inner_inner_tab1)
                self.verticalLayoutWidget_4.setToolTip('Set Speed Value')
                self.verticalLayoutWidget_4.setGeometry(QtCore.QRect(100, 180, 300, 100))
                self.verticalLayoutWidget_4.setStyleSheet("background-color: transparent; color: black")  
                self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_4)
                self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)

                self.progress_bar_4 = QtWidgets.QProgressBar(self.verticalLayoutWidget_4)
                self.progress_bar_4.setStyleSheet("QProgressBar { color: black; }")
                self.progress_bar_4.setInvertedAppearance(True)
                self.slider_4 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.verticalLayoutWidget_4)
                self.slider_4.setStyleSheet("background-color : #f5f5f5;")  
                self.slider_4.setRange(0, 100)
                self.slider_4.valueChanged.connect(self.update_progress_bar)
                self.slider_4.valueChanged.connect(self.update_motor_speed4)

                self.verticalLayout_4.addWidget(self.progress_bar_4)
                self.verticalLayout_4.addWidget(self.slider_4)

                # İkinci iç içe sekme
                inner_inner_tab2 = QtWidgets.QWidget()
                inner_inner_tab_widget.addTab(inner_inner_tab2, "Microscope Process")


                #Send data1
                self.verticalLayoutWidget = QtWidgets.QWidget(inner_inner_tab2)
                self.verticalLayoutWidget.setToolTip('Send X Data')
                self.verticalLayoutWidget.setGeometry(QtCore.QRect(555, 65, 120, 23))
                self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
                self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
                self.verticalLayout.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout.setObjectName("verticalLayout")
                self.lineEditSendData = QtWidgets.QLineEdit(self.verticalLayoutWidget)
                self.lineEditSendData.setObjectName("lineEditSendData")
                self.verticalLayout.addWidget(self.lineEditSendData)
                self.verticalLayoutWidget.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius : 5px;")

                #send data2
                self.verticalLayoutWidget_8 =QtWidgets.QWidget(inner_inner_tab2)
                self.verticalLayoutWidget_8.setToolTip('Send Y Data ')
                self.verticalLayoutWidget_8.setGeometry(QtCore.QRect(555, 25, 120, 23))
                self.verticalLayoutWidget_8.setObjectName("verticalLayoutWidget")
                self.verticalLayoutWidget_8.setStyleSheet("background-color: transparent; border: 1px solid black; border-radius : 5px;")
                self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_8)
                self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout_8.setObjectName("verticalLayout")
                self.lineEditSendData_2 = QtWidgets.QLineEdit(self.verticalLayoutWidget_8)
                self.lineEditSendData_2.setObjectName("verticalLayout_8")
                self.verticalLayout_8.addWidget(self.lineEditSendData_2)

#Tab 3 BUttonlar

      


                self.MicRight = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRight.setGeometry(QtCore.QRect(380, 20, 131, 81))
                self.MicRight.setObjectName("MicRight")
                self.MicRight.setCheckable(True)
                self.MicRight.clicked.connect(self.MicroS_button_clicked)
                self.MicRight.clicked.connect(self.ButtonDisable)
                self.MicRight.setStyleSheet(self.button_style)
                self.MicRight.setToolTip('Microscope Right Button')


                self.MicLeft = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeft.setGeometry(QtCore.QRect(220, 20, 131, 81))
                self.MicLeft.setObjectName("MicLeft")
                self.MicLeft.setCheckable(True)
                self.MicLeft.clicked.connect(self.MicroL_button_clicked)
                self.MicLeft.clicked.connect(self.ButtonDisable)
                self.MicLeft.setStyleSheet(self.button_style)
                self.MicLeft.setToolTip('Microscope Left Button')


                self.MicRightZed = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightZed.setGeometry(QtCore.QRect(60, 150, 131, 81))
                self.MicRightZed.setObjectName("MicRightZed")
                self.MicRightZed.setCheckable(True)
                self.MicRightZed.clicked.connect(self.MRZ_button_clicked)
                self.MicRightZed.clicked.connect(self.ButtonDisable)
                self.MicRightZed.setStyleSheet(self.button_style)
                self.MicRightZed.setToolTip('Microscope Right Zed Button')


                self.MicLeftZed = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftZed.setGeometry(QtCore.QRect(60, 20, 131, 81))
                self.MicLeftZed.setObjectName("MicLeftZed")
                self.MicLeftZed.setCheckable(True)
                self.MicLeftZed.clicked.connect(self.MLZ_button_clicked)
                self.MicLeftZed.clicked.connect(self.ButtonDisable)
                self.MicLeftZed.setStyleSheet(self.button_style)
                self.MicLeftZed.setToolTip('Microscope Left Zed Button')



#Mic Left Zed Butonları
                self.MicLeftZedUP = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftZedUP.setGeometry(QtCore.QRect(800, 10, 101, 91))
                self.MicLeftZedUP.setStyleSheet("background:transparent")
                self.MicLeftZedUP.setText("")
                self.MicLeftZedUP.setObjectName("UpButton_2")
                self.MicLeftZedUP.setVisible(False)
                self.MicLeftZedUP.clicked.connect(self.MicLeftZedYP)
                self.MicLeftZedUP.setCheckable(True)
                self.MicLeftZedUP.clicked.connect(self.button_disableway)
                self.MicLeftZedUP.setFont(QtGui.QFont("Arial", 11))  
                self.MicLeftZedUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2.png")))
                self.MicLeftZedUP.setIconSize(QtCore.QSize(100, 100))

                #MicLeftZedUp Possition Buttons
                self.LeftZedPossition = QtWidgets.QPushButton(inner_inner_tab2)
                self.LeftZedPossition.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.LeftZedPossition.setStyleSheet(self.button_style)
                self.LeftZedPossition.clicked.connect(self.button_disableway)
                self.LeftZedPossition.setVisible(False)
                self.LeftZedPossition.clicked.connect(self.MicLeftZedYP)
                self.LeftZedPossition.setObjectName("Possition Button")
                self.LeftZedPossition.setCheckable(False)
                self.LeftZedPossition.setFont(QtGui.QFont("Arial", 8))

                self.LeftZedDistance = QtWidgets.QPushButton(inner_inner_tab2)
                self.LeftZedDistance.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.LeftZedDistance.setStyleSheet(self.button_style)
                self.LeftZedDistance.clicked.connect(self.button_disableway)
                self.LeftZedDistance.setVisible(False)
                self.LeftZedDistance.clicked.connect(self.MicLeftZedYP)
                self.LeftZedDistance.setObjectName("Distance Button")
                self.LeftZedDistance.setCheckable(False)
                self.LeftZedDistance.setFont(QtGui.QFont("Arial", 8)) 


                self.MicLeftZedDOWN = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftZedDOWN.setGeometry(QtCore.QRect(800, 180, 101, 91))
                self.MicLeftZedDOWN.setStyleSheet("background:transparent")
                self.MicLeftZedDOWN.setText("")
                self.MicLeftZedDOWN.setObjectName("DownButton_2")
                self.MicLeftZedDOWN.setVisible(False)
                self.MicLeftZedDOWN.clicked.connect(self.MicLeftZedYN)
                self.MicLeftZedDOWN.setCheckable(True)
                self.MicLeftZedDOWN.clicked.connect(self.button_disableway)
                self.MicLeftZedDOWN.setFont(QtGui.QFont("Arial", 11))  
                self.MicLeftZedDOWN.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2.png")))
                self.MicLeftZedDOWN.setIconSize(QtCore.QSize(100, 100)) 




#Mic Right Zed Buttons

                self.MicRightZedUP = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightZedUP.setGeometry(QtCore.QRect(800, 10, 101, 91))
                self.MicRightZedUP.setStyleSheet("background:transparent")
                self.MicRightZedUP.setText("")
                self.MicRightZedUP.setObjectName("UpButton_2")
                self.MicRightZedUP.setVisible(False)
                self.MicRightZedUP.clicked.connect(self.MicRightZedYP)
                self.MicRightZedUP.setCheckable(True)
                self.MicRightZedUP.setFont(QtGui.QFont("Arial", 11))  
                self.MicRightZedUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2.png")))
                self.MicRightZedUP.setIconSize(QtCore.QSize(100, 100))
                self.MicRightZedUP.clicked.connect(self.button_disableway)

                #MicRightZedUp Possition Buttons
                self.RightZedPossition = QtWidgets.QPushButton(inner_inner_tab2)
                self.RightZedPossition.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.RightZedPossition.setStyleSheet(self.button_style)
                self.RightZedPossition.clicked.connect(self.button_disableway)
                self.RightZedPossition.setVisible(False)
                self.RightZedPossition.clicked.connect(self.MicRightZedYP)
                self.RightZedPossition.setObjectName("Possition Button")
                self.RightZedPossition.setCheckable(True)
                self.RightZedPossition.setFont(QtGui.QFont("Arial", 8))

                self.RightZedDistance = QtWidgets.QPushButton(inner_inner_tab2)
                self.RightZedDistance.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.RightZedDistance.setStyleSheet(self.button_style)
                self.RightZedDistance.clicked.connect(self.button_disableway)
                self.RightZedDistance.setVisible(False)
                self.RightZedDistance.clicked.connect(self.MicRightZedYP)
                self.RightZedDistance.setObjectName("Distance Button")
                self.RightZedDistance.setCheckable(True)
                self.RightZedDistance.setFont(QtGui.QFont("Arial", 8))



                self.MicRightZedDOWN = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightZedDOWN.setGeometry(QtCore.QRect(800, 180, 101, 91))
                self.MicRightZedDOWN.setStyleSheet("background:transparent")
                self.MicRightZedDOWN.setText("")
                self.MicRightZedDOWN.setObjectName("DownButton_2")
                self.MicRightZedDOWN.setVisible(False)
                self.MicRightZedDOWN.clicked.connect(self.MicRightZedYN)
                self.MicRightZedDOWN.setCheckable(True)
                self.MicRightZedDOWN.clicked.connect(self.button_disableway)
                self.MicRightZedDOWN.setFont(QtGui.QFont("Arial", 11))  
                self.MicRightZedDOWN.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2.png")))
                self.MicRightZedDOWN.setIconSize(QtCore.QSize(100, 100))



        
#Mic Left Buttons

                self.MicLeftUP = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftUP.setGeometry(QtCore.QRect(800, 10, 101, 91))
                self.MicLeftUP.setStyleSheet("background:transparent")
                self.MicLeftUP.setText("")
                self.MicLeftUP.setObjectName("UpButton_2")
                self.MicLeftUP.setVisible(False)
                self.MicLeftUP.clicked.connect(self.MicLeftYP)
                self.MicLeftUP.clicked.connect(self.button_disableway)
                self.MicLeftUP.setCheckable(True)
                self.MicLeftUP.setFont(QtGui.QFont("Arial", 11))  
                self.MicLeftUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2.png")))
                self.MicLeftUP.setIconSize(QtCore.QSize(100, 100))

                #MicLeft Possition Buttons
                self.MicLeftPossitionX = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftPossitionX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.MicLeftPossitionX.setStyleSheet(self.button_style)
                self.MicLeftPossitionX.clicked.connect(self.button_disableway)
                self.MicLeftPossitionX.setVisible(False)
                self.MicLeftPossitionX.clicked.connect(self.MicLeftPossX)
                self.MicLeftPossitionX.setObjectName("Possition Button")
                self.MicLeftPossitionX.setCheckable(False)
                self.MicLeftPossitionX.setFont(QtGui.QFont("Arial", 8))

                self.MicLeftPossitionY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftPossitionY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.MicLeftPossitionY.setStyleSheet(self.button_style)
                self.MicLeftPossitionY.clicked.connect(self.button_disableway)
                self.MicLeftPossitionY.setVisible(False)
                self.MicLeftPossitionY.clicked.connect(self.MicLeftPossY)
                self.MicLeftPossitionY.setObjectName("Distance Button")
                self.MicLeftPossitionY.setCheckable(False)
                self.MicLeftPossitionY.setFont(QtGui.QFont("Arial", 8))

                self.MicLeftPossitionMOVEXY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftPossitionMOVEXY.setGeometry(QtCore.QRect(800, 190, 100, 70))
                self.MicLeftPossitionMOVEXY.setStyleSheet(self.button_style)
                self.MicLeftPossitionMOVEXY.clicked.connect(self.button_disableway)
                self.MicLeftPossitionMOVEXY.setVisible(False)
                self.MicLeftPossitionMOVEXY.clicked.connect(self.MicLeftYP)
                self.MicLeftPossitionMOVEXY.setObjectName("Distance Button")
                self.MicLeftPossitionMOVEXY.setCheckable(False)
                self.MicLeftPossitionMOVEXY.setFont(QtGui.QFont("Arial", 8))

                #MicLeft Distance Buttons
                self.MicLeftDistanceX = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftDistanceX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.MicLeftDistanceX.setStyleSheet(self.button_style)
                self.MicLeftDistanceX.clicked.connect(self.button_disableway)
                self.MicLeftDistanceX.setVisible(False)
                self.MicLeftDistanceX.clicked.connect(self.MicLeftDissX)
                self.MicLeftDistanceX.setObjectName("Possition Button")
                self.MicLeftDistanceX.setCheckable(False)
                self.MicLeftDistanceX.setFont(QtGui.QFont("Arial", 8))

                self.MicLeftDistanceY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftDistanceY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.MicLeftDistanceY.setStyleSheet(self.button_style)
                self.MicLeftDistanceY.clicked.connect(self.button_disableway)
                self.MicLeftDistanceY.setVisible(False)
                self.MicLeftDistanceY.clicked.connect(self.MicLeftDissY)
                self.MicLeftDistanceY.setObjectName("Distance Button")
                self.MicLeftDistanceY.setCheckable(False)
                self.MicLeftDistanceY.setFont(QtGui.QFont("Arial", 8))

                self.MicLeftDistanceGOXY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftDistanceGOXY.setGeometry(QtCore.QRect(800, 190, 100, 70))
                self.MicLeftDistanceGOXY.setStyleSheet(self.button_style)
                self.MicLeftDistanceGOXY.clicked.connect(self.button_disableway)
                self.MicLeftDistanceGOXY.setVisible(False)
                self.MicLeftDistanceGOXY.clicked.connect(self.MicLeftYP)
                self.MicLeftDistanceGOXY.setObjectName("Distance Button")
                self.MicLeftDistanceGOXY.setCheckable(False)
                self.MicLeftDistanceGOXY.setFont(QtGui.QFont("Arial", 8))
                


                self.MicLeftDOWN = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftDOWN.setGeometry(QtCore.QRect(800, 180, 101, 91))
                self.MicLeftDOWN.setStyleSheet("background:transparent")
                self.MicLeftDOWN.setText("")
                self.MicLeftDOWN.setObjectName("DownButton_2")
                self.MicLeftDOWN.setVisible(False)
                self.MicLeftDOWN.clicked.connect(self.button_disableway)
                self.MicLeftDOWN.clicked.connect(self.MicLeftYN)
                self.MicLeftDOWN.setCheckable(True)
                self.MicLeftDOWN.setFont(QtGui.QFont("Arial", 20))  
                self.MicLeftDOWN.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2.png")))
                self.MicLeftDOWN.setIconSize(QtCore.QSize(100, 100))




                self.MicLeftRIGHT = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftRIGHT.setGeometry(QtCore.QRect(900, 90, 101, 91))
                self.MicLeftRIGHT.setStyleSheet("background:transparent")
                self.MicLeftRIGHT.setText("")
                self.MicLeftRIGHT.setObjectName("RightButton")
                self.MicLeftRIGHT.setVisible(False)
                self.MicLeftRIGHT.clicked.connect(self.button_disableway)
                self.MicLeftRIGHT.clicked.connect(self.MicLeftXP)
                self.MicLeftRIGHT.setCheckable(True)
                self.MicLeftRIGHT.setFont(QtGui.QFont("Arial", 20))  
                self.MicLeftRIGHT.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2.png")))
                self.MicLeftRIGHT.setIconSize(QtCore.QSize(100, 100))




                self.MicLeftLEFT = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicLeftLEFT.setGeometry(QtCore.QRect(700, 90, 101, 91))
                self.MicLeftLEFT.setStyleSheet("background: transparent")
                self.MicLeftLEFT.setText("")
                self.MicLeftLEFT.setObjectName("LeftButton")
                self.MicLeftLEFT.setVisible(False)
                self.MicLeftLEFT.clicked.connect(self.button_disableway)
                self.MicLeftLEFT.clicked.connect(self.MicLeftXN)
                self.MicLeftLEFT.setCheckable(True)
                self.MicLeftLEFT.setFont(QtGui.QFont("Arial", 20))  
                self.MicLeftLEFT.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2.png")))
                self.MicLeftLEFT.setIconSize(QtCore.QSize(100, 100))  

#Mic Right Buttons   

                self.MicRightUP = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightUP.setGeometry(QtCore.QRect(800, 10, 101, 91))
                self.MicRightUP.setStyleSheet("background:transparent")
                self.MicRightUP.setText("")
                self.MicRightUP.setObjectName("UpButton_2")
                self.MicRightUP.setVisible(False)
                self.MicRightUP.clicked.connect(self.button_disableway)
                self.MicRightUP.clicked.connect(self.MicRightYP)
                self.MicRightUP.setCheckable(True)
                self.MicRightUP.setFont(QtGui.QFont("Arial", 20))  
                self.MicRightUP.setIcon(QtGui.QIcon(manager.get_image_path("uparrow2.png")))
                self.MicRightUP.setIconSize(QtCore.QSize(100, 100))  

                #MicLeft Possition Buttons
                self.MicRightPossitionX = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightPossitionX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.MicRightPossitionX.setStyleSheet(self.button_style)
                self.MicRightPossitionX.clicked.connect(self.button_disableway)
                self.MicRightPossitionX.setVisible(False)
                self.MicRightPossitionX.clicked.connect(self.MicRightPossX)
                self.MicRightPossitionX.setObjectName("Possition Button")
                self.MicRightPossitionX.setCheckable(False)
                self.MicRightPossitionX.setFont(QtGui.QFont("Arial", 8))

                self.MicRightPossitionY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightPossitionY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.MicRightPossitionY.setStyleSheet(self.button_style)
                self.MicRightPossitionY.clicked.connect(self.button_disableway)
                self.MicRightPossitionY.setVisible(False)
                self.MicRightPossitionY.clicked.connect(self.MicRightPossY)
                self.MicRightPossitionY.setObjectName("Distance Button")
                self.MicRightPossitionY.setCheckable(False)
                self.MicRightPossitionY.setFont(QtGui.QFont("Arial", 8))

                self.MicRightPossitionMOVEXY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightPossitionMOVEXY.setGeometry(QtCore.QRect(800, 190, 100, 70))
                self.MicRightPossitionMOVEXY.setStyleSheet(self.button_style)
                self.MicRightPossitionMOVEXY.clicked.connect(self.button_disableway)
                self.MicRightPossitionMOVEXY.setVisible(False)
                self.MicRightPossitionMOVEXY.clicked.connect(self.MicRightYP)
                self.MicRightPossitionMOVEXY.setObjectName("Distance Button")
                self.MicRightPossitionMOVEXY.setCheckable(False)
                self.MicRightPossitionMOVEXY.setFont(QtGui.QFont("Arial",8))

                #MicLeft Distance Buttons
                self.MicRightDistanceX = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightDistanceX.setGeometry(QtCore.QRect(900, 70, 100, 70))
                self.MicRightDistanceX.setStyleSheet(self.button_style)
                self.MicRightDistanceX.clicked.connect(self.button_disableway)
                self.MicRightDistanceX.setVisible(False)
                self.MicRightDistanceX.clicked.connect(self.MicRightDissX)
                self.MicRightDistanceX.setObjectName("Distance Button")
                self.MicRightDistanceX.setCheckable(False)
                self.MicRightDistanceX.setFont(QtGui.QFont("Arial", 8))

                self.MicRightDistanceY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightDistanceY.setGeometry(QtCore.QRect(700, 70, 100, 70))
                self.MicRightDistanceY.setStyleSheet(self.button_style)
                self.MicRightDistanceY.clicked.connect(self.button_disableway)
                self.MicRightDistanceY.setVisible(False)
                self.MicRightDistanceY.clicked.connect(self.MicRightDissY)
                self.MicRightDistanceY.setObjectName("Distance Button")
                self.MicRightDistanceY.setCheckable(False)
                self.MicRightDistanceY.setFont(QtGui.QFont("Arial", 8))

                self.MicRightDistanceGOXY = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightDistanceGOXY.setGeometry(QtCore.QRect(800, 190, 100, 70))
                self.MicRightDistanceGOXY.setStyleSheet(self.button_style)
                self.MicRightDistanceGOXY.clicked.connect(self.button_disableway)
                self.MicRightDistanceGOXY.setVisible(False)
                self.MicRightDistanceGOXY.clicked.connect(self.MicRightYP)
                self.MicRightDistanceGOXY.setObjectName("Distance Button")
                self.MicRightDistanceGOXY.setCheckable(False)
                self.MicRightDistanceGOXY.setFont(QtGui.QFont("Arial", 8))


                self.MicRightDOWN = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightDOWN.setGeometry(QtCore.QRect(800, 180, 101, 91))
                self.MicRightDOWN.setStyleSheet("background:transparent")
                self.MicRightDOWN.setText("")
                self.MicRightDOWN.setObjectName("DownButton_2")
                self.MicRightDOWN.setVisible(False)
                self.MicRightDOWN.clicked.connect(self.button_disableway)
                self.MicRightDOWN.clicked.connect(self.MicRightYN)
                self.MicRightDOWN.setCheckable(True)
                self.MicRightDOWN.setFont(QtGui.QFont("Arial", 20))  
                self.MicRightDOWN.setIcon(QtGui.QIcon(manager.get_image_path("downarrow2.png")))
                self.MicRightDOWN.setIconSize(QtCore.QSize(100, 100))  




                self.MicRightRIGHT = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightRIGHT.setGeometry(QtCore.QRect(900, 90, 101, 91))
                self.MicRightRIGHT.setStyleSheet("background:transparent")
                self.MicRightRIGHT.setText("")
                self.MicRightRIGHT.setObjectName("RightButton")
                self.MicRightRIGHT.setVisible(False)
                self.MicRightRIGHT.clicked.connect(self.button_disableway)
                self.MicRightRIGHT.clicked.connect(self.MicRightXP)
                self.MicRightRIGHT.setCheckable(True)
                self.MicRightRIGHT.setFont(QtGui.QFont("Arial", 20))  
                self.MicRightRIGHT.setIcon(QtGui.QIcon(manager.get_image_path("rightarrow2.png")))
                self.MicRightRIGHT.setIconSize(QtCore.QSize(100, 100))  




                self.MicRightLEFT = QtWidgets.QPushButton(inner_inner_tab2)
                self.MicRightLEFT.setGeometry(QtCore.QRect(700, 90, 101, 91))
                self.MicRightLEFT.setStyleSheet("background:transparent")
                self.MicRightLEFT.setText("")
                self.MicRightLEFT.setObjectName("LeftButton")
                self.MicRightLEFT.setVisible(False)
                self.MicRightLEFT.clicked.connect(self.button_disableway)
                self.MicRightLEFT.clicked.connect(self.MicroSXN)
                self.MicRightLEFT.setCheckable(True)
                self.MicRightLEFT.setFont(QtGui.QFont("Arial", 20))  
                self.MicRightLEFT.setIcon(QtGui.QIcon(manager.get_image_path("leftarrow2.png")))
                self.MicRightLEFT.setIconSize(QtCore.QSize(100, 100))  










                self.line_7 = QtWidgets.QFrame(inner_inner_tab2)
                self.line_7.setGeometry(QtCore.QRect(30, 300, 951, 21))
                self.line_7.setStyleSheet("background: transparent")
                self.line_7.setFrameShadow(QtWidgets.QFrame.Plain)
                self.line_7.setLineWidth(2)
                self.line_7.setFrameShape(QtWidgets.QFrame.HLine)
                self.line_7.setObjectName("line_7")

                self.GapDoc_2 = QtWidgets.QWidget(inner_inner_tab2)
                self.GapDoc_2.setToolTip('Microscope Left Zed Datas')
                self.GapDoc_2.setGeometry(QtCore.QRect(60, 110, 131, 31))
                self.GapDoc_2.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_2.setObjectName("MLZ")
                self.GapDoc_layout2 = QtWidgets.QVBoxLayout(self.GapDoc_2)
                self.GapDoc_layout2.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout2.setObjectName("2")
                self.GapDoc_layout2.addWidget (self.bufferMLZ)
                


                self.GapDoc_3 = QtWidgets.QLineEdit(inner_inner_tab2)
                self.GapDoc_3.setToolTip('Microscope Left X Possition Datas')
                self.GapDoc_3.setGeometry(QtCore.QRect(220, 110, 131, 31))
                self.GapDoc_3.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_3.setObjectName("ML")
                self.GapDoc_layout3 = QtWidgets.QGridLayout(self.GapDoc_3)
                self.GapDoc_layout3.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout3.setObjectName("3")
                self.GapDoc_layout3.addWidget(self.bufferMLeft)

                self.GapDoc_3 = QtWidgets.QLineEdit(inner_inner_tab2)
                self.GapDoc_3.setToolTip('Microscope Left Y Possition Datas')
                self.GapDoc_3.setGeometry(QtCore.QRect(220, 150, 131, 31))
                self.GapDoc_3.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_3.setObjectName("ML")
                self.GapDoc_layout3 = QtWidgets.QGridLayout(self.GapDoc_3)
                self.GapDoc_layout3.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout3.setObjectName("3")
                self.GapDoc_layout3.addWidget(self.bufferMLeftY)

                


                self.GapDoc_6 = QtWidgets.QLineEdit(inner_inner_tab2)
                self.GapDoc_6.setToolTip('Microscope Right X Possition Datas')
                self.GapDoc_6.setGeometry(QtCore.QRect(380, 110, 131, 31))
                self.GapDoc_6.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_6.setObjectName("MR")
                self.GapDoc_layout6 = QtWidgets.QGridLayout(self.GapDoc_6)
                self.GapDoc_layout6.setObjectName("6")
                self.GapDoc_layout6.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout6.addWidget(self.bufferMRight)

                self.GapDoc_6 = QtWidgets.QLineEdit(inner_inner_tab2)
                self.GapDoc_6.setToolTip('Microscope Right Y Possition Datas')
                self.GapDoc_6.setGeometry(QtCore.QRect(380, 150, 131, 31))
                self.GapDoc_6.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_6.setObjectName("MRY")
                self.GapDoc_layout6 = QtWidgets.QGridLayout(self.GapDoc_6)
                self.GapDoc_layout6.setObjectName("6")
                self.GapDoc_layout6.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout6.addWidget(self.bufferMRightY)


                self.GapDoc_7 = QtWidgets.QLineEdit(inner_inner_tab2)
                self.GapDoc_7.setToolTip('Microscope Right Zed Possition Datas')
                self.GapDoc_7.setGeometry(QtCore.QRect(60, 235, 131, 31))
                self.GapDoc_7.setStyleSheet("border : 1px solid black; border-radius :5px;")
                self.GapDoc_7.setObjectName("MRZ")
                self.GapDoc_layout7 = QtWidgets.QGridLayout(self.GapDoc_7)
                self.GapDoc_layout7.setObjectName("7")
                self.GapDoc_layout7.setContentsMargins(0, 0, 0, 0)
                self.GapDoc_layout7.addWidget(self.bufferMRZ)


                self.verticalLayoutWidget_3 = QtWidgets.QWidget(inner_inner_tab2)
                self.verticalLayoutWidget_3.setToolTip('Set Speed Value')
                self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(220, 175, 300, 100))
                self.verticalLayoutWidget_3.setStyleSheet("background-color: transparent; color: #Black")  
                self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
                self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)

                self.progress_bar_3 = QtWidgets.QProgressBar(self.verticalLayoutWidget_3)
                self.progress_bar_3.setStyleSheet("QProgressBar { color: black; }")
                self.progress_bar_3.setInvertedAppearance(True)
                self.slider_3 = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.verticalLayoutWidget_3)
                self.slider_3.setStyleSheet("background-color : #f5f5f5;")  
                self.slider_3.setRange(0, 100)
                self.slider_3.valueChanged.connect(self.update_progress_bar)
                self.slider_3.valueChanged.connect(self.update_motor_speed3)

                self.verticalLayout_3.addWidget(self.progress_bar_3)
                self.verticalLayout_3.addWidget(self.slider_3)

                # üçüncü iç içe sekme
                inner_inner_tab3 = QtWidgets.QWidget()
                inner_inner_tab_widget.addTab(inner_inner_tab3, "Align Process")

                self.verticalLayoutWidgetAligncheck = QtWidgets.QWidget(inner_inner_tab3)
                self.verticalLayoutWidgetAligncheck.setGeometry(QtCore.QRect(130,190,50,50))
                self.verticalLayoutWidgetAligncheck.setObjectName("verticalLayoutWidgetAligncheck")
                self.verticalLayoutWidgetAligncheck.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #õlabels
                self.verticalLayoutAlligncheck = QtWidgets.QVBoxLayout(self.verticalLayoutWidgetAligncheck)
                self.verticalLayoutAlligncheck.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutAlligncheck.setObjectName("verticalLayoutAlligncheck")
                self.image_Aligncheck = QtWidgets.QLabel(self.verticalLayoutWidgetAligncheck)
                self.image_Aligncheck.setObjectName("image_Aligncheck")
                self.image_Aligncheck.setStyleSheet("background: transparent")
                self.image_Aligncheck.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_Aligncheck.setVisible(True)
                self.image_Aligncheck.setScaledContents(True)
                self.verticalLayoutAlligncheck.addWidget(self.image_Aligncheck)

                self.verticalLayoutWidgetAutoAlignment = QtWidgets.QWidget(inner_inner_tab3)
                self.verticalLayoutWidgetAutoAlignment.setGeometry(QtCore.QRect(350,190,50,50))
                self.verticalLayoutWidgetAutoAlignment.setObjectName("verticalLayoutWidgetAutoAlignment")
                self.verticalLayoutWidgetAutoAlignment.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #õlabels
                self.verticalLayoutAutoaligment = QtWidgets.QVBoxLayout(self.verticalLayoutWidgetAutoAlignment)
                self.verticalLayoutAutoaligment.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutAutoaligment.setObjectName("verticalLayoutAutoaligment")
                self.image_AutoAllingment = QtWidgets.QLabel(self.verticalLayoutWidgetAutoAlignment)
                self.image_AutoAllingment.setObjectName("image_AutoAllingment")
                self.image_AutoAllingment.setStyleSheet("background: transparent")
                self.image_AutoAllingment.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_AutoAllingment.setVisible(True)
                self.image_AutoAllingment.setScaledContents(True)
                self.verticalLayoutAutoaligment.addWidget(self.image_AutoAllingment)

                self.verticalLayoutWidgetAutoFocus = QtWidgets.QWidget(inner_inner_tab3)
                self.verticalLayoutWidgetAutoFocus.setGeometry(QtCore.QRect(570,190,50,50))
                self.verticalLayoutWidgetAutoFocus.setObjectName("verticalLayoutWidgetAutoFocus")
                self.verticalLayoutWidgetAutoFocus.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #õlabels
                self.verticalLayout_AutoFocus = QtWidgets.QVBoxLayout(self.verticalLayoutWidgetAutoFocus)
                self.verticalLayout_AutoFocus.setContentsMargins(0, 0, 0, 0)
                self.verticalLayout_AutoFocus.setObjectName("verticalLayout_AutoFocus")
                self.image_AutoFocus = QtWidgets.QLabel(self.verticalLayoutWidgetAutoFocus)
                self.image_AutoFocus.setObjectName("image_AutoFocus")
                self.image_AutoFocus.setStyleSheet("background: transparent")
                self.image_AutoFocus.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_AutoFocus.setVisible(True)
                self.image_AutoFocus.setScaledContents(True)
                self.verticalLayout_AutoFocus.addWidget(self.image_AutoFocus)

                self.verticalLayoutWidget_StartExposure = QtWidgets.QWidget(inner_inner_tab3)
                self.verticalLayoutWidget_StartExposure.setGeometry(QtCore.QRect(780,190,50,50))
                self.verticalLayoutWidget_StartExposure.setObjectName("verticalLayoutWidget_StartExposure")
                self.verticalLayoutWidget_StartExposure.setStyleSheet("background-color: transparent; color: black; border: 1px solid black;")                                   #õlabels
                self.verticalLayoutStartExposure = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_StartExposure)
                self.verticalLayoutStartExposure.setContentsMargins(0, 0, 0, 0)
                self.verticalLayoutStartExposure.setObjectName("verticalLayoutStartExposure")
                self.image_StartExposure = QtWidgets.QLabel(self.verticalLayoutWidget_StartExposure)
                self.image_StartExposure.setObjectName("image_StartExposure")
                self.image_StartExposure.setStyleSheet("background: transparent")
                self.image_StartExposure.setPixmap(QtGui.QPixmap(manager.get_image_path("red.png")))
                self.image_StartExposure.setVisible(True)
                self.image_StartExposure.setScaledContents(True)
                self.verticalLayoutStartExposure.addWidget(self.image_StartExposure)

                self.StartExposure = QtWidgets.QPushButton(inner_inner_tab3)
                self.StartExposure.setToolTip('Start Exposure Button')
                self.StartExposure.setGeometry(QtCore.QRect(730, 90, 161, 81))
                self.StartExposure.setObjectName("StartExposure")
                self.StartExposure.setCheckable(True)
                self.StartExposure.setStyleSheet(self.button_style)
                self.StartExposure.clicked.connect(self.SendStartExposure)
                self.StartExposureStatus = QtWidgets.QLabel(inner_inner_tab3)
                self.StartExposureStatus.setGeometry(QtCore.QRect(730, 240, 181, 21))
                self.StartExposureStatus.setFont(font)
                self.StartExposureStatus.setStyleSheet("background: transparent")
                self.StartExposureStatus.setObjectName("StartExposureStatus")
                self.StartExposure.clicked.connect(self.AlignControl4)


                self.AlignCheck = QtWidgets.QPushButton(inner_inner_tab3)
                self.AlignCheck.setToolTip('Align Check Button')
                self.AlignCheck.setGeometry(QtCore.QRect(80, 90, 161, 81))
                self.AlignCheck.setObjectName("AlignCheck")
                self.AlignCheck.setCheckable(True)
                self.AlignCheck.setStyleSheet(self.button_style)
                self.AlignCheck.clicked.connect(self.SendAlignCheck)
                self.AlignCheckStatus = QtWidgets.QLabel(inner_inner_tab3)
                self.AlignCheckStatus.setGeometry(QtCore.QRect(80, 240, 181, 21))
                self.AlignCheckStatus.setFont(font)
                self.AlignCheckStatus.setStyleSheet("background: transparent")
                self.AlignCheckStatus.setObjectName("AlignCheckStatus")
                #self.AlignCheck.clicked.connect(self.AlignControl)
                
                self.line_10 = QtWidgets.QFrame(inner_inner_tab3)
                self.line_10.setGeometry(QtCore.QRect(80, 170, 821, 21))
                self.line_10.setStyleSheet("background: transparent")
                self.line_10.setFrameShadow(QtWidgets.QFrame.Plain)
                self.line_10.setLineWidth(2)
                self.line_10.setFrameShape(QtWidgets.QFrame.HLine)
                self.line_10.setObjectName("line_10")


                self.AutoFocus = QtWidgets.QPushButton(inner_inner_tab3)
                self.AutoFocus.setToolTip('İşlevsiz')
                self.AutoFocus.setGeometry(QtCore.QRect(520, 90, 161, 81))
                self.AutoFocus.setObjectName("AutoFocus")
                self.AutoFocus.setCheckable(True)
                self.AutoFocus.setStyleSheet(self.button_style)
                self.AutoFocus.clicked.connect(self.SendAutoFocus)
                self.AutoFocusStatus = QtWidgets.QLabel(inner_inner_tab3)
                self.AutoFocusStatus.setGeometry(QtCore.QRect(520, 240, 181, 21))
                self.AutoFocusStatus.setFont(font)
                self.AutoFocusStatus.setStyleSheet("background: transparent")
                self.AutoFocusStatus.setObjectName("AutoFocusStatus")
                self.AutoFocus.clicked.connect(self.AlignControl3)


                self.AutoAlignment = QtWidgets.QPushButton(inner_inner_tab3)
                self.AutoAlignment.setToolTip('Image processing functions in the camera On/Off ')
                self.AutoAlignment.setGeometry(QtCore.QRect(300, 90, 161, 81))
                self.AutoAlignment.setObjectName("AutoAlignment")
                self.AutoAlignment.setCheckable(True)
                self.AutoAlignment.setStyleSheet(self.button_style)
                self.AutoAlignment.clicked.connect(self.SendAutoAlignment)
                self.AutoAlignmentStatus = QtWidgets.QLabel(inner_inner_tab3)
                self.AutoAlignmentStatus.setGeometry(QtCore.QRect(300, 240, 181, 21))
                self.AutoAlignmentStatus.setFont(font)
                self.AutoAlignmentStatus.setStyleSheet("background: transparent")
                self.AutoAlignmentStatus.setObjectName("AutoAlignmentStatus")
                self.AutoAlignment.clicked.connect(self.AlignControl2)



                self.Align = QtWidgets.QLabel(inner_inner_tab3)
                self.Align.setGeometry(QtCore.QRect(480, 30, 41, 31))
                font = QtGui.QFont()
                font.setPointSize(10)
                self.Align.setFont(font)
                self.Align.setStyleSheet("background: transparent")
                self.Align.setObjectName("Align")
                self.tabWidget.addTab(self.tab_Align, "")



                self.verticalLayoutWidget_18 = QtWidgets.QWidget(self.centralwidget)
                self.verticalLayoutWidget_18.setToolTip('Incoming raw datas')
                self.verticalLayoutWidget_18.setGeometry(QtCore.QRect(1510, 830, 401, 141))
                self.verticalLayoutWidget_18.setObjectName("verticalLayoutWidget_18")
                self.verticalLayoutWidget_18.setVisible(True)
                self.verticalLayoutWidget_18.setStyleSheet("background-color: transparent;  border: 1px solid black; border-radius : 5px;")  
                self.verticalLayout_18 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_18)
                self.mainLogBox = QtWidgets.QTextEdit(self.verticalLayoutWidget_18)
                self.mainLogBox.setObjectName("mainLogBox")
                self.mainLogBox.setReadOnly(True)
                self.mainLogBox.setStyleSheet("background-color: #1a1a2e; color: #ddd; font-family: Consolas; font-size: 11px;")
                self.verticalLayout_18.addWidget(self.mainLogBox)
                self.verticalLayout_18.addWidget(self.bufferTxt)


                self.StartProcess = QtWidgets.QPushButton(self.centralwidget)
                self.StartProcess.setToolTip('Start Process Button')
                self.StartProcess.setGeometry(QtCore.QRect(1510, 750, 131, 51))
                self.StartProcess.setObjectName("StartProcess")
                self.StartProcess.setStyleSheet(self.button_style)
                self.StartProcess.clicked.connect(self.StartProcessButton)
                self.StartProcess.setCheckable(True)
                self.StartProcess.setEnabled(True)
                self.line = QtWidgets.QFrame(self.centralwidget)
                self.line.setGeometry(QtCore.QRect(950, 0, 20, 661))
                self.line.setFrameShape(QtWidgets.QFrame.VLine)
                self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
                self.line.setObjectName("line")


                self.EmergencyStop = QtWidgets.QPushButton(self.centralwidget)
                self.EmergencyStop.setToolTip('EmergencyStop')
                self.EmergencyStop.setGeometry(QtCore.QRect(1050, 900, 131, 51))
                self.EmergencyStop.setObjectName("EmergencyStop")
                self.EmergencyStop.setStyleSheet(self.button_style)
                self.EmergencyStop.clicked.connect(self.EmergencyStoped)
                


                self.Camera1 = QtWidgets.QLabel(self.centralwidget)
                self.Camera1.setToolTip("Camera 1")
                self.Camera1.setToolTipDuration(2000)
                self.Camera1.setGeometry(QtCore.QRect(10, 0, 951, 661))
                self.Camera1.setStyleSheet("background-color: #111; color: #555; font-size: 28px; border: 1px solid #333; border-radius: 6px;")
                self.Camera1.setAlignment(Qt.AlignCenter)
                self.Camera1.setObjectName("Camera1")
                self.Camera1.setVisible(True)
                self.Camera1.mousePressEvent = self.mouse_callback





                self.Camera2 = QtWidgets.QLabel(self.centralwidget)
                self.Camera2.setGeometry(QtCore.QRect(960, 0, 951, 661))
                self.Camera2.setStyleSheet("background-color: #111; color: #555; font-size: 28px; border: 1px solid #333; border-radius: 6px;")
                self.Camera2.setAlignment(Qt.AlignCenter)
                self.Camera2.setObjectName("Camera2")
                self.Camera2.setVisible(True)
                self.Camera2.mousePressEvent= self.mouse_callback

              



                ProcessScreen.setCentralWidget(self.centralwidget)
                self.menubar = QtWidgets.QMenuBar(ProcessScreen)
                self.menubar.setGeometry(QtCore.QRect(0, 0, 1920, 26))
                self.menubar.setObjectName("menubar")
                ProcessScreen.setMenuBar(self.menubar)
                self.statusbar = QtWidgets.QStatusBar(ProcessScreen)
                self.statusbar.setObjectName("statusbar")
                ProcessScreen.setStatusBar(self.statusbar)

                self.retranslateUi(ProcessScreen)
                self.tabWidget.setCurrentIndex(2)
                QtCore.QMetaObject.connectSlotsByName(ProcessScreen)


                serial_mgr.data_received.connect(self._process_binary_command)

                self.comboBox = QtWidgets.QComboBox(self.centralwidget)
                self.comboBox.setToolTip('Available Ports')
                self.comboBox.setGeometry(QtCore.QRect(1800, 740, 70, 20))
                self.comboBox.setObjectName("comboBox")
                self.comboBox.setStyleSheet("background-color: transparent; color:  border: 1px solid black; border-radius : 5px; ")
                self.listSerialPorts()

                #port Butonu
                self.port_button = QPushButton(self.centralwidget)
                self.port_button.setToolTip('Open Port')
                self.port_button.setGeometry(QtCore.QRect(1800,770,70,30))
                self.port_button.setText("Port Open")
                self.port_button.setFont(QtGui.QFont("Times New Roman", 8))
                self.port_button.clicked.connect(self.portConnectfn)
                self.port_button.setStyleSheet("background-color: transparent;  border : 1px solid black; border-radius :1px;")

                #Control Buttonları Veri Akışı

                self.Logolabel = QtWidgets.QLabel(self.centralwidget)
                self.Logolabel.setGeometry(QtCore.QRect(1150, 835, 340, 180))
                self.Logolabel.setPixmap(QtGui.QPixmap(manager.get_image_path("Main_Logo.png")))
                self.Logolabel.setVisible(False)
                self.Logolabel.setScaledContents(True)
                self.Logolabel.setStyleSheet("background: transparent")


                self.verticalLayoutWidget_Light = QtWidgets.QWidget(self.centralwidget)
                self.verticalLayoutWidget_Light.setToolTip('Set Light Value')
                self.verticalLayoutWidget_Light.setGeometry(QtCore.QRect(1050, 780, 300, 100))
                self.verticalLayoutWidget_Light.setStyleSheet("background: transparent;")  
                self.verticalLayout_Light = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_Light)
                self.verticalLayout_Light.setContentsMargins(0, 0, 0, 0)

                self.progress_bar_Light = QtWidgets.QProgressBar(self.verticalLayoutWidget_Light)
                self.progress_bar_Light.setStyleSheet("QProgressBar { color: black; }")
                self.slider_Light = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.verticalLayoutWidget_Light)
                self.slider_Light.setStyleSheet("background-color : #f5f5f5;")  
                self.slider_Light.setRange(0, 100)
                self.slider_Light.setVisible(True)
                self.progress_bar_Light.setInvertedAppearance(True)
                self.slider_Light.valueChanged.connect(self.update_progress_bar)
                self.slider_Light.valueChanged.connect(self.update_Light_degree)

                self.verticalLayout_Light.addWidget(self.progress_bar_Light)
                self.verticalLayout_Light.addWidget(self.slider_Light)

                #Zed Speed
                self.verticalLayoutWidget_ZedSpeed = QtWidgets.QWidget(inner_inner_tab2)
                self.verticalLayoutWidget_ZedSpeed.setToolTip('Set Zed Speed Value')
                self.verticalLayoutWidget_ZedSpeed.setGeometry(QtCore.QRect(0, 10, 50, 250))
                self.verticalLayoutWidget_ZedSpeed.setStyleSheet("background: transparent;")  
                self.verticalLayout_ZedSpeed = QtWidgets.QHBoxLayout(self.verticalLayoutWidget_ZedSpeed)
                self.verticalLayout_ZedSpeed.setContentsMargins(0, 0, 0, 0)

                self.progress_bar_ZedSpeed = QtWidgets.QProgressBar(self.verticalLayoutWidget_ZedSpeed)
                self.progress_bar_ZedSpeed.setStyleSheet("QProgressBar { color: black; }")
                self.progress_bar_ZedSpeed.setOrientation(QtCore.Qt.Vertical)
                self.progress_bar_ZedSpeed.setInvertedAppearance(True)
                self.slider_ZedSpeed = QtWidgets.QSlider(QtCore.Qt.Vertical, self.verticalLayoutWidget_ZedSpeed)
                self.slider_ZedSpeed.setStyleSheet("background-color : #f5f5f5;")  
                self.slider_ZedSpeed.setRange(0, 100)
                self.slider_ZedSpeed.valueChanged.connect(self.update_progress_bar)
                self.slider_ZedSpeed.valueChanged.connect(self.update_Zed_Speed)

                self.verticalLayout_ZedSpeed.addWidget(self.progress_bar_ZedSpeed)
                self.verticalLayout_ZedSpeed.addWidget(self.slider_ZedSpeed)


        
                
        


        





        def retranslateUi(self, ProcessScreen):
                _translate = QtCore.QCoreApplication.translate
                ProcessScreen.setWindowTitle(_translate("ProcessScreen", "ProcessScreen"))
                self.ContactMode.setText(_translate("ProcessScreen", "Contact Mode"))
                self.Proxymity.setText(_translate("ProcessScreen", "Proxymity"))
                self.VacuumContact.setText(_translate("ProcessScreen", "Vacuum Contact"))
                self.SoftContact.setText(_translate("ProcessScreen", "Soft Contact"))
                self.HardContact.setText(_translate("ProcessScreen", "Hard Contact"))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("ProcessScreen", "Contact Mode"))
                self.UpButton.setText(_translate("ProcessScreen", ""))
                self.DownButton.setText(_translate("ProcessScreen", ""))
                self.um.setText(_translate("ProcessScreen", "um"))
                self.mWcm.setText(_translate("ProcessScreen", "mW/cm^2"))
                self.Gap.setText(_translate("ProcessScreen", "Gap"))
                self.ExposureDose.setText(_translate("ProcessScreen", "Exposure Dose"))
                self.GapButton.setText(_translate("ProcessScreen", "Set Gap"))
                self.ExposureButton.setText(_translate("ProcessScreen", "Set Exposure Dose"))
                # self.MicroSpeed.setText(_translate("ProcessScreen", "Microscope Speed"))
                # self.SampleSpeed.setText(_translate("ProcessScreen", "Sample Speed"))
                self.textBrowser_2.setHtml(_translate("ProcessScreen", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
        "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
        "<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">exposure dose girilmedi ise hata verdir</p></body></html>"))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("ProcessScreen", "Settings"))
                self.Theta.setText(_translate("ProcessScreen", "Theta"))
                self.SampleXY.setText(_translate("ProcessScreen", "Saple X/Y"))
                self.MicRight.setText(_translate("ProcessScreen", "Mic Right"))
                self.MicLeft.setText(_translate("ProcessScreen", "Mic Left"))
                self.MicRightZed.setText(_translate("ProcessScreen", "Mic Right Zed"))
                self.MicLeftZed.setText(_translate("ProcessScreen", "Mic Left Zed"))
                self.MaskLoad.setText(_translate("ProcessScreen", "Mask Load"))
                self.SampleVacuumStatus.setText(_translate("ProcessScreen", "Sample Vacuum Status"))  
                self.VacuumContactStatus.setText(_translate("ProcessScreen", "Vacuum Contact Status  "))
                self.ProxymityStatus.setText(_translate("ProcessScreen", "Proxymity Status  "))
                self.HardContactStatus.setText(_translate("ProcessScreen", "Hard Contact Status  "))
                self.SoftContactStatus.setText(_translate("ProcessScreen", "Soft Contact Status  "))
                # self.MaskHolderLock.setText(_translate("ProcessScreen", "Mask Holder Lock"))
                self.MaskVacuumStatus.setText(_translate("ProcessScreen", "Mask Vacuum Status"))
                self.MaskVacuum.setText(_translate("ProcessScreen", "Mask Vacuum"))
                self.SampleVacuum.setText(_translate("ProcessScreen", "Sample Vacuum"))
                #self.MaskHolderVacuumStatus.setText(_translate("ProcessScreen", "Mask Holder Vacuum Status"))
                self.MaskLoad_2.setText(_translate("ProcessScreen", "Maske Load/Unload"))
                self.SampleHolderLoad.setText(_translate("ProcessScreen", "Sample Holder Load/Unload"))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _translate("ProcessScreen", "Vacuum Control"))
                self.StartExposure.setText(_translate("ProcessScreen", "Start Exposure"))
                self.AlignCheck.setText(_translate("ProcessScreen", "Aling Check"))
                self.AutoFocus.setText(_translate("ProcessScreen", "Auto Focus"))
                self.AutoAlignment.setText(_translate("ProcessScreen", "Auto Alignment"))
                self.Align.setText(_translate("ProcessScreen", "Align"))
                self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Align), _translate("ProcessScreen", "Align"))
                self.StartProcess.setText(_translate("ProcessScreen", "Start Process"))
                self.EmergencyStop.setText(_translate("ProcessScreen", "Emergency STOP"))
                self.Camera1.setText(_translate("ProcessScreen", ""))
                self.Camera2.setText("CAM 2 (Offline)")
                self.AutoAlignmentStatus.setText(_translate("ProcessScreen", "Auto Alignment Status  "))
                self.AlignCheckStatus.setText(_translate("ProcessScreen", "Align Check Status  "))
                self.AutoFocusStatus.setText(_translate("ProcessScreen", "Auto Focus Status  "))
                self.StartExposureStatus.setText(_translate("ProcessScreen", "Exposure Status  "))
                self.ThetaDistanceX.setText(_translate("ProcessScreen", " X Distance  "))
                self.ThetaDistanceY.setText(_translate("ProcessScreen", " Y Distance  "))
                self.ThetaPossitionX.setText(_translate("ProcessScreen", " X Possition  "))
                self.ThetaPossitionY.setText(_translate("ProcessScreen", " Y Possition  "))
                self.SampleDistanceX.setText(_translate("ProcessScreen", " X Distance  "))
                self.SampleDistanceY.setText(_translate("ProcessScreen", " Y Distance  "))
                self.SampleDistanceGOXY.setText(_translate("ProcessScreen", " GOXY   "))
                self.SamplePossitionX.setText(_translate("ProcessScreen", " X Possition  "))
                self.SamplePossitionY.setText(_translate("ProcessScreen", " Y Possition  "))
                self.SamplePossitionMOVEXY.setText(_translate("ProcessScreen", " MOVEXY   "))
                self.MicLeftDistanceX.setText(_translate("ProcessScreen", " X Distance  "))
                self.MicLeftDistanceY.setText(_translate("ProcessScreen", " Y Distance  "))
                self.MicLeftDistanceGOXY.setText(_translate("ProcessScreen", " GOXY   "))
                self.MicLeftPossitionX.setText(_translate("ProcessScreen", " X Possition  "))
                self.MicLeftPossitionY.setText(_translate("ProcessScreen", " Y Possition  "))
                self.MicLeftPossitionMOVEXY.setText(_translate("ProcessScreen", " MOVEXY   "))
                
                self.MicRightDistanceX.setText(_translate("ProcessScreen", " X Distance  "))
                self.MicRightDistanceY.setText(_translate("ProcessScreen", " Y Distance  "))
                self.MicRightDistanceGOXY.setText(_translate("ProcessScreen", " GOXY   "))
                self.MicRightPossitionX.setText(_translate("ProcessScreen", " X Possition  "))
                self.MicRightPossitionY.setText(_translate("ProcessScreen", " Y Possition  "))
                self.MicRightPossitionMOVEXY.setText(_translate("ProcessScreen", " MOVEXY   "))

                self.image_proxymity.setText((""))#Proxymity
                self.image_SoftContact.setText((""))#SoftContact
                self.image_HardContact.setText((""))#HardContact
                self.image_VacuumContact.setText((""))#VacuumContact
                self.image_MaskLU.setText((""))#Proxymity
                self.image_SampleHolderLoad.setText((""))#SoftContact
                self.image_MaskHolderVacuum.setText((""))#HardContact
                self.image_MaskVacuum.setText((""))#VacuumContact
                self.image_SampleVacuum.setText((""))#Proxymity
                self.image_Aligncheck.setText((""))#SoftContact
                self.image_AutoAllingment.setText((""))#HardContact
                self.image_AutoFocus.setText((""))#VacuumContact
                self.image_StartExposure.setText((""))#VacuumContact

        def open_camera(self):
                pass

        def _open_main_menu(self):
                """NavBar BACK → MainMenu'ye dön."""
                from MainMenu import Ui_MainWindow
                from PyQt5.QtWidgets import QMainWindow
                self._mm_win = QMainWindow()
                self._mm_ui = Ui_MainWindow()
                self._mm_ui.MainscreenUi(self._mm_win)
                manager.switch_window(self._mm_win)

        def setButtonChecked(self):
                self.SoftContact.clicked.connect(self.SendSoftContact)
                self.SoftContact.setChecked(True)
                cmd_mgr.set_contact_mode(1)
                self.SoftContact.setStyleSheet(self._active_style)
        



        def start_camera(self):
                self.camera.start()
                self.camera.frame_update.connect(self.update_frame)

        def start_camera2(self):
                self.camera2.start()
                self.camera2.frame_update.connect(self.update_frame2)

        def Startloop(self):
                self.camera.startloop()

        def Startloop(self):
                self.camera2.startloop()

        def stop_camera(self):
                self.camera.stop()

        def stop_camera2(self):
                self.camera2.stop()

        def update_frame(self, Camera1):
                q_image = QPixmap.fromImage(Camera1)
                self.Camera1.setPixmap(q_image)

        def update_frame2(self, Camera2):
                q_image2 = QPixmap.fromImage(Camera2)
                self.Camera2.setPixmap(q_image2)

        def incrementValue(self):
                self.currentValue += 1
                self.updateLabel()

        def decrementValue(self):
                if self.currentValue > 1:  # Minimum değer kontrolü
                        self.currentValue -= 1
                        self.updateLabel()
        


        def updateLabel(self):
                self.label.setText(str(self.currentValue))
        

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ProcessScreen = QtWidgets.QMainWindow()
    ui = Ui_ProcessScreen()
    ui.setupUi(ProcessScreen)
    ProcessScreen.show()
    sys.exit(app.exec_())
