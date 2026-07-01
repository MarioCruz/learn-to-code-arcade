# minesweeper_test.py — touch-driven Minesweeper on the ST7796S (480x320) + XPT2046.
#
# 9x7 grid, 10 mines. Resistive touch is single-point (no right-click), so a MODE
# button toggles DIG/FLAG. First dig is safe, zero-cells flood open, mines reveal
# on a loss. NEW GAME resets, MENU returns to the launcher. Importable (menu.py
# calls run()) or standalone via `mpremote run minesweeper_test.py` (SELFTEST first).

import time
import gc
import random
from game_common import ssd, get_tap, in_rect
from gui.core.nanogui import refresh, fillcircle
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font

SELFTEST = True

# ---- Layout -----------------------------------------------------------------
COLS, ROWS, MINES = 9, 7, 10
N = COLS * ROWS
CELL = 33
BX = 8
BY = (ssd.height - ROWS * CELL) // 2   # vertically centred -> board y 44..275
PANEL_X = 322
BTN_W, BTN_H = 150, 40
MODE_X, MODE_Y = 325, 150
NEW_X, NEW_Y = 325, 208
MENU_X, MENU_Y = 325, 266

NUM_COLORS = {1: BLUE, 2: GREEN, 3: RED, 4: MAGENTA,
              5: YELLOW, 6: CYAN, 7: WHITE, 8: GREY}

wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)

mines = [False] * N
revealed = [False] * N
flagged = [False] * N
counts = [0] * N
state = {"over": False, "msg": "Dig!", "col": GREEN,
         "mode": "DIG", "started": False, "hit": -1}


# ---- Game logic -------------------------------------------------------------
def neighbors(r, c):
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                out.append((nr, nc))
    return out


def place_mines(sr, sc):
    safe = {sr * COLS + sc}
    for (nr, nc) in neighbors(sr, sc):
        safe.add(nr * COLS + nc)
    placed = 0
    while placed < MINES:
        i = random.randint(0, N - 1)
        if i in safe or mines[i]:
            continue
        mines[i] = True
        placed += 1
    for r in range(ROWS):
        for c in range(COLS):
            i = r * COLS + c
            if mines[i]:
                counts[i] = -1
                continue
            counts[i] = sum(1 for (nr, nc) in neighbors(r, c) if mines[nr * COLS + nc])


def flood(sr, sc):
    stack = [(sr, sc)]
    while stack:
        r, c = stack.pop()
        i = r * COLS + c
        if revealed[i] or flagged[i]:
            continue
        revealed[i] = True
        if counts[i] == 0:
            for (nr, nc) in neighbors(r, c):
                ni = nr * COLS + nc
                if not revealed[ni] and not flagged[ni]:
                    stack.append((nr, nc))


def check_win():
    for i in range(N):
        if not mines[i] and not revealed[i]:
            return False
    return True


def lose(hit_i):
    state["over"] = True
    state["msg"], state["col"] = "BOOM!", RED
    state["hit"] = hit_i
    for i in range(N):
        if mines[i]:
            revealed[i] = True


def win():
    state["over"] = True
    state["msg"], state["col"] = "You win!", GREEN
    for i in range(N):
        if mines[i]:
            flagged[i] = True


def mines_left():
    return MINES - sum(flagged)


