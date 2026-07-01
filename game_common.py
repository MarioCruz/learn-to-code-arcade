# game_common.py — shared display + XPT2046 touch helpers for the game launcher
# and the games it runs. Import this instead of duplicating the touch code.
#
# Importing this allocates the nano-gui framebuffer (via color_setup) and sets up
# the touch pins once; every game and the menu share the single `ssd` instance.

import time
from color_setup import ssd, spi, pcs
from gui.core.colors import *          # noqa: F401,F403 (populate colour LUT)
from machine import Pin

T_CS = Pin(33, Pin.OUT, value=1)
T_IRQ = Pin(36, Pin.IN)
W = ssd.width
H = ssd.height

# Calibration from touch_test.py (both axes inverted, high raw = low screen coord)
X_MIN, X_MAX = 270, 3850
Y_MIN, Y_MAX = 380, 3720


def read_raw():
    if T_IRQ.value() != 0:             # IRQ low == touched
        return None
    spi.init(baudrate=2_000_000)       # XPT2046 max ~2.5MHz
    pcs.value(1)                       # deselect display
    xs = []
    ys = []
    try:
        for _ in range(5):
            T_CS.value(0)
            spi.write(b"\x90")
            r = spi.read(2)
            rx = ((r[0] << 8) | r[1]) >> 3
            T_CS.value(1)
            T_CS.value(0)
            spi.write(b"\xd0")
            r = spi.read(2)
            ry = ((r[0] << 8) | r[1]) >> 3
            T_CS.value(1)
            if 100 < rx < 4000 and 100 < ry < 4000:
                xs.append(rx)
                ys.append(ry)
    finally:
        spi.init(baudrate=20_000_000)  # ALWAYS restore fast SPI for the display
    if len(xs) < 2:
        return None
    xs.sort()
    ys.sort()
    m = len(xs) // 2
    return (xs[m], ys[m])


def to_screen(rx, ry):
    x = W - 1 - (rx - X_MIN) * W // (X_MAX - X_MIN)
    y = H - 1 - (ry - Y_MIN) * H // (Y_MAX - Y_MIN)
    return (max(0, min(W - 1, x)), max(0, min(H - 1, y)))


def get_tap():
    # Block until a stable touch, then wait for finger-release (debounce).
    while True:
        p = read_raw()
        if p:
            x, y = to_screen(*p)
            released = 0
            while released < 3:
                released = released + 1 if read_raw() is None else 0
                time.sleep_ms(10)
            return (x, y)
        time.sleep_ms(20)


def in_rect(x, y, bx, by, bw, bh):
    return bx <= x <= bx + bw and by <= y <= by + bh
