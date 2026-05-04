"""
LIMA Binary Protocol Engine
============================
Paket yapısı: [START (0xAA)][CMD_ID (1B)][DATA (4B Big-Endian)][CHECKSUM (1B)][END (0x55)]
Checksum: (CMD_ID + sum(DATA_BYTES)) & 0xFF

IMPORTANT: Bu dosyadaki hex kodları STM32 main.c'deki #define'lar ile
           BİREBİR eşleşmelidir. Değişiklik yaparken her iki dosyayı
           birlikte güncelleyin.
"""

import struct
from enum import IntEnum


# ─── Sabitler ────────────────────────────────────────────────────────────────
START_BYTE = 0xAA
END_BYTE   = 0x55
PACKET_SIZE = 8  # START(1) + CMD(1) + DATA(4) + CHK(1) + END(1)


class LimaCommand(IntEnum):
    """LIMA protokol komutları — STM32 main.c ile birebir eşleştirilmiş."""

    # ══════════════════════════════════════════════════════════════════════
    #  SYSTEM
    # ══════════════════════════════════════════════════════════════════════
    STOP            = 0x01
    COMCHECK        = 0x02
    TESTMODE        = 0x03
    TESTMODEBACK    = 0x04
    JOYMODE         = 0x05
    JOYMODEBACK     = 0x06
    HOMESYSTM       = 0xF0
    KEEPHPOS        = 0xF1
    YP              = 0xF2

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Left Z  (MLZ)
    # ══════════════════════════════════════════════════════════════════════
    MOVEMLZ         = 0x10   # TX: Pozisyona git
    MLZPOS          = 0x11   # RX: STM32 pozisyon geri bildirimi
    HOMEMLZ         = 0x14   # TX: Home komutu
    GOMLZ           = 0xAB   # TX: Mesafe git (0xAA START_BYTE çakışması düzeltildi)
    MLZP            = 0xAC   # TX: Jog pozitif
    MLZN            = 0xAD   # TX: Jog negatif

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Right Z  (MRZ)
    # ══════════════════════════════════════════════════════════════════════
    HOMEMRZ         = 0x19   # TX: Home komutu
    HOMEMRZOK       = 0x1A   # RX: Home tamamlandı bildirimi
    MRZPOS          = 0xB3   # RX: STM32 pozisyon geri bildirimi
    MOVEMRZ         = 0xBC   # TX: Pozisyona git
    GOMRZ           = 0xBD   # TX: Mesafe git
    MRZP            = 0xBE   # TX: Jog pozitif
    MRZN            = 0xBF   # TX: Jog negatif

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Theta  (STH)
    # ══════════════════════════════════════════════════════════════════════
    STPOS           = 0x20   # RX: STM32 pozisyon geri bildirimi
    MOVESTH         = 0x21   # TX: Pozisyona git
    GOSTH           = 0x22   # TX: Mesafe git
    STHP            = 0x23   # TX: Jog pozitif
    STHN            = 0x24   # TX: Jog negatif
    HOMESTH         = 0x94   # TX: Home komutu
    HOMESTHOK       = 0x95   # RX: Home tamamlandı bildirimi

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Sample X  (SX)
    # ══════════════════════════════════════════════════════════════════════
    SXPOS           = 0x30   # RX: STM32 pozisyon geri bildirimi
    SXGPOS          = 0x33   # TX: Go-distance pozisyon değeri
    SXP             = 0x35   # TX: Jog pozitif
    SXN             = 0x36   # TX: Jog negatif
    SXMPOS          = 0x79   # TX: Move-to-position pozisyon değeri
    MOVESX          = 0x60   # TX: Pozisyona git (Python-only, STM32 echo)
    GOSX            = 0x61   # TX: Mesafe git (Python-only, STM32 echo)
    HOMESX          = 0x66   # TX: Home komutu
    HOMESXOK        = 0x67   # RX: Home tamamlandı bildirimi

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Sample Y  (SY)
    # ══════════════════════════════════════════════════════════════════════
    SYPOS           = 0x31   # RX: STM32 pozisyon geri bildirimi
    SYGPOS          = 0x34   # TX: Go-distance pozisyon değeri
    SYP             = 0x37   # TX: Jog pozitif
    SYN             = 0x38   # TX: Jog negatif
    SYMPOS          = 0x7A   # TX: Move-to-position pozisyon değeri
    MOVESY          = 0x70   # TX: Pozisyona git (Python-only, STM32 echo)
    GOSY            = 0x71   # TX: Mesafe git (Python-only, STM32 echo)
    HOMESY          = 0x76   # TX: Home komutu
    HOMESYOK        = 0x77   # RX: Home tamamlandı bildirimi

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Sample XY  (Combined)
    # ══════════════════════════════════════════════════════════════════════
    GOSXY           = 0x78   # TX: Combined XY mesafe git
    MOVESXY         = 0x7B   # TX: Combined XY pozisyona git (Python-only)
    HOMESXY         = 0x7C   # TX: Combined XY home (Python-only)

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Sample Z  (SZ / Zed)
    # ══════════════════════════════════════════════════════════════════════
    SZPOS           = 0x32   # RX: STM32 pozisyon geri bildirimi
    MOVESZ          = 0x39   # TX: Pozisyona git
    GOSZ            = 0x3A   # TX: Mesafe git
    SZP             = 0x3B   # TX: Jog pozitif
    SZN             = 0x3C   # TX: Jog negatif
    HOMESZ          = 0x84   # TX: Home komutu
    HOMESZOK        = 0x85   # RX: Home tamamlandı bildirimi

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Left X  (MLX)
    # ══════════════════════════════════════════════════════════════════════
    MLXPOS          = 0xA0   # RX: STM32 pozisyon geri bildirimi
    MLXMPOS         = 0xA2   # TX: Move-to-position pozisyon değeri
    MLXGPOS         = 0xA3   # TX: Go-distance pozisyon değeri
    MLXP            = 0xA6   # TX: Jog pozitif
    MLXN            = 0xA7   # TX: Jog negatif
    HOMEMLX         = 0x53   # TX: Home komutu
    HOMEMLXOK       = 0x54   # RX: Home tamamlandı bildirimi
    MLXYH           = 0x27   # TX: ML XY Home özel komut (Python-only)
    HOMEMLXY        = 0x28   # TX: ML XY combined home (Python-only)

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Left Y  (MLY)
    # ══════════════════════════════════════════════════════════════════════
    MLYPOS          = 0xA1   # RX: STM32 pozisyon geri bildirimi
    MLYMPOS         = 0xA4   # TX: Move-to-position pozisyon değeri
    MLYGPOS         = 0xA5   # TX: Go-distance pozisyon değeri
    MLYP            = 0xA8   # TX: Jog pozitif
    MLYN            = 0xA9   # TX: Jog negatif
    HOMEMLY         = 0x15   # TX: Home komutu (Python-only)

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Left XY  (Combined — Python-only, STM32 echo)
    # ══════════════════════════════════════════════════════════════════════
    MOVEMLX         = 0x86   # TX: MLX pozisyona git (tek eksen)
    GOMLX           = 0x87   # TX: MLX mesafe git (tek eksen)
    MOVEMLY         = 0x88   # TX: MLY pozisyona git (tek eksen)
    GOMLY           = 0x89   # TX: MLY mesafe git (tek eksen)
    MOVEML          = 0x8A   # TX: ML combined XY pozisyona git
    GOML            = 0x8B   # TX: ML combined XY mesafe git

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Right X  (MRX)
    # ══════════════════════════════════════════════════════════════════════
    MRXPOS          = 0xB1   # RX: STM32 pozisyon geri bildirimi
    MRXMPOS         = 0xB4   # TX: Move-to-position pozisyon değeri
    MRXGPOS         = 0xB5   # TX: Go-distance pozisyon değeri
    MRXP            = 0xB8   # TX: Jog pozitif
    MRXN            = 0xB9   # TX: Jog negatif
    HOMEMRX         = 0x46   # TX: Home komutu (Python-only)
    HOMEMRXY        = 0x47   # TX: MR XY combined home (Python-only)

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Right Y  (MRY)
    # ══════════════════════════════════════════════════════════════════════
    MRYPOS          = 0xB2   # RX: STM32 pozisyon geri bildirimi
    MRYMPOS         = 0xB6   # TX: Move-to-position pozisyon değeri
    MRYGPOS         = 0xB7   # TX: Go-distance pozisyon değeri
    MRYP            = 0xBA   # TX: Jog pozitif
    MRYN            = 0xBB   # TX: Jog negatif
    HOMEMRY         = 0x57   # TX: Home komutu (Python-only)

    # ══════════════════════════════════════════════════════════════════════
    #  MOTOR: Micro Right XY  (Combined — Python-only, STM32 echo)
    # ══════════════════════════════════════════════════════════════════════
    MOVEMRX         = 0x40   # TX: MRX pozisyona git (tek eksen)
    GOMRX           = 0x41   # TX: MRX mesafe git (tek eksen)
    MOVEMRY         = 0x50   # TX: MRY pozisyona git (tek eksen)
    GOMRY           = 0x51   # TX: MRY mesafe git (tek eksen)
    MOVEMR          = 0x58   # TX: MR combined XY pozisyona git
    GOMR            = 0x59   # TX: MR combined XY mesafe git

    # ══════════════════════════════════════════════════════════════════════
    #  SPEED / LIGHT  (Python-only, STM32 echo)
    # ══════════════════════════════════════════════════════════════════════
    SXYSPEED        = 0x96   # TX: Sample XY hız ayarı
    MICSPEED        = 0x97   # TX: Microscope hız ayarı
    MICLIGHT        = 0x98   # TX: Microscope ışık değeri
    FOCUSSPEED      = 0x99   # TX: Focus hız ayarı
    MicroSpeed      = 0x9A   # TX: Micro motor hız ayarı
    SampleSpeed     = 0x9B   # TX: Sample motor hız ayarı

    # ══════════════════════════════════════════════════════════════════════
    #  CONTACT MODE
    # ══════════════════════════════════════════════════════════════════════
    CONTMODE        = 0xB0   # TX: Temas modu seçimi
    PROXCONT        = 0x9C   # TX: Proximity contact değeri (Python-only)
    CONTPOS         = 0x9D   # TX: Contact pozisyon değeri (Python-only)
    HARDCONTACTSEL  = 0x9E   # TX: Hard contact seçimi (Python-only)

    # ══════════════════════════════════════════════════════════════════════
    #  ALIGNMENT
    # ══════════════════════════════════════════════════════════════════════
    ALIGN           = 0xC0
    ALIGNBACK       = 0xC1
    ALIGNCHK        = 0xC2
    ALIGNCHKBACK    = 0xC3
    ALIGNSTOP       = 0xC4
    AUTOALIGN       = 0xC5
    AUTOFOCUS       = 0xC6

    # ══════════════════════════════════════════════════════════════════════
    #  EXPOSURE
    # ══════════════════════════════════════════════════════════════════════
    EXPOSURE        = 0xD0
    EXPDOSE         = 0xD1
    EXPENERGY       = 0xD2
    EXPPOWER        = 0xD3

    # ══════════════════════════════════════════════════════════════════════
    #  GAP / VALVE CONTROL
    # ══════════════════════════════════════════════════════════════════════
    GAP             = 0xE0
    GAPPOS          = 0xE1
    CONVSEL         = 0xE2
    MASKVSEL        = 0xE3
    SAMPVSEL        = 0xE4
    SAMPHVSEL       = 0xE5
    SAMPFVSEL       = 0xE6
    RINGSEL         = 0xE7
    WECLSEL         = 0xE8
    OPTICSEL        = 0xE9
    OPTC            = 0xEA
    OPM             = 0xEB


