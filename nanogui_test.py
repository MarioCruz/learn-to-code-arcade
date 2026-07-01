# nanogui_test.py — visual smoke test of nano-gui on the ST7796S at full 480x320.
import gc

print("FREE_START", gc.mem_free())
from color_setup import ssd  # allocates the 76,800-byte framebuffer + inits panel

print("FREE_AFTER_SSD", gc.mem_free())
from gui.core.nanogui import refresh, circle, fillcircle
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font

print("FREE_AFTER_IMPORTS", gc.mem_free())

refresh(ssd, True)  # clear framebuffer to black and show

W = ssd.width  # 480
H = ssd.height  # 320

# 1) Color bars along the top — test color order (R,G,B,Y from top down)
bh = 34
ssd.fill_rect(0, 0, W, bh, RED)
ssd.fill_rect(0, bh, W, bh, GREEN)
ssd.fill_rect(0, 2 * bh, W, bh, BLUE)
ssd.fill_rect(0, 3 * bh, W, bh, YELLOW)

# 2) White border around the whole panel — checks full extent / orientation
ssd.rect(0, 0, W, H, WHITE)

# 3) Text via nano-gui writer/labels
CWriter.set_textpos(ssd, 0, 0)
wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)
Label(wri, 150, 8, "nano-gui on ST7796S", fgcolor=CYAN)
Label(wri, 180, 8, "Hello Mario - 480x320", fgcolor=WHITE)

# 4) Shapes — magenta filled circle, white outline (bottom-right region)
fillcircle(ssd, 400, 250, 45, MAGENTA)
circle(ssd, 400, 250, 55, WHITE)

refresh(ssd)  # push the whole framebuffer to the panel
gc.collect()
print("FREE_END", gc.mem_free())
print("NANOGUI_TEST_DONE")
