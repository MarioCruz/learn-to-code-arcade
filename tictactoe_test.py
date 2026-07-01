# tictactoe_test.py — touch-driven Tic-Tac-Toe on the ST7796S (480x320) + XPT2046.
#
# You play X (tap a cell); a heuristic AI plays O. NEW GAME resets, MENU returns
# to the launcher. Importable (menu.py calls run()) or standalone via `mpremote
# run tictactoe_test.py` (which also plays a scripted SELFTEST first).

import time
import gc
from game_common import ssd, get_tap, in_rect
from gui.core.nanogui import refresh, circle
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font

SELFTEST = True

# ---- Layout -----------------------------------------------------------------
BX, BY, CELL = 10, 10, 100           # board: 300x300 square, cells of 100px
PANEL_X = 322
BTN_W, BTN_H = 140, 32
NEW_X, NEW_Y = 330, 246
MENU_X, MENU_Y = 330, 284

wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)

WINS = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6))

board = [" "] * 9
state = {"over": False, "combo": None, "msg": "Your turn (X)",
         "col": CYAN, "x": 0, "o": 0, "d": 0}


# ---- Game logic -------------------------------------------------------------
def winner():
    for a, b, c in WINS:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a], (a, b, c)
    return None, None


def board_full():
    return " " not in board


def ai_move():
    for mark in ("O", "X"):                    # win, else block X
        for i in range(9):
            if board[i] == " ":
                board[i] = mark
                w, _ = winner()
                board[i] = " "
                if w == mark:
                    return i
    for i in (4, 0, 2, 6, 8, 1, 3, 5, 7):      # centre, corners, edges
        if board[i] == " ":
            return i
    return None


def cell_at(x, y):
    if BX <= x < BX + 3 * CELL and BY <= y < BY + 3 * CELL:
        return ((y - BY) // CELL) * 3 + (x - BX) // CELL
    return None


# ---- Drawing ----------------------------------------------------------------
def draw_mark(i, p):
    x0 = BX + (i % 3) * CELL
    y0 = BY + (i // 3) * CELL
    pad = 20
    if p == "X":
        for off in (-1, 0, 1):
            ssd.line(x0 + pad, y0 + pad + off, x0 + CELL - pad, y0 + CELL - pad + off, CYAN)
            ssd.line(x0 + pad, y0 + CELL - pad + off, x0 + CELL - pad, y0 + pad + off, CYAN)
    else:
        cx, cy, r = x0 + CELL // 2, y0 + CELL // 2, CELL // 2 - pad
        for rr in (r, r - 1, r - 2):
            circle(ssd, cx, cy, rr, YELLOW)


def draw_win(combo):
    a, c = combo[0], combo[2]
    ax = BX + (a % 3) * CELL + CELL // 2
    ay = BY + (a // 3) * CELL + CELL // 2
    cx = BX + (c % 3) * CELL + CELL // 2
    cy = BY + (c // 3) * CELL + CELL // 2
    for off in (-1, 0, 1):
        ssd.line(ax + off, ay, cx + off, cy, RED)
        ssd.line(ax, ay + off, cx, cy + off, RED)


def draw_button(bx, by, bg, text, tx):
    ssd.fill_rect(bx, by, BTN_W, BTN_H, bg)
    ssd.rect(bx, by, BTN_W, BTN_H, WHITE)
    Label(wri, by + 8, bx + tx, text, fgcolor=WHITE)


def redraw():
    gc.collect()
    ssd.fill(BLACK)
    for k in (1, 2):
        ssd.vline(BX + k * CELL, BY, 3 * CELL, WHITE)
        ssd.hline(BX, BY + k * CELL, 3 * CELL, WHITE)
    ssd.rect(BX, BY, 3 * CELL, 3 * CELL, WHITE)
    for i in range(9):
        if board[i] != " ":
            draw_mark(i, board[i])
    if state["combo"]:
        draw_win(state["combo"])
    Label(wri, 10, PANEL_X, "TIC-TAC-TOE", fgcolor=GREEN)
    Label(wri, 70, PANEL_X, state["msg"], fgcolor=state["col"])
    Label(wri, 118, PANEL_X, "You (X): %d" % state["x"], fgcolor=CYAN)
    Label(wri, 146, PANEL_X, "CPU (O): %d" % state["o"], fgcolor=YELLOW)
    Label(wri, 174, PANEL_X, "Draws:  %d" % state["d"], fgcolor=WHITE)
    draw_button(NEW_X, NEW_Y, DARKBLUE, "NEW GAME", 22)
    draw_button(MENU_X, MENU_Y, DARKGREEN, "MENU", 44)
    refresh(ssd)


def new_game():
    for i in range(9):
        board[i] = " "
    state["over"] = False
    state["combo"] = None
    state["msg"] = "Your turn (X)"
    state["col"] = CYAN


def finish(win_mark, combo):
    state["over"] = True
    state["combo"] = combo
    if win_mark == "X":
        state["msg"], state["col"] = "You win!", GREEN
        state["x"] += 1
    elif win_mark == "O":
        state["msg"], state["col"] = "CPU wins!", RED
        state["o"] += 1
    else:
        state["msg"], state["col"] = "Draw.", WHITE
        state["d"] += 1


def resolve():
    w, combo = winner()
    if w or board_full():
        finish(w, combo)
        return True
    return False


# ---- Loop -------------------------------------------------------------------
def run():
    new_game()
    redraw()
    print("TTT_RUN free=%d" % gc.mem_free())
    while True:
        x, y = get_tap()
        if in_rect(x, y, MENU_X, MENU_Y, BTN_W, BTN_H):
            return
        if in_rect(x, y, NEW_X, NEW_Y, BTN_W, BTN_H):
            new_game()
            redraw()
            continue
        if state["over"]:
            continue
        i = cell_at(x, y)
        if i is None or board[i] != " ":
            continue
        board[i] = "X"
        if resolve():
            redraw()
            continue
        redraw()
        time.sleep_ms(300)
        j = ai_move()
        if j is not None:
            board[j] = "O"
        if not resolve():
            state["msg"], state["col"] = "Your turn (X)", CYAN
        redraw()


def selftest():
    print("SELFTEST_START free=%d" % gc.mem_free())
    for p, i in (("X", 0), ("O", 4), ("X", 1), ("O", 5), ("X", 2)):
        board[i] = p
    over = resolve()
    print("SELFTEST winner=%s combo=%s over=%s" % (state["msg"], state["combo"], over))
    redraw()
    print("SELFTEST_RENDERED free=%d" % gc.mem_free())
    time.sleep(2)
    new_game()


if __name__ == "__main__":
    refresh(ssd, True)
    if SELFTEST:
        selftest()
    run()
