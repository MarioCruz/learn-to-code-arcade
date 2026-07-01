# 2048_test.py — touch-driven 2048 on the ST7796S (480x320) + XPT2046.
#
# Swipe up/down/left/right to slide the 4x4 board; equal tiles merge and double.
# Reach 2048 to win (keep going), no moves left = game over. NEW resets, MENU
# returns to the launcher. Resistive touch is single-point, so a "swipe" is the
# vector from finger-down to finger-up; a short press is treated as a tap (for
# the buttons). Importable (menu.py calls run()) or standalone via `mpremote run
# 2048_test.py` (plays a scripted SELFTEST first).

import time
import gc
import random
from game_common import ssd, read_raw, to_screen, in_rect
from gui.core.nanogui import refresh
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font

SELFTEST = True
FONT_H = 20
SWIPE_MIN = 30                     # px of travel to count as a swipe vs a tap

# ---- Layout -----------------------------------------------------------------
BX, BY, CELL = 8, 8, 76            # 4x4 board -> 304x304, x 8..312, y 8..312
PANEL_X = 322
BTN_W, BTN_H = 140, 42
NEW_X, NEW_Y = 330, 200
MENU_X, MENU_Y = 330, 252

TILE_BG = {2: GREY, 4: CYAN, 8: BLUE, 16: GREEN, 32: LIGHTGREEN, 64: DARKGREEN,
           128: YELLOW, 256: MAGENTA, 512: LIGHTRED, 1024: RED, 2048: WHITE}
DARK_TEXT = (GREY, CYAN, YELLOW, WHITE, LIGHTGREEN, GREEN)   # BLACK text on these

wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)

grid = [0] * 16                    # index = row * 4 + col
state = {"over": False, "won": False, "msg": "Swipe to move",
         "col": WHITE, "score": 0, "best": 0}


# ---- Input ------------------------------------------------------------------
def get_gesture():
    # Block for a touch, follow it to release, classify as tap or swipe.
    while True:
        p = read_raw()
        if p:
            break
        time.sleep_ms(20)
    sx, sy = to_screen(*p)
    lx, ly = sx, sy
    up = 0
    while up < 2:                  # track last point until 2 consecutive releases
        p = read_raw()
        if p is None:
            up += 1
        else:
            up = 0
            lx, ly = to_screen(*p)
        time.sleep_ms(10)
    dx, dy = lx - sx, ly - sy
    if max(abs(dx), abs(dy)) < SWIPE_MIN:
        return ("tap", sx, sy)
    if abs(dx) > abs(dy):
        return ("swipe", "R" if dx > 0 else "L")
    return ("swipe", "D" if dy > 0 else "U")


# ---- Game logic -------------------------------------------------------------
def slide_line(line):
    # Compress + merge a 4-cell line toward index 0. Returns (new, gained, moved).
    nz = [v for v in line if v]
    out = []
    gained = 0
    i = 0
    while i < len(nz):
        if i + 1 < len(nz) and nz[i] == nz[i + 1]:
            v = nz[i] * 2
            out.append(v)
            gained += v
            i += 2
        else:
            out.append(nz[i])
            i += 1
    while len(out) < 4:
        out.append(0)
    return out, gained, out != line


def move(d):
    moved_any = False
    gained = 0
    for k in range(4):
        if d in ("L", "R"):
            idx = [k * 4 + c for c in range(4)]
        else:
            idx = [r * 4 + k for r in range(4)]
        if d in ("R", "D"):
            idx = idx[::-1]
        new, sc, moved = slide_line([grid[i] for i in idx])
        if moved:
            moved_any = True
            gained += sc
            for i, v in zip(idx, new):
                grid[i] = v
    return moved_any, gained


def spawn():
    empty = [i for i in range(16) if grid[i] == 0]
    if empty:
        grid[empty[random.randint(0, len(empty) - 1)]] = 4 if random.randint(1, 10) == 1 else 2


def can_move():
    if 0 in grid:
        return True
    for r in range(4):
        for c in range(3):
            if grid[r * 4 + c] == grid[r * 4 + c + 1]:
                return True
    for c in range(4):
        for r in range(3):
            if grid[r * 4 + c] == grid[(r + 1) * 4 + c]:
                return True
    return False


