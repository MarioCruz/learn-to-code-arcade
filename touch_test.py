# touch_test.py — XPT2046 touch test on the shared SPI(1) bus, with nano-gui feedback.
# Tap the 5 yellow targets; a green dot is drawn where touch is detected.
import time
from color_setup import ssd, spi, pcs
from gui.core.nanogui import refresh, fillcircle, circle
from gui.core.colors import *
from machine import Pin

T_CS = Pin(33, Pin.OUT, value=1)
T_IRQ = Pin(36, Pin.IN)
W = ssd.width
H = ssd.height

# Calibration copied from the project's proven touch.py (both axes inverted)
X_MIN, X_MAX = 270, 3850
Y_MIN, Y_MAX = 380, 3720


def read_raw():
    # IRQ low == touched
    if T_IRQ.value() != 0:
        return None
    spi.init(baudrate=2_000_000)  # XPT2046 max ~2.5MHz
    pcs.value(1)  # deselect display
    xs = []
    ys = []
    try:
        for _ in range(5):
            T_CS.value(0)
            spi.write(b"\x90")  # X channel
            r = spi.read(2)
            rx = ((r[0] << 8) | r[1]) >> 3
            T_CS.value(1)
            T_CS.value(0)
            spi.write(b"\xd0")  # Y channel
            r = spi.read(2)
            ry = ((r[0] << 8) | r[1]) >> 3
            T_CS.value(1)
            if 100 < rx < 4000 and 100 < ry < 4000:
                xs.append(rx)
                ys.append(ry)
    finally:
        spi.init(baudrate=20_000_000)  # ALWAYS restore fast SPI for display
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


targets = ((40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40), (W // 2, H // 2))
refresh(ssd, True)
ssd.rect(0, 0, W, H, WHITE)
for (tx, ty) in targets:
    circle(ssd, tx, ty, 12, YELLOW)
refresh(ssd)

print("TOUCH_TEST_START tap the 5 yellow targets (~35s)")
t_end = time.ticks_add(time.ticks_ms(), 35000)
n = 0
while time.ticks_diff(t_end, time.ticks_ms()) > 0:
    p = read_raw()
    if p:
        rx, ry = p
        x, y = to_screen(rx, ry)
        n += 1
        print("TOUCH %d raw=(%d,%d) screen=(%d,%d)" % (n, rx, ry, x, y))
        fillcircle(ssd, x, y, 4, GREEN)
        refresh(ssd)
        time.sleep_ms(150)
    else:
        time.sleep_ms(20)
print("TOUCH_TEST_DONE touches=%d" % n)
