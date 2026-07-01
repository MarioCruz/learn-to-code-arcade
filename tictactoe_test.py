# tictactoe_test.py — touch-driven Tic-Tac-Toe on the ST7796S (480x320) + XPT2046.
#
# Human plays X (tap a cell). A small heuristic AI plays O. A NEW GAME button on
# the right panel resets the board. Reuses the proven XPT2046 read + calibration
# from touch_test.py on the shared SPI(1) bus.
#
# Run:  mpremote connect /dev/cu.usbserial-110 run tictactoe_test.py
# Stop: Ctrl-C (the interactive loop blocks waiting for taps).
#
# On startup a SELFTEST plays a scripted game so a headless `run` confirms the
# grid, X/O marks, win-line and win detection all render without error and
# reports free RAM. Set SELFTEST = False to skip straight to interactive play.

import time
import gc
from color_setup import ssd, spi, pcs
from gui.core.nanogui import refresh, circle
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font
from machine import Pin

SELFTEST = True

# ---- Touch (XPT2046 on shared SPI(1)) --------------------------------------
T_CS = Pin(33, Pin.OUT, value=1)
T_IRQ = Pin(36, Pin.IN)
W = ssd.width   # 480
H = ssd.height  # 320

# Calibration from touch_test.py (both axes inverted, high raw = low screen)
X_MIN, X_MAX = 270, 3850
Y_MIN, Y_MAX = 380, 3720


def read_raw():
    if T_IRQ.value() != 0:  # IRQ low == touched
        return None
    spi.init(baudrate=2_000_000)  # XPT2046 max ~2.5MHz
    pcs.value(1)                  # deselect display
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


def get_tap():
    # Block until a stable touch, then wait for release (debounce). Returns (x, y).
    while True:
        p = read_raw()
        if p:
            x, y = to_screen(*p)
            released = 0
            while released < 3:          # need 3 consecutive "up" reads
                released = released + 1 if read_raw() is None else 0
                time.sleep_ms(10)
            return (x, y)
        time.sleep_ms(20)


# ---- Layout -----------------------------------------------------------------
BX, BY, CELL = 10, 10, 100           # board: 300x300 square, cells of 100px
PANEL_X = 322                        # right-hand text column
BTN_X, BTN_Y, BTN_W, BTN_H = 330, 255, 140, 50

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
    # 1) win if possible, 2) block X, 3) center, 4) corner, 5) any.
    for mark in ("O", "X"):
        for i in range(9):
            if board[i] == " ":
                board[i] = mark
                w, _ = winner()
                board[i] = " "
                if w == mark:
                    return i
    for i in (4, 0, 2, 6, 8, 1, 3, 5, 7):
        if board[i] == " ":
            return i
    return None


def cell_at(x, y):
    if BX <= x < BX + 3 * CELL and BY <= y < BY + 3 * CELL:
        return ((y - BY) // CELL) * 3 + (x - BX) // CELL
    return None


def in_button(x, y):
    return BTN_X <= x <= BTN_X + BTN_W and BTN_Y <= y <= BTN_Y + BTN_H


# ---- Drawing ----------------------------------------------------------------
def draw_mark(i, p):
    x0 = BX + (i % 3) * CELL
    y0 = BY + (i // 3) * CELL
    pad = 20
    if p == "X":
        for off in (-1, 0, 1):  # 3px thick strokes
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


def redraw():
    gc.collect()
    ssd.fill(BLACK)
    # grid
    for k in (1, 2):
        ssd.vline(BX + k * CELL, BY, 3 * CELL, WHITE)
        ssd.hline(BX, BY + k * CELL, 3 * CELL, WHITE)
    ssd.rect(BX, BY, 3 * CELL, 3 * CELL, WHITE)
    # marks
    for i in range(9):
        if board[i] != " ":
            draw_mark(i, board[i])
    if state["combo"]:
        draw_win(state["combo"])
    # right panel
    Label(wri, 10, PANEL_X, "TIC-TAC-TOE", fgcolor=GREEN)
    Label(wri, 70, PANEL_X, state["msg"], fgcolor=state["col"])
    Label(wri, 120, PANEL_X, "You (X): %d" % state["x"], fgcolor=CYAN)
    Label(wri, 150, PANEL_X, "CPU (O): %d" % state["o"], fgcolor=YELLOW)
    Label(wri, 180, PANEL_X, "Draws:  %d" % state["d"], fgcolor=WHITE)
    # new game button
    ssd.fill_rect(BTN_X, BTN_Y, BTN_W, BTN_H, DARKBLUE)
    ssd.rect(BTN_X, BTN_Y, BTN_W, BTN_H, WHITE)
    Label(wri, BTN_Y + 16, BTN_X + 22, "NEW GAME", fgcolor=WHITE)
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
        state["msg"] = "You win!"
        state["col"] = GREEN
        state["x"] += 1
    elif win_mark == "O":
        state["msg"] = "CPU wins!"
        state["col"] = RED
        state["o"] += 1
    else:
        state["msg"] = "Draw."
        state["col"] = WHITE
        state["d"] += 1


def resolve():
    # Check terminal state after a move; return True if the game ended.
    w, combo = winner()
    if w or board_full():
        finish(w, combo)
        return True
    return False


# ---- Self-test (scripted game to exercise all render paths) ------------------
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
    redraw()
    print("SELFTEST_DONE free=%d" % gc.mem_free())


# ---- Main -------------------------------------------------------------------
def main():
    refresh(ssd, True)  # clear + show
    if SELFTEST:
        selftest()
    new_game()
    redraw()
    print("TTT_READY tap a cell to play (Ctrl-C to stop) free=%d" % gc.mem_free())
    while True:
        x, y = get_tap()
        if in_button(x, y):
            new_game()
            redraw()
            continue
        if state["over"]:
            continue                       # game over: only NEW GAME resets
        i = cell_at(x, y)
        if i is None or board[i] != " ":
            continue
        board[i] = "X"                     # human move
        if resolve():
            redraw()
            continue
        redraw()
        state["msg"] = "CPU thinking..."
        state["col"] = YELLOW
        time.sleep_ms(300)
        j = ai_move()                      # AI move
        if j is not None:
            board[j] = "O"
        if not resolve():
            state["msg"] = "Your turn (X)"
            state["col"] = CYAN
        redraw()


main()