# ---- Drawing ----------------------------------------------------------------
def _cx(s, x0, w):
    return x0 + (w - wri.stringlen(s)) // 2


def draw_button(bx, by, bg, text, tx):
    ssd.fill_rect(bx, by, BTN_W, BTN_H, bg)
    ssd.rect(bx, by, BTN_W, BTN_H, WHITE)
    Label(wri, by + (BTN_H - FONT_H) // 2, bx + tx, text, fgcolor=WHITE)


def redraw():
    gc.collect()
    ssd.fill(BLACK)
    for r in range(4):
        for c in range(4):
            v = grid[r * 4 + c]
            x0, y0 = BX + c * CELL, BY + r * CELL
            if v == 0:
                ssd.fill_rect(x0 + 3, y0 + 3, CELL - 6, CELL - 6, DARKBLUE)
            else:
                bg = TILE_BG.get(v, WHITE)
                ssd.fill_rect(x0 + 3, y0 + 3, CELL - 6, CELL - 6, bg)
                s = str(v)
                fg = BLACK if bg in DARK_TEXT else WHITE
                Label(wri, y0 + (CELL - FONT_H) // 2, _cx(s, x0, CELL), s,
                      fgcolor=fg, bgcolor=bg)
    Label(wri, 10, PANEL_X, "2048", fgcolor=GREEN)
    Label(wri, 60, PANEL_X, "Score: %d" % state["score"], fgcolor=CYAN)
    Label(wri, 90, PANEL_X, "Best:  %d" % state["best"], fgcolor=YELLOW)
    Label(wri, 140, PANEL_X, state["msg"], fgcolor=state["col"])
    draw_button(NEW_X, NEW_Y, DARKBLUE, "NEW GAME", 22)
    draw_button(MENU_X, MENU_Y, DARKGREEN, "MENU", 44)
    refresh(ssd)


def new_game():
    for i in range(16):
        grid[i] = 0
    state["over"] = False
    state["won"] = False
    state["msg"], state["col"] = "Swipe to move", WHITE
    state["score"] = 0
    random.seed(time.ticks_us())
    spawn()
    spawn()


# ---- Loop -------------------------------------------------------------------
def run():
    new_game()
    redraw()
    print("G2048_RUN free=%d" % gc.mem_free())
    while True:
        g = get_gesture()
        if g[0] == "tap":
            x, y = g[1], g[2]
            if in_rect(x, y, MENU_X, MENU_Y, BTN_W, BTN_H):
                return
            if in_rect(x, y, NEW_X, NEW_Y, BTN_W, BTN_H):
                new_game()
                redraw()
            continue
        if state["over"]:
            continue
        moved, gained = move(g[1])
        if not moved:
            continue
        state["score"] += gained
        if state["score"] > state["best"]:
            state["best"] = state["score"]
        spawn()
        if not state["won"] and 2048 in grid:
            state["won"] = True
            state["msg"], state["col"] = "2048! Keep going", GREEN
        if not can_move():
            state["over"] = True
            state["msg"], state["col"] = "Game over", RED
        redraw()


def selftest():
    print("SELFTEST_START free=%d" % gc.mem_free())
    for i in range(16):
        grid[i] = 0
    grid[0], grid[1], grid[2] = 2, 2, 4
    _, g = move("L")
    print("SELFTEST slideL row0=%s gained=%d (expect [4,4,0,0] 4)" % (grid[0:4], g))
    for i in range(16):
        grid[i] = 0
    grid[0], grid[1] = 1024, 1024
    move("L")
    print("SELFTEST merge row0[0]=%d (expect 2048)" % grid[0])
    new_game()
    print("SELFTEST new_game tiles=%d (expect 2)" % sum(1 for v in grid if v))
    redraw()
    print("SELFTEST_RENDERED free=%d" % gc.mem_free())
    time.sleep(2)
    new_game()


if __name__ == "__main__":
    refresh(ssd, True)
    if SELFTEST:
        selftest()
    run()
