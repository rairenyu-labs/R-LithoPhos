"""
LIMA Serial Manager
====================
Thread-safe seri port yöneticisi. QSerialPort üzerinden binary paket gönderimi/alımı.
Tüm seri port işlemleri bu sınıf üzerinden yönetilir.
"""

from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QMutexLocker, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

from protocol import (
    LimaCommand, build_packet, find_packets, PACKET_SIZE, START_BYTE, END_BYTE
)


class SerialManager(QObject):
    """Thread-safe seri port yöneticisi."""

    # ── Sinyaller ─────────────────────────────────────────────────────────
    connected       = pyqtSignal(str)          # port adı
    disconnected    = pyqtSignal()
    data_received   = pyqtSignal(object, int)  # (LimaCommand, value)
    raw_received    = pyqtSignal(bytes)         # ham byte verisi (debug)
    error_occurred  = pyqtSignal(str)          # hata mesajı
    connection_changed = pyqtSignal(bool)      # bağlantı durumu

    # ── Singleton ─────────────────────────────────────────────────────────
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent=None):
        if self._initialized:
            return
        super().__init__(parent)
        self._initialized = True

        self._port = QSerialPort()
        self._mutex = QMutex()
        self._read_buffer = bytearray()

        # Veri geldiğinde oku
        self._port.readyRead.connect(self._on_ready_read)
        self._port.errorOccurred.connect(self._on_error)

    # ── Bağlantı ──────────────────────────────────────────────────────────

    @staticmethod
    def available_ports() -> list[str]:
        """Mevcut seri portları listeler."""
        return [p.portName() for p in QSerialPortInfo.availablePorts()]

    def is_connected(self) -> bool:
        """Port açık mı?"""
        return self._port.isOpen()

    def connect(self, port_name: str = None, baud_rate: int = 9600) -> bool:
        """Seri porta bağlanır.
        
        Args:
            port_name: Port adı (None ise otomatik seçim: COM3 veya ilk port)
            baud_rate: Baud hızı (varsayılan 115200)
        
        Returns:
            Bağlantı başarılıysa True
        """
        with QMutexLocker(self._mutex):
            if self._port.isOpen():
                self._port.close()

            if not port_name:
                ports = self.available_ports()
                if not ports:
                    self.error_occurred.emit("Seri port bulunamadı")
                    return False
                port_name = "COM6" if "COM6" in ports else ports[0]

            self._port.setPortName(port_name)
            self._port.setBaudRate(baud_rate)
            self._port.setDataBits(QSerialPort.Data8)
            self._port.setParity(QSerialPort.NoParity)
            self._port.setStopBits(QSerialPort.OneStop)
            self._port.setReadBufferSize(0)
            self._port.clear()

            if self._port.open(QIODevice.ReadWrite):
                print(f"[SerialManager] Port {port_name} açıldı (baud={baud_rate})")
                self._read_buffer.clear()
                self.connected.emit(port_name)
                self.connection_changed.emit(True)
                return True
            else:
                err = self._port.errorString()
                print(f"[SerialManager] Port açılamadı: {err}")
                self.error_occurred.emit(f"Port açılamadı: {err}")
                self.connection_changed.emit(False)
                return False

    def disconnect(self):
        """Seri port bağlantısını kapatır."""
        with QMutexLocker(self._mutex):
            if self._port.isOpen():
                self._port.close()
                self._read_buffer.clear()
                print("[SerialManager] Port kapatıldı")
                self.disconnected.emit()
                self.connection_changed.emit(False)

    # ── Veri gönderme ─────────────────────────────────────────────────────

    def send_command(self, cmd: LimaCommand, value: int = 0) -> bool:
        """Binary paket oluşturup gönderir.
        
        Args:
            cmd: LimaCommand enum değeri
            value: Gönderilecek integer değer
        
        Returns:
            Gönderim başarılıysa True
        """
        with QMutexLocker(self._mutex):
            if not self._port.isOpen():
                self.error_occurred.emit("Port açık değil")
                return False

            packet = build_packet(cmd, value)
            bytes_written = self._port.write(packet)

            if bytes_written == len(packet):
                print(f"[TX] {cmd.name} = {value}  ->  {packet.hex(' ').upper()}")
                return True
            else:
                self.error_occurred.emit(f"Yazma hatası: {bytes_written}/{len(packet)} byte")
                return False

    def send_raw(self, data: bytes) -> bool:
        """Ham byte verisi gönderir (geriye uyumluluk).
        
        Args:
            data: Gönderilecek ham byte verisi
        
        Returns:
            Gönderim başarılıysa True
        """
        with QMutexLocker(self._mutex):
            if not self._port.isOpen():
                self.error_occurred.emit("Port açık değil")
                return False

            bytes_written = self._port.write(data)
            return bytes_written == len(data)

    # ── Veri okuma ────────────────────────────────────────────────────────

    def _on_ready_read(self):
        """QSerialPort readyRead sinyali tetiklendiğinde çağrılır."""
        raw = bytes(self._port.readAll())
        if not raw:
            return

        self.raw_received.emit(raw)
        self._read_buffer.extend(raw)

        # Tam paketleri bul ve sinyal gönder
        packets, remaining = find_packets(bytes(self._read_buffer))
        self._read_buffer = bytearray(remaining)

        for cmd, value in packets:
            print(f"[RX] {cmd.name} = {value}")
            self.data_received.emit(cmd, value)

    def _on_error(self, error):
        """QSerialPort hata sinyali."""
        if error == QSerialPort.NoError:
            return
        err_msg = self._port.errorString()
        print(f"[SerialManager] Hata: {err_msg}")
        self.error_occurred.emit(err_msg)

    # ── Qt property (geriye uyumluluk) ────────────────────────────────────

    @property
    def port(self) -> QSerialPort:
        """Alt seviye QSerialPort erişimi (geriye uyumluluk için)."""
        return self._port


# ── Global singleton instance ─────────────────────────────────────────────
serial_mgr = SerialManager()