def cell_at(x, y):
    if BX <= x < BX + COLS * CELL and BY <= y < BY + ROWS * CELL:
        return ((y - BY) // CELL, (x - BX) // CELL)
    return None


# ---- Drawing ----------------------------------------------------------------
def draw_flag(x0, y0):
    px = x0 + CELL // 2 - 4
    ssd.vline(px, y0 + 7, CELL - 14, WHITE)
    ssd.fill_rect(px, y0 + 7, 10, 7, RED)


def draw_mine(x0, y0, exploded):
    ssd.fill_rect(x0 + 1, y0 + 1, CELL - 2, CELL - 2, RED if exploded else LIGHTRED)
    cx, cy = x0 + CELL // 2, y0 + CELL // 2
    fillcircle(ssd, cx, cy, CELL // 2 - 8, BLACK)
    ssd.hline(x0 + 4, cy, CELL - 8, BLACK)
    ssd.vline(cx, y0 + 4, CELL - 8, BLACK)


def draw_cell(r, c):
    i = r * COLS + c
    x0, y0 = BX + c * CELL, BY + r * CELL
    if revealed[i]:
        if mines[i]:
            draw_mine(x0, y0, i == state["hit"])
        else:
            ssd.fill_rect(x0 + 1, y0 + 1, CELL - 2, CELL - 2, BLACK)
            n = counts[i]
            if n > 0:
                Label(wri, y0 + 6, x0 + (CELL - 13) // 2, str(n),
                      fgcolor=NUM_COLORS[n], bgcolor=BLACK)
    else:
        ssd.fill_rect(x0 + 1, y0 + 1, CELL - 2, CELL - 2, GREY)
        if flagged[i]:
            draw_flag(x0, y0)


def draw_button(bx, by, bg, text, tx):
    ssd.fill_rect(bx, by, BTN_W, BTN_H, bg)
    ssd.rect(bx, by, BTN_W, BTN_H, WHITE)
    Label(wri, by + 11, bx + tx, text, fgcolor=WHITE)


def redraw():
    gc.collect()
    ssd.fill(BLACK)
    ssd.fill_rect(BX, BY, COLS * CELL, ROWS * CELL, DARKBLUE)
    for r in range(ROWS):
        for c in range(COLS):
            draw_cell(r, c)
    Label(wri, 8, PANEL_X, "MINE-", fgcolor=CYAN)
    Label(wri, 32, PANEL_X, "SWEEPER", fgcolor=CYAN)
    Label(wri, 74, PANEL_X, "Mines: %d" % mines_left(), fgcolor=WHITE)
    Label(wri, 110, PANEL_X, state["msg"], fgcolor=state["col"])
    draw_button(MODE_X, MODE_Y, DARKGREEN if state["mode"] == "DIG" else LIGHTRED,
                "MODE: %s" % state["mode"], 12)
    draw_button(NEW_X, NEW_Y, DARKBLUE, "NEW GAME", 26)
    draw_button(MENU_X, MENU_Y, DARKGREEN, "MENU", 55)
    refresh(ssd)


def new_game():
    for i in range(N):
        mines[i] = revealed[i] = flagged[i] = False
        counts[i] = 0
    state["over"] = False
    state["msg"], state["col"] = "Dig!", GREEN
    state["mode"] = "DIG"
    state["started"] = False
    state["hit"] = -1


# ---- Loop -------------------------------------------------------------------
def run():
    new_game()
    redraw()
    print("MINE_RUN free=%d" % gc.mem_free())
    while True:
        x, y = get_tap()
        if in_rect(x, y, MENU_X, MENU_Y, BTN_W, BTN_H):
            return
        if in_rect(x, y, NEW_X, NEW_Y, BTN_W, BTN_H):
            new_game()
            redraw()
            continue
        if in_rect(x, y, MODE_X, MODE_Y, BTN_W, BTN_H):
            state["mode"] = "FLAG" if state["mode"] == "DIG" else "DIG"
            redraw()
            continue
        if state["over"]:
            continue
        cell = cell_at(x, y)
        if cell is None:
            continue
        r, c = cell
        i = r * COLS + c
        if state["mode"] == "FLAG":
            if not revealed[i]:
                flagged[i] = not flagged[i]
                redraw()
            continue
        if flagged[i] or revealed[i]:
            continue
        if not state["started"]:
            random.seed(time.ticks_us())
            place_mines(r, c)
            state["started"] = True
        if mines[i]:
            lose(i)
            redraw()
            continue
        flood(r, c)
        if check_win():
            win()
        redraw()


def selftest():
    print("SELFTEST_START free=%d" % gc.mem_free())
    random.seed(12345)
    place_mines(3, 4)
    i = 3 * COLS + 4
    print("SELFTEST mines=%d safe_cell_is_mine=%s safe_count=%d"
          % (sum(mines), mines[i], counts[i]))
    flood(3, 4)
    print("SELFTEST revealed_after_flood=%d" % sum(revealed))
    redraw()
    print("SELFTEST rendered free=%d" % gc.mem_free())
    time.sleep(2)
    mi = mines.index(True)
    lose(mi)
    redraw()
    print("SELFTEST loss msg=%s hit=%d" % (state["msg"], mi))
    time.sleep(1)
    new_game()


if __name__ == "__main__":
    refresh(ssd, True)
    if SELFTEST:
        selftest()
    run()
