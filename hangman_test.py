# hangman_test.py — touch-driven Hangman on the ST7796S (480x320) + XPT2046.
#
# nano-gui has no keyboard widget, so this draws its own on-screen A-Z keyboard
# (same tap-button pattern as the launcher). Tap letters to guess; six wrong
# guesses draws the full figure and ends the game. NEW resets, MENU returns to
# the launcher. Importable (menu.py calls run()) or standalone via `mpremote run
# hangman_test.py` (which plays a scripted SELFTEST first).

import time
import gc
import random
from game_common import ssd, W, get_tap, in_rect
from gui.core.nanogui import refresh, circle
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font

SELFTEST = True
MAX_MISSES = 6
FONT_H = 20

WORDS = ("PYTHON", "DISPLAY", "TOUCH", "CIRCUIT", "RESISTOR", "VOLTAGE",
         "PIXEL", "SENSOR", "BATTERY", "ARDUINO", "SOLDER", "SILICON",
         "GADGET", "ROBOT", "LASER", "MODULE", "FIRMWARE", "BINARY",
         "ROUTER", "ANTENNA", "NANOGUI", "PANEL", "GALLOWS", "HANGMAN",
         "MICRO", "KERNEL", "PACKET", "SIGNAL", "DIODE", "SKETCH")

# ---- Buttons + keyboard geometry -------------------------------------------
NEW_X, NEW_Y, TBW, TBH = 296, 6, 86, 30
MENU_X, MENU_Y = 388, 6

KEY_W, KEY_H, SP, VSP, KB_TOP = 50, 36, 52, 39, 202
KROWS = ("ABCDEFGHI", "JKLMNOPQR", "STUVWXYZ")
KEYS = {}
for _ri, _row in enumerate(KROWS):
    _total = (len(_row) - 1) * SP + KEY_W
    _x0 = (W - _total) // 2
    _y = KB_TOP + _ri * VSP
    for _ci, _ch in enumerate(_row):
        KEYS[_ch] = (_x0 + _ci * SP, _y, KEY_W, KEY_H)

wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)

guessed = set()
state = {"over": False, "msg": "Guess a letter", "col": WHITE,
         "misses": 0, "secret": ""}


# ---- Game logic -------------------------------------------------------------
def new_game(word=None):
    guessed.clear()
    if word is None:
        random.seed(time.ticks_us())
        word = WORDS[random.randint(0, len(WORDS) - 1)]
    state["secret"] = word
    state["misses"] = 0
    state["over"] = False
    state["msg"] = "Guess a letter"
    state["col"] = WHITE


def guess(ch):
    if state["over"] or ch in guessed:
        return
    guessed.add(ch)
    secret = state["secret"]
    if ch not in secret:
        state["misses"] += 1
        if state["misses"] >= MAX_MISSES:
            state["over"] = True
            state["msg"], state["col"] = "Answer: " + secret, RED
            return
    if all(c in guessed for c in secret):
        state["over"] = True
        state["msg"], state["col"] = "You win!", GREEN


# ---- Drawing ----------------------------------------------------------------
def _cx(s, x0, w):
    return x0 + (w - wri.stringlen(s)) // 2


def draw_button(bx, by, bw, bh, bg, text):
    ssd.fill_rect(bx, by, bw, bh, bg)
    ssd.rect(bx, by, bw, bh, WHITE)
    Label(wri, by + (bh - FONT_H) // 2, _cx(text, bx, bw), text, fgcolor=WHITE)


def draw_gallows(m):
    ssd.hline(18, 192, 104, WHITE)                 # base
    ssd.vline(30, 57, 135, WHITE)                  # pole
    ssd.hline(30, 57, 92, WHITE)                   # beam
    ssd.vline(120, 57, 18, WHITE)                  # rope
    if m >= 1:
        for r in (11, 12):
            circle(ssd, 120, 86, r, RED)           # head
    if m >= 2:
        for o in (-1, 0, 1):
            ssd.vline(120 + o, 98, 44, RED)        # body
    if m >= 3:
        ssd.line(120, 106, 103, 124, RED)          # left arm
        ssd.line(119, 106, 102, 124, RED)
    if m >= 4:
        ssd.line(120, 106, 137, 124, RED)          # right arm
        ssd.line(121, 106, 138, 124, RED)
    if m >= 5:
        ssd.line(120, 142, 104, 165, RED)          # left leg
        ssd.line(119, 142, 103, 165, RED)
    if m >= 6:
        ssd.line(120, 142, 136, 165, RED)          # right leg
        ssd.line(121, 142, 137, 165, RED)


def draw_keyboard():
    for ch, (x, y, w, h) in KEYS.items():
        if ch in guessed:
            bg = DARKGREEN if ch in state["secret"] else LIGHTRED
        else:
            bg = DARKBLUE
        ssd.fill_rect(x, y, w, h, bg)
        ssd.rect(x, y, w, h, WHITE)
        Label(wri, y + (h - FONT_H) // 2, _cx(ch, x, w), ch, fgcolor=WHITE)


def redraw():
    gc.collect()
    ssd.fill(BLACK)
    Label(wri, 8, 10, "HANGMAN", fgcolor=GREEN)
    draw_button(NEW_X, NEW_Y, TBW, TBH, DARKBLUE, "NEW")
    draw_button(MENU_X, MENU_Y, TBW, TBH, DARKGREEN, "MENU")
    draw_gallows(state["misses"])
    secret = state["secret"]
    disp = " ".join(c if c in guessed else "_" for c in secret)
    Label(wri, 92, _cx(disp, 150, W - 150), disp, fgcolor=CYAN)
    Label(wri, 130, _cx(state["msg"], 150, W - 150), state["msg"], fgcolor=state["col"])
    miss = "Misses: %d/%d" % (state["misses"], MAX_MISSES)
    Label(wri, 160, _cx(miss, 150, W - 150), miss, fgcolor=YELLOW)
    draw_keyboard()
    refresh(ssd)


# ---- Loop -------------------------------------------------------------------
def run():
    new_game()
    redraw()
    print("HANG_RUN free=%d" % gc.mem_free())
    while True:
        x, y = get_tap()
        if in_rect(x, y, MENU_X, MENU_Y, TBW, TBH):
            return
        if in_rect(x, y, NEW_X, NEW_Y, TBW, TBH):
            new_game()
            redraw()
            continue
        if state["over"]:
            continue
        for ch, (kx, ky, kw, kh) in KEYS.items():
            if in_rect(x, y, kx, ky, kw, kh):
                guess(ch)
                redraw()
                break


def selftest():
    print("SELFTEST_START free=%d" % gc.mem_free())
    new_game("PYTHON")
    for ch in "PYTHON":
        guess(ch)
    print("SELFTEST win msg=%s over=%s misses=%d" % (state["msg"], state["over"], state["misses"]))
    redraw()
    print("SELFTEST_RENDERED free=%d" % gc.mem_free())
    time.sleep(2)
    new_game("QUARTZ")
    for ch in "BCDFGK":                 # six letters, none in QUARTZ -> lose
        guess(ch)
    print("SELFTEST lose msg=%s over=%s misses=%d" % (state["msg"], state["over"], state["misses"]))
    redraw()
    time.sleep(1)
    new_game()


if __name__ == "__main__":
    refresh(ssd, True)
    if SELFTEST:
        selftest()
    run()
