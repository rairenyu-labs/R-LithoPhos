"""
LIMA Port Connect (Refactored)
===============================
Geriye uyumluluk wrapper — yeni SerialManager'ı kullanır.
"""

from serial_manager import serial_mgr
from protocol import LimaCommand


def portConnect(self):
    """Seri porta bağlanır ve başlangıç handshake paketi gönderir.
    
    Geriye uyumluluk: eski modüllerdeki portConnect(self) çağrılarını destekler.
    """
    # Bağlantıyı SerialManager üzerinden yap
    if serial_mgr.is_connected():
        if hasattr(self, 'msg_box_port2'):
            self.msg_box_port2()
        print("Port zaten açık")
        return

    success = serial_mgr.connect()

    if success:
        # Eski kod bağlantıda <> + 0x00000001 + _ gönderiyordu
        # Artık boş handshake olarak YP komutu ile değer=1 gönderilir
        serial_mgr.send_command(LimaCommand.YP, 1)
    else:
        if hasattr(self, 'msg_box_port2'):
            self.msg_box_port2()