# ─── ASCII adından Enum'a hızlı lookup ───────────────────────────────────────
_NAME_TO_CMD: dict[str, LimaCommand] = {cmd.name: cmd for cmd in LimaCommand}


def lookup_command(ascii_name: str) -> LimaCommand:
    """ASCII komut adını (ör: 'MOVEMLZ') LimaCommand enum'una çevirir.
    
    Büyük/küçük harf duyarsız arama yapar; bulunamazsa KeyError fırlatır.
    """
    key = ascii_name.strip().strip("<>").upper()
    # Case-insensitive lookup (MicroSpeed, SampleSpeed gibi mixed-case komutlar için)
    for name, cmd in _NAME_TO_CMD.items():
        if name.upper() == key:
            return cmd
    raise KeyError(f"Bilinmeyen komut: '{ascii_name}'")


# ─── Paket oluşturma ────────────────────────────────────────────────────────

def _to_unsigned_32(value: int) -> int:
    """Negatif değerleri 32-bit unsigned'a çevirir (two's complement)."""
    if value < 0:
        value += 0x100000000
    return value & 0xFFFFFFFF


def _compute_checksum(cmd_byte: int, data_bytes: bytes) -> int:
    """Basit toplam checksum: (CMD + sum(DATA)) & 0xFF"""
    return (cmd_byte + sum(data_bytes)) & 0xFF


