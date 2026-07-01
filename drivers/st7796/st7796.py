# st7796.py nano-gui driver for ST7796S (e.g. E32R40T 4.0" 480x320)
#
# Framebuffer + show()/refresh logic: Peter Hinch's ILI9486 nano-gui driver
#   Copyright (c) Peter Hinch 2022-2024  (MIT license)
# Init sequence: adapted from the project's proven display.py ST7796S init.
#
# The panel is driven in PORTRAIT (native 320x480); nano-gui's show() performs
# the landscape rotation in software, so MADCTL stays portrait here.

from time import sleep_ms
import gc
import framebuf
import asyncio
from drivers.boolpalette import BoolPalette


@micropython.viper
def _lcopy(dest: ptr16, source: ptr8, lut: ptr16, length: int, gscale: bool):
    n: int = 0
    x: int = 0
    while length:
        c = source[x]
        p = c >> 4
        q = c & 0x0F
        if gscale:
            dest[n] = p >> 1 | p << 4 | p << 9 | ((p & 0x01) << 15)
            n += 1
            dest[n] = q >> 1 | q << 4 | q << 9 | ((q & 0x01) << 15)
        else:
            dest[n] = lut[p]
            n += 1
            dest[n] = lut[q]
        n += 1
        x += 1
        length -= 1


@micropython.viper
def _lscopy(dest: ptr16, source: ptr8, lut: ptr16, ch: int, gscale: bool):
    col = ch & 0x1FF
    height = (ch >> 9) & 0x1FF
    wbytes = ch >> 19
    n = 0
    clsb = col & 1
    idx = col >> 1
    while height:
        if clsb:
            c = source[idx] & 0x0F
        else:
            c = source[idx] >> 4
        dest[n] = c >> 1 | c << 4 | c << 9 | ((c & 0x01) << 15) if gscale else lut[c]
        n += 1
        idx += wbytes
        height -= 1


class ST7796(framebuf.FrameBuffer):

    lut = bytearray(32)
    COLOR_INVERT = 0

    @classmethod
    def rgb(cls, r, g, b):
        return cls.COLOR_INVERT ^ (
            (r & 0xF8) | (g & 0xE0) >> 5 | (g & 0x1C) << 11 | (b & 0xF8) << 5
        )

    def __init__(
        self, spi, cs, dc, rst, height=320, width=480, usd=False, mirror=False, init_spi=False
    ):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.lock_mode = False
        self.height = height
        self.width = width
        self._long = max(height, width)
        self._short = min(height, width)
        self._spi_init = init_spi
        self._gscale = False
        self.mode = framebuf.GS4_HMSB
        self.palette = BoolPalette(self.mode)
        gc.collect()
        buf = bytearray(height * width // 2)
        self.mvb = memoryview(buf)
        super().__init__(buf, width, height, self.mode)
        self._linebuf = bytearray(self._short * 2)

        # Hardware reset (rst may be a no-op callable if board has no RST line)
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(50)
        if self._spi_init:
            self._spi_init(spi)
        self._lock = asyncio.Lock()

        # --- ST7796S init (proven values from display.py) ---
        self._wcmd(b"\x01")  # SWRESET
        sleep_ms(120)
        self._wcmd(b"\x11")  # sleep out
        sleep_ms(120)
        self._wcd(b"\xf0", b"\xc3")  # unlock command set
        self._wcd(b"\xf0", b"\x96")
        # Portrait MADCTL so nano-gui's show() rotation is correct. BGR bit set.
        madctl = 0x48 if usd else 0x88
        if mirror:
            madctl ^= 0x80
        self._wcd(b"\x36", madctl.to_bytes(1, "big"))
        self._wcd(b"\x3a", b"\x55")  # COLMOD 16-bit
        # Column/page address only overridden if not the native 320x480 panel
        if self._short != 320:
            self._wcd(b"\x2a", int.to_bytes(self._short - 1, 4, "big"))
        if self._long != 480:
            self._wcd(b"\x2b", int.to_bytes(self._long - 1, 4, "big"))
        self._wcd(b"\xb5", b"\x02\x03\x00\x04")
        self._wcd(b"\xb6", b"\x80\x02\x3b")
        self._wcd(b"\xb1", b"\x80\x10")
        self._wcd(b"\xb4", b"\x00")
        self._wcd(b"\xc1", b"\x13")
        self._wcd(b"\xc2", b"\xa7")
        self._wcd(b"\xc5", b"\x09")
        self._wcd(b"\xe0", b"\xf0\x09\x0b\x06\x04\x15\x2f\x54\x42\x3c\x17\x14\x18\x1b")
        self._wcd(b"\xe1", b"\xe0\x09\x0b\x06\x04\x03\x2b\x43\x42\x3b\x16\x14\x17\x1b")
        self._wcd(b"\xf0", b"\x3c")  # lock command set
        self._wcd(b"\xf0", b"\x69")
        sleep_ms(120)
        self._wcmd(b"\x29")  # display on
        sleep_ms(100)
        self._wcmd(b"\x13")  # normal display mode on

    def _wcmd(self, command):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)

    def _wcd(self, command, data):
        self._dc(0)
        self._cs(0)
        self._spi.write(command)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def greyscale(self, gs=None):
        if gs is not None:
            self._gscale = gs
        return self._gscale

    def show(self):
        clut = ST7796.lut
        lb = self._linebuf
        buf = self.mvb
        cm = self._gscale
        if self._spi_init:
            self._spi_init(self._spi)
        self._wcmd(b"\x2c")  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        if self.width < self.height:  # Portrait
            wd = self.width // 2
            ht = self.height
            for start in range(0, wd * ht, wd):
                _lcopy(lb, buf[start:], clut, wd, cm)
                self._spi.write(lb)
        else:  # Landscape
            width = self.width
            wd = width - 1
            cargs = (self.height << 9) + (width << 18)
            for col in range(width):
                _lscopy(lb, buf, clut, wd - col + cargs, cm)
                self._spi.write(lb)
        self._cs(1)
