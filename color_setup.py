# color_setup.py — nano-gui hardware setup for E32R40T ST7796S (480x320)
# Import this FIRST so the framebuffer is allocated before other modules.
from machine import Pin, SPI
import gc
from drivers.st7796.st7796 import ST7796 as SSD

pdc = Pin(2, Pin.OUT, value=0)
pcs = Pin(15, Pin.OUT, value=1)
pbl = Pin(27, Pin.OUT, value=1)  # backlight ON


# Board has no exposed LCD reset line; software reset is used. No-op callable.
class _NoRst:
    def __call__(self, v):
        pass


prst = _NoRst()

gc.collect()
spi = SPI(1, baudrate=20_000_000, polarity=0, phase=0,
          sck=Pin(14), mosi=Pin(13), miso=Pin(12))
ssd = SSD(spi, pcs, pdc, prst, height=320, width=480)