def build_packet(cmd: LimaCommand, value: int = 0) -> bytes:
    """Binary paket oluşturur.
    
    Yapı: [0xAA][CMD][D3][D2][D1][D0][CHECKSUM][0x55]
    Data: 4 byte, Big-Endian
    
    Args:
        cmd: LimaCommand enum değeri
        value: Gönderilecek integer değer (negatif olabilir)
    
    Returns:
        8 byte'lık ham paket verisi
    """
    unsigned_val = _to_unsigned_32(value)
    data_bytes = struct.pack(">I", unsigned_val)  # Big-Endian 4 byte
    cmd_byte = int(cmd)
    checksum = _compute_checksum(cmd_byte, data_bytes)

    return bytes([
        START_BYTE,
        cmd_byte,
        *data_bytes,
        checksum,
        END_BYTE
    ])


# ─── Paket ayrıştırma ───────────────────────────────────────────────────────

class ProtocolError(Exception):
    """Protokol hatası (geçersiz paket, checksum hatası vb.)"""
    pass


def parse_packet(data: bytes) -> tuple[LimaCommand, int]:
    """Ham byte verisinden komut ve değer ayrıştırır.
    
    Args:
        data: 8 byte'lık ham paket verisi
    
    Returns:
        (LimaCommand, int) tuple'ı
    
    Raises:
        ProtocolError: Geçersiz paket yapısı veya checksum hatası
    """
    if len(data) != PACKET_SIZE:
        raise ProtocolError(f"Paket boyutu hatalı: beklenen {PACKET_SIZE}, gelen {len(data)}")

    if data[0] != START_BYTE:
        raise ProtocolError(f"Geçersiz START byte: 0x{data[0]:02X}")

    if data[-1] != END_BYTE:
        raise ProtocolError(f"Geçersiz END byte: 0x{data[-1]:02X}")

    cmd_byte = data[1]
    data_bytes = data[2:6]
    received_checksum = data[6]

    # Checksum doğrulama
    expected_checksum = _compute_checksum(cmd_byte, data_bytes)
    if received_checksum != expected_checksum:
        raise ProtocolError(
            f"Checksum hatası: beklenen 0x{expected_checksum:02X}, "
            f"gelen 0x{received_checksum:02X}"
        )

    # Komutu bul
    try:
        cmd = LimaCommand(cmd_byte)
    except ValueError:
        raise ProtocolError(f"Bilinmeyen opcode: 0x{cmd_byte:02X}")

    # Değeri ayrıştır (Big-Endian unsigned → signed)
    value = struct.unpack(">I", data_bytes)[0]
    # 32-bit signed'a çevir (two's complement)
    if value >= 0x80000000:
        value -= 0x100000000

    return cmd, value


def find_packets(buffer: bytes) -> tuple[list[tuple[LimaCommand, int]], bytes]:
    """Bir byte buffer'ından tüm geçerli paketleri bulur ve ayrıştırır.
    
    Args:
        buffer: Ham byte verisi (birden fazla paket içerebilir)
    
    Returns:
        (parsed_packets, remaining_buffer) tuple'ı
    """
    packets = []
    i = 0

    while i <= len(buffer) - PACKET_SIZE:
        if buffer[i] == START_BYTE and buffer[i + PACKET_SIZE - 1] == END_BYTE:
            try:
                cmd, value = parse_packet(buffer[i:i + PACKET_SIZE])
                packets.append((cmd, value))
                i += PACKET_SIZE
            except ProtocolError:
                i += 1  # Geçersiz paket, bir byte ilerle
        else:
            i += 1

    return packets, buffer[i:]
