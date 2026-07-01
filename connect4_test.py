# connect4_test.py — touch-driven Connect Four on the ST7796S (480x320) + XPT2046.
#
# You play RED (tap a column to drop a disc). A minimax + alpha-beta AI plays
# YELLOW. First to line up four (horizontal / vertical / diagonal) wins; the
# winning four are ringed in white. A NEW GAME button on the right resets.
#
# Same reusable skeleton as tictactoe_test.py: calibrated XPT2046 read on the
# shared SPI(1) bus, a single `state` dict, and a full `redraw()` per change.
#
# Run:  mpremote connect /dev/cu.usbserial-110 run connect4_test.py
# Stop: Ctrl-C (the interactive loop blocks waiting for taps).
#
# On startup a SELFTEST plays a scripted position so a headless `run` confirms
# the board, discs, win detection + highlight render, and times one AI move.

import time
import gc
from color_setup import ssd, spi, pcs
from gui.core.nanogui import refresh, circle, fillcircle
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font
from machine import Pin

SELFTEST = True
DEPTH = 4          # AI search depth (higher = stronger + slower)

# ---- Touch (XPT2046 on shared SPI(1)) --------------------------------------
T_CS = Pin(33, Pin.OUT, value=1)
T_IRQ = Pin(36, Pin.IN)
W = ssd.width   # 480
H = ssd.height  # 320

X_MIN, X_MAX = 270, 3850          # calibration from touch_test.py
Y_MIN, Y_MAX = 380, 3720


def read_raw():
    if T_IRQ.value() != 0:        # IRQ low == touched
        return None
    spi.init(baudrate=2_000_000)  # XPT2046 max ~2.5MHz
    pcs.value(1)                  # deselect display
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


# ---- Layout -----------------------------------------------------------------
COLS, ROWS = 7, 6
CELL = 43
BX, BY = 8, 34                     # board 301x258 -> x 8..309, y 34..292
DISC_R = CELL // 2 - 3             # 18
PANEL_X = 322
BTN_X, BTN_Y, BTN_W, BTN_H = 330, 250, 140, 55

EMPTY, HUMAN, AI = 0, 1, 2         # HUMAN = RED, AI = YELLOW

wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)

grid = [EMPTY] * (COLS * ROWS)     # index = row * COLS + col; row 0 = top
state = {"over": False, "combo": None, "msg": "Your turn",
         "col": RED, "you": 0, "cpu": 0, "draw": 0}

DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))   # right, down, down-right, down-left
ORDER = (3, 2, 4, 1, 5, 0, 6)              # centre-first column order


# ---- Game logic -------------------------------------------------------------
def valid_cols():
    return [c for c in ORDER if grid[c] == EMPTY]     # top cell (row 0) free


def is_full():
    return EMPTY not in grid[:COLS]                   # all top cells taken


def drop(c, piece):
    for r in range(ROWS - 1, -1, -1):                 # bottom up
        if grid[r * COLS + c] == EMPTY:
            grid[r * COLS + c] = piece
            return r
    return -1


def made_win(r, c, piece):
    # Fast check: did the disc just placed at (r, c) complete a line of 4?
    for dr, dc in DIRS:
        count = 1
        rr, cc = r + dr, c + dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and grid[rr * COLS + cc] == piece:
            count += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and grid[rr * COLS + cc] == piece:
            count += 1
            rr -= dr
            cc -= dc
        if count >= 4:
            return True
    return False


def find_win(piece):
    # Full-board scan; returns the 4 winning cells for `piece`, else None.
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r * COLS + c] != piece:
                continue
            for dr, dc in DIRS:
                rr, cc = r + 3 * dr, c + 3 * dc
                if 0 <= rr < ROWS and 0 <= cc < COLS:
                    if all(grid[(r + k * dr) * COLS + (c + k * dc)] == piece
                           for k in range(4)):
                        return [(r + k * dr, c + k * dc) for k in range(4)]
    return None


def _score_window(a, b, c, d, piece, opp):
    cells = (grid[a], grid[b], grid[c], grid[d])
    p = cells.count(piece)
    o = cells.count(opp)
    e = cells.count(EMPTY)
    s = 0
    if p == 4:
        s += 100
    elif p == 3 and e == 1:
        s += 5
    elif p == 2 and e == 2:
        s += 2
    if o == 3 and e == 1:
        s -= 4
    return s


def score_position():
    piece, opp = AI, HUMAN
    s = 0
    centre = COLS // 2
    for r in range(ROWS):                             # prefer centre column
        if grid[r * COLS + centre] == piece:
            s += 3
    for r in range(ROWS):                             # horizontal
        base = r * COLS
        for c in range(COLS - 3):
            s += _score_window(base + c, base + c + 1, base + c + 2, base + c + 3, piece, opp)
    for c in range(COLS):                             # vertical
        for r in range(ROWS - 3):
            s += _score_window(r * COLS + c, (r + 1) * COLS + c,
                               (r + 2) * COLS + c, (r + 3) * COLS + c, piece, opp)
    for r in range(ROWS - 3):                         # diagonal down-right
        for c in range(COLS - 3):
            s += _score_window(r * COLS + c, (r + 1) * COLS + c + 1,
                               (r + 2) * COLS + c + 2, (r + 3) * COLS + c + 3, piece, opp)
    for r in range(ROWS - 3):                         # diagonal down-left
        for c in range(3, COLS):
            s += _score_window(r * COLS + c, (r + 1) * COLS + c - 1,
                               (r + 2) * COLS + c - 2, (r + 3) * COLS + c - 3, piece, opp)
    return s


