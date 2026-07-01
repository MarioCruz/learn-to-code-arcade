# menu.py — touch launcher for the games on the ST7796S (480x320) + XPT2046.
#
# Shows a button per game; tapping one loads that game's module and calls run().
# When you tap the game's MENU button, run() returns here and the game's module
# is unloaded (del sys.modules + gc.collect) so only ONE game's code is resident
# at a time — important on this no-PSRAM board where the framebuffer is the
# gating allocation.
#
# Run:  mpremote connect /dev/cu.usbserial-110 run menu.py
# Boot: copy as main.py (mpremote fs cp menu.py :main.py) to launch on power-up.

import gc
import sys
from game_common import ssd, W, H, get_tap, in_rect
from gui.core.nanogui import refresh
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font

MENU_SELFTEST = True

wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)

# (label, module name, accent colour)
GAMES = (("Tic-Tac-Toe", "tictactoe_test", CYAN),
         ("Connect Four", "connect4_test", YELLOW),
         ("Minesweeper", "minesweeper_test", GREEN),
         ("Hangman", "hangman_test", MAGENTA),
         ("2048", "2048_test", RED))

BTN_W, BTN_H, GAP = 300, 40, 10
BTN_X = (W - BTN_W) // 2                          # horizontally centred
BLOCK_H = len(GAMES) * BTN_H + (len(GAMES) - 1) * GAP
TOP = (H - BLOCK_H) // 2 + 6                      # centred vertically, nudged for title
FONT_H = 20                                       # freesans20 glyph height


def btn_rect(i):
    return (BTN_X, TOP + i * (BTN_H + GAP), BTN_W, BTN_H)


def _cx(s, x0, w):
    # x that centres string `s` within the span [x0, x0 + w)
    return x0 + (w - wri.stringlen(s)) // 2


def draw_menu():
    gc.collect()
    ssd.fill(BLACK)
    ssd.rect(0, 0, W, H, WHITE)
    title = "GAME MENU"
    Label(wri, 14, _cx(title, 0, W), title, fgcolor=WHITE)
    for i, (label, mod, col) in enumerate(GAMES):
        x, y, w, h = btn_rect(i)
        ssd.fill_rect(x, y, w, h, DARKBLUE)
        ssd.rect(x, y, w, h, col)
        Label(wri, y + (h - FONT_H) // 2, _cx(label, x, w), label, fgcolor=col)
    foot = "Tap a game to play"
    Label(wri, H - 24, _cx(foot, 0, W), foot, fgcolor=GREY)
    refresh(ssd)


def launch(mod_name):
    gc.collect()                            # reclaim menu-draw garbage first
    mod = __import__(mod_name)
    try:
        mod.run()
    finally:
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        del mod
        gc.collect()


def run():
    while True:
        draw_menu()
        chosen = None
        while chosen is None:
            x, y = get_tap()
            for i, (label, mod, col) in enumerate(GAMES):
                bx, by, bw, bh = btn_rect(i)
                if in_rect(x, y, bx, by, bw, bh):
                    chosen = mod
                    break
        launch(chosen)


def selftest():
    # Headless: confirm each game module loads + exposes run(), then unload.
    print("MENU_SELFTEST_START free=%d" % gc.mem_free())
    for label, mod, col in GAMES:
        m = __import__(mod)
        ok = hasattr(m, "run")
        print("MENU_SELFTEST %s run=%s free=%d" % (mod, ok, gc.mem_free()))
        if mod in sys.modules:
            del sys.modules[mod]
        del m
        gc.collect()
    print("MENU_SELFTEST_DONE free=%d" % gc.mem_free())


if MENU_SELFTEST:
    selftest()

draw_menu()
print("MENU_READY tap a game (Ctrl-C to stop) free=%d" % gc.mem_free())
run()
