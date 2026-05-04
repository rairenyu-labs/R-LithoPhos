"""
LIMA Command Manager
=====================
Tüm komut gönderimlerini merkezi olarak yöneten yüksek seviye API.
UI katmanı bu sınıfı kullanarak seri port ile iletişim kurar.
"""

from protocol import LimaCommand, lookup_command
from serial_manager import serial_mgr


class CommandManager:
    """Merkezi komut yöneticisi. UI → SerialManager arasında köprü."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.log_callback = None
        return cls._instance

    # ── Genel gönderim ────────────────────────────────────────────────────

    def send(self, cmd: LimaCommand | str, value: int = 0) -> bool:
        """Komut gönderir.
        
        Args:
            cmd: LimaCommand enum veya ASCII komut adı (ör: 'MOVEMLZ')
            value: Gönderilecek integer değer
        
        Returns:
            Gönderim başarılıysa True
        """
        if isinstance(cmd, str):
            cmd = lookup_command(cmd)
            
        cmd_name = getattr(cmd, 'name', str(cmd))
        if self.log_callback:
            self.log_callback(f"{cmd_name} {value}")

        success = serial_mgr.send_command(cmd, value)
            
        return success

    # ── Motor hareket komutları ───────────────────────────────────────────

    def move_to_position(self, axis: str, value: int) -> bool:
        """Belirtilen eksene pozisyon komutu gönderir (MOVE).
        
        Args:
            axis: Eksen adı — 'MLZ','MRZ','MLX','MLY','MRX','MRY','SX','SY','SZ','STH','ML','MR','SXY'
            value: Hedef pozisyon değeri
        """
        cmd_map = {
            'MLZ': LimaCommand.MOVEMLZ,  'MRZ': LimaCommand.MOVEMRZ,
            'MLX': LimaCommand.MOVEMLX,  'MLY': LimaCommand.MOVEMLY,
            'MRX': LimaCommand.MOVEMRX,  'MRY': LimaCommand.MOVEMRY,
            'SX':  LimaCommand.MOVESX,   'SY':  LimaCommand.MOVESY,
            'SZ':  LimaCommand.MOVESZ,   'STH': LimaCommand.MOVESTH,
            'ML':  LimaCommand.MOVEML,   'MR':  LimaCommand.MOVEMR,
            'SXY': LimaCommand.MOVESXY,
        }
        return self.send(cmd_map[axis.upper()], value)

    def go_distance(self, axis: str, value: int) -> bool:
        """Belirtilen eksene mesafe komutu gönderir (GO).
        
        Args:
            axis: Eksen adı
            value: Mesafe değeri
        """
        cmd_map = {
            'MLZ': LimaCommand.GOMLZ,  'MRZ': LimaCommand.GOMRZ,
            'MLX': LimaCommand.GOMLX,  'MLY': LimaCommand.GOMLY,
            'MRX': LimaCommand.GOMRX,  'MRY': LimaCommand.GOMRY,
            'SX':  LimaCommand.GOSX,   'SY':  LimaCommand.GOSY,
            'SZ':  LimaCommand.GOSZ,   'STH': LimaCommand.GOSTH,
            'ML':  LimaCommand.GOML,   'MR':  LimaCommand.GOMR,
            'SXY': LimaCommand.GOSXY,
        }
        return self.send(cmd_map[axis.upper()], value)

    def jog_positive(self, axis: str, value: int = 1) -> bool:
        """Eksen pozitif yönde jog hareketi (P)."""
        cmd_map = {
            'MLZ': LimaCommand.MLZP, 'MRZ': LimaCommand.MRZP,
            'MLX': LimaCommand.MLXP, 'MLY': LimaCommand.MLYP,
            'MRX': LimaCommand.MRXP, 'MRY': LimaCommand.MRYP,
            'SX':  LimaCommand.SXP,  'SY':  LimaCommand.SYP,
            'SZ':  LimaCommand.SZP,  'STH': LimaCommand.STHP,
        }
        return self.send(cmd_map[axis.upper()], value)

    def jog_negative(self, axis: str, value: int = 1) -> bool:
        """Eksen negatif yönde jog hareketi (N)."""
        cmd_map = {
            'MLZ': LimaCommand.MLZN, 'MRZ': LimaCommand.MRZN,
            'MLX': LimaCommand.MLXN, 'MLY': LimaCommand.MLYN,
            'MRX': LimaCommand.MRXN, 'MRY': LimaCommand.MRYN,
            'SX':  LimaCommand.SXN,  'SY':  LimaCommand.SYN,
            'SZ':  LimaCommand.SZN,  'STH': LimaCommand.STHN,
        }
        return self.send(cmd_map[axis.upper()], value)

    def home_axis(self, axis: str) -> bool:
        """Ekseni home pozisyonuna gönderir."""
        cmd_map = {
            'MLZ': LimaCommand.HOMEMLZ, 'MRZ': LimaCommand.HOMEMRZ,
            'MLX': LimaCommand.HOMEMLX, 'MLY': LimaCommand.HOMEMLY,
            'MRX': LimaCommand.HOMEMRX, 'MRY': LimaCommand.HOMEMRY,
            'MLXY': LimaCommand.HOMEMLXY, 'MRXY': LimaCommand.HOMEMRXY,
            'SX':  LimaCommand.HOMESX,  'SY':  LimaCommand.HOMESY,
            'SZ':  LimaCommand.HOMESZ,  'STH': LimaCommand.HOMESTH,
            'SXY': LimaCommand.HOMESXY, 'SYSTEM': LimaCommand.HOMESYSTM,
        }
        return self.send(cmd_map[axis.upper()], 1)

    def stop(self, value: int = 1) -> bool:
        """Tüm motor hareketlerini durdurur."""
        return self.send(LimaCommand.STOP, value)

    # ── Hız & Işık komutları ──────────────────────────────────────────────

    def set_speed(self, speed_type: str, value: int) -> bool:
        """Hız ayarlar.
        
        Args:
            speed_type: 'SXY', 'MIC', 'FOCUS', 'MICRO', 'SAMPLE'
            value: Hız değeri (0-100 aralığı)
        """
        cmd_map = {
            'SXY':    LimaCommand.SXYSPEED,
            'MIC':    LimaCommand.MICSPEED,
            'FOCUS':  LimaCommand.FOCUSSPEED,
            'MICRO':  LimaCommand.MicroSpeed,
            'SAMPLE': LimaCommand.SampleSpeed,
        }
        return self.send(cmd_map[speed_type.upper()], value)

    def set_light(self, value: int) -> bool:
        """Mikro ışık değerini ayarlar."""
        return self.send(LimaCommand.MICLIGHT, value)

    # ── Contact Mode ──────────────────────────────────────────────────────

    def set_contact_mode(self, mode: int) -> bool:
        """Temas modu ayarlar (1=soft, 2=vacuum, 3=proximity)."""
        return self.send(LimaCommand.CONTMODE, mode)

    def set_proximity_contact(self, value: int) -> bool:
        """Proximity contact değeri gönderir."""
        return self.send(LimaCommand.PROXCONT, value)

    def set_hard_contact(self, value: int) -> bool:
        """Hard contact seçimi gönderir."""
        return self.send(LimaCommand.HARDCONTACTSEL, value)

    def set_contact_position(self, value: int) -> bool:
        """Contact pozisyonu gönderir."""
        return self.send(LimaCommand.CONTPOS, value)

    # ── Alignment ─────────────────────────────────────────────────────────

    def align(self, value: int = 1) -> bool:
        return self.send(LimaCommand.ALIGN, value)

    def align_back(self, value: int = 1) -> bool:
        return self.send(LimaCommand.ALIGNBACK, value)

    def align_check(self, value: int = 1) -> bool:
        return self.send(LimaCommand.ALIGNCHK, value)

    def align_check_back(self, value: int = 1) -> bool:
        return self.send(LimaCommand.ALIGNCHKBACK, value)

    def align_stop(self, value: int = 1) -> bool:
        return self.send(LimaCommand.ALIGNSTOP, value)

    # ── Exposure ──────────────────────────────────────────────────────────

    def set_exposure(self, value: int) -> bool:
        return self.send(LimaCommand.EXPOSURE, value)

    def set_exposure_dose(self, value: int) -> bool:
        return self.send(LimaCommand.EXPDOSE, value)

    def set_exposure_energy(self, value: int) -> bool:
        return self.send(LimaCommand.EXPENERGY, value)

    def set_exposure_power(self, value: int) -> bool:
        return self.send(LimaCommand.EXPPOWER, value)

    # ── Gap & Valve ───────────────────────────────────────────────────────

    def set_gap(self, value: int) -> bool:
        return self.send(LimaCommand.GAP, value)

    def set_gap_position(self, value: int) -> bool:
        return self.send(LimaCommand.GAPPOS, value)

    def valve_select(self, valve: str, value: int = 1) -> bool:
        """Valf seçim komutu gönderir.
        
        Args:
            valve: 'CONV','MASK','SAMP','SAMPH','SAMPF','RING','WECL','OPTIC','OPTC','OPM'
            value: Değer
        """
        cmd_map = {
            'CONV':   LimaCommand.CONVSEL,
            'MASK':   LimaCommand.MASKVSEL,
            'SAMP':   LimaCommand.SAMPVSEL,
            'SAMPH':  LimaCommand.SAMPHVSEL,
            'SAMPF':  LimaCommand.SAMPFVSEL,
            'RING':   LimaCommand.RINGSEL,
            'WECL':   LimaCommand.WECLSEL,
            'OPTIC':  LimaCommand.OPTICSEL,
            'OPTC':   LimaCommand.OPTC,
            'OPM':    LimaCommand.OPM,
        }
        return self.send(cmd_map[valve.upper()], value)

    # ── Sistem ────────────────────────────────────────────────────────────

    def comcheck(self, value: int = 1) -> bool:
        return self.send(LimaCommand.COMCHECK, value)

    def test_mode(self, value: int = 1) -> bool:
        return self.send(LimaCommand.TESTMODE, value)

    def test_mode_back(self, value: int = 1) -> bool:
        return self.send(LimaCommand.TESTMODEBACK, value)

    def joy_mode(self, value: int = 1) -> bool:
        return self.send(LimaCommand.JOYMODE, value)

    def joy_mode_back(self, value: int = 1) -> bool:
        return self.send(LimaCommand.JOYMODEBACK, value)

    def keep_home_position(self, value: int = 1) -> bool:
        return self.send(LimaCommand.KEEPHPOS, value)

    # ── Pozisyon raporlama ────────────────────────────────────────────────

    def set_mpos(self, axis: str, value: int) -> bool:
        """Eksen MPOS (memory position) değerini gönderir."""
        cmd_map = {
            'MLX': LimaCommand.MLXMPOS, 'MLY': LimaCommand.MLYMPOS,
            'MRX': LimaCommand.MRXMPOS, 'MRY': LimaCommand.MRYMPOS,
            'SX':  LimaCommand.SXMPOS,  'SY':  LimaCommand.SYMPOS,
        }
        return self.send(cmd_map[axis.upper()], value)

    def set_gpos(self, axis: str, value: int) -> bool:
        """Eksen GPOS (go position) değerini gönderir."""
        cmd_map = {
            'MLX': LimaCommand.MLXGPOS, 'MLY': LimaCommand.MLYGPOS,
            'MRX': LimaCommand.MRXGPOS, 'MRY': LimaCommand.MRYGPOS,
            'SX':  LimaCommand.SXGPOS,  'SY':  LimaCommand.SYGPOS,
        }
        return self.send(cmd_map[axis.upper()], value)

    def mlxyh(self, value: int = 1) -> bool:
        """Micro Left XY Home komutunu gönderir."""
        return self.send(LimaCommand.MLXYH, value)


# ── Global singleton instance ─────────────────────────────────────────────
cmd_mgr = CommandManager()