def minimax(depth, alpha, beta, maximizing, lr, lc, lp):
    if lp is not None and made_win(lr, lc, lp):
        return (None, 1000000 + depth) if lp == AI else (None, -1000000 - depth)
    if is_full():
        return (None, 0)
    if depth == 0:
        return (None, score_position())
    cols = valid_cols()
    if maximizing:
        value, best = -1000000000, cols[0]
        for c in cols:
            r = drop(c, AI)
            _, s = minimax(depth - 1, alpha, beta, False, r, c, AI)
            grid[r * COLS + c] = EMPTY
            if s > value:
                value, best = s, c
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return (best, value)
    else:
        value, best = 1000000000, cols[0]
        for c in cols:
            r = drop(c, HUMAN)
            _, s = minimax(depth - 1, alpha, beta, True, r, c, HUMAN)
            grid[r * COLS + c] = EMPTY
            if s < value:
                value, best = s, c
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return (best, value)


def ai_choose():
    col, _ = minimax(DEPTH, -1000000000, 1000000000, True, None, None, None)
    if col is None:
        vc = valid_cols()
        col = vc[0] if vc else 0
    return col


def col_at(x):
    if BX <= x < BX + COLS * CELL:
        return (x - BX) // CELL
    return None


def in_button(x, y):
    return BTN_X <= x <= BTN_X + BTN_W and BTN_Y <= y <= BTN_Y + BTN_H


# ---- Drawing ----------------------------------------------------------------
def redraw():
    gc.collect()
    ssd.fill(BLACK)
    ssd.fill_rect(BX - 4, BY - 4, COLS * CELL + 8, ROWS * CELL + 8, BLUE)  # board
    for r in range(ROWS):
        for c in range(COLS):
            cx = BX + c * CELL + CELL // 2
            cy = BY + r * CELL + CELL // 2
            v = grid[r * COLS + c]
            col = BLACK if v == EMPTY else (RED if v == HUMAN else YELLOW)
            fillcircle(ssd, cx, cy, DISC_R, col)
    if state["combo"]:                                # ring the winning four
        for (r, c) in state["combo"]:
            cx = BX + c * CELL + CELL // 2
            cy = BY + r * CELL + CELL // 2
            circle(ssd, cx, cy, DISC_R, WHITE)
            circle(ssd, cx, cy, DISC_R - 1, WHITE)
    # right panel
    Label(wri, 8, PANEL_X, "CONNECT", fgcolor=GREEN)
    Label(wri, 32, PANEL_X, "  FOUR", fgcolor=GREEN)
    Label(wri, 80, PANEL_X, state["msg"], fgcolor=state["col"])
    Label(wri, 130, PANEL_X, "You:  %d" % state["you"], fgcolor=RED)
    Label(wri, 160, PANEL_X, "CPU:  %d" % state["cpu"], fgcolor=YELLOW)
    Label(wri, 190, PANEL_X, "Draw: %d" % state["draw"], fgcolor=WHITE)
    ssd.fill_rect(BTN_X, BTN_Y, BTN_W, BTN_H, DARKBLUE)
    ssd.rect(BTN_X, BTN_Y, BTN_W, BTN_H, WHITE)
    Label(wri, BTN_Y + 18, BTN_X + 22, "NEW GAME", fgcolor=WHITE)
    refresh(ssd)


def new_game():
    for i in range(len(grid)):
        grid[i] = EMPTY
    state["over"] = False
    state["combo"] = None
    state["msg"] = "Your turn"
    state["col"] = RED


def finish(win_piece, combo):
    state["over"] = True
    state["combo"] = combo
    if win_piece == HUMAN:
        state["msg"] = "You win!"
        state["col"] = GREEN
        state["you"] += 1
    elif win_piece == AI:
        state["msg"] = "CPU wins!"
        state["col"] = RED
        state["cpu"] += 1
    else:
        state["msg"] = "Draw."
        state["col"] = WHITE
        state["draw"] += 1


def resolve(piece):
    combo = find_win(piece)
    if combo:
        finish(piece, combo)
        return True
    if is_full():
        finish(EMPTY, None)
        return True
    return False


# ---- Self-test --------------------------------------------------------------
def selftest():
    print("SELFTEST_START free=%d" % gc.mem_free())
    for c in range(4):                                # RED four-in-a-row, bottom
        drop(c, HUMAN)
    print("SELFTEST find_win(RED)=%s" % find_win(HUMAN))
    over = resolve(HUMAN)
    redraw()
    print("SELFTEST winner=%s over=%s rendered free=%d" % (state["msg"], over, gc.mem_free()))
    time.sleep(2)
    new_game()                                        # time a first AI move
    t0 = time.ticks_ms()
    c = ai_choose()
    dt = time.ticks_diff(time.ticks_ms(), t0)
    print("SELFTEST ai_choose(depth=%d)=col%d in %dms" % (DEPTH, c, dt))
    new_game()
    redraw()
    print("SELFTEST_DONE free=%d" % gc.mem_free())


# ---- Main -------------------------------------------------------------------
def main():
    refresh(ssd, True)
    if SELFTEST:
        selftest()
    new_game()
    redraw()
    print("C4_READY tap a column to play (Ctrl-C to stop) free=%d" % gc.mem_free())
    while True:
        x, y = get_tap()
        if in_button(x, y):
            new_game()
            redraw()
            continue
        if state["over"]:
            continue
        c = col_at(x)
        if c is None or grid[c] != EMPTY:             # off-board or column full
            continue
        drop(c, HUMAN)                                # human move
        if resolve(HUMAN):
            redraw()
            continue
        state["msg"] = "CPU thinking..."
        state["col"] = YELLOW
        redraw()
        aic = ai_choose()                             # AI move
        drop(aic, AI)
        if not resolve(AI):
            state["msg"] = "Your turn"
            state["col"] = RED
        redraw()


main()
