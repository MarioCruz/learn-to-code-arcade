# connect4_test.py — touch-driven Connect Four on the ST7796S (480x320) + XPT2046.
#
# You play RED (tap a column to drop). A minimax + alpha-beta AI plays YELLOW.
# NEW GAME resets, MENU returns to the launcher. Importable (menu.py calls run())
# or standalone via `mpremote run connect4_test.py` (plays a SELFTEST first,
# which also times an AI move).

import time
import gc
from game_common import ssd, get_tap, in_rect
from gui.core.nanogui import refresh, circle, fillcircle
from gui.core.writer import CWriter
from gui.core.colors import *
from gui.widgets.label import Label
import gui.fonts.freesans20 as font

SELFTEST = True
DEPTH = 4          # AI search depth (higher = stronger + slower)

# ---- Layout -----------------------------------------------------------------
COLS, ROWS = 7, 6
CELL = 43
BX, BY = 8, 34                     # board 301x258 -> x 8..309, y 34..292
DISC_R = CELL // 2 - 3             # 18
PANEL_X = 322
BTN_W, BTN_H = 140, 32
NEW_X, NEW_Y = 330, 244
MENU_X, MENU_Y = 330, 282

EMPTY, HUMAN, AI = 0, 1, 2         # HUMAN = RED, AI = YELLOW

wri = CWriter(ssd, font, WHITE, BLACK, verbose=False)

grid = [EMPTY] * (COLS * ROWS)     # index = row * COLS + col; row 0 = top
state = {"over": False, "combo": None, "msg": "Your turn",
         "col": RED, "you": 0, "cpu": 0, "draw": 0}

DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))   # right, down, down-right, down-left
ORDER = (3, 2, 4, 1, 5, 0, 6)              # centre-first column order


# ---- Game logic -------------------------------------------------------------
def valid_cols():
    return [c for c in ORDER if grid[c] == EMPTY]


def is_full():
    return EMPTY not in grid[:COLS]


def drop(c, piece):
    for r in range(ROWS - 1, -1, -1):
        if grid[r * COLS + c] == EMPTY:
            grid[r * COLS + c] = piece
            return r
    return -1


def made_win(r, c, piece):
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
    for r in range(ROWS):
        if grid[r * COLS + centre] == piece:
            s += 3
    for r in range(ROWS):
        base = r * COLS
        for c in range(COLS - 3):
            s += _score_window(base + c, base + c + 1, base + c + 2, base + c + 3, piece, opp)
    for c in range(COLS):
        for r in range(ROWS - 3):
            s += _score_window(r * COLS + c, (r + 1) * COLS + c,
                               (r + 2) * COLS + c, (r + 3) * COLS + c, piece, opp)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            s += _score_window(r * COLS + c, (r + 1) * COLS + c + 1,
                               (r + 2) * COLS + c + 2, (r + 3) * COLS + c + 3, piece, opp)
    for r in range(ROWS - 3):
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


# ---- Drawing ----------------------------------------------------------------
def draw_button(bx, by, bg, text, tx):
    ssd.fill_rect(bx, by, BTN_W, BTN_H, bg)
    ssd.rect(bx, by, BTN_W, BTN_H, WHITE)
    Label(wri, by + 8, bx + tx, text, fgcolor=WHITE)


def redraw():
    gc.collect()
    ssd.fill(BLACK)
    ssd.fill_rect(BX - 4, BY - 4, COLS * CELL + 8, ROWS * CELL + 8, BLUE)
    for r in range(ROWS):
        for c in range(COLS):
            cx = BX + c * CELL + CELL // 2
            cy = BY + r * CELL + CELL // 2
            v = grid[r * COLS + c]
            col = BLACK if v == EMPTY else (RED if v == HUMAN else YELLOW)
            fillcircle(ssd, cx, cy, DISC_R, col)
    if state["combo"]:
        for (r, c) in state["combo"]:
            cx = BX + c * CELL + CELL // 2
            cy = BY + r * CELL + CELL // 2
            circle(ssd, cx, cy, DISC_R, WHITE)
            circle(ssd, cx, cy, DISC_R - 1, WHITE)
    Label(wri, 8, PANEL_X, "CONNECT", fgcolor=GREEN)
    Label(wri, 32, PANEL_X, "  FOUR", fgcolor=GREEN)
    Label(wri, 80, PANEL_X, state["msg"], fgcolor=state["col"])
    Label(wri, 120, PANEL_X, "You:  %d" % state["you"], fgcolor=RED)
    Label(wri, 146, PANEL_X, "CPU:  %d" % state["cpu"], fgcolor=YELLOW)
    Label(wri, 172, PANEL_X, "Draw: %d" % state["draw"], fgcolor=WHITE)
    draw_button(NEW_X, NEW_Y, DARKBLUE, "NEW GAME", 22)
    draw_button(MENU_X, MENU_Y, DARKGREEN, "MENU", 44)
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
        state["msg"], state["col"] = "You win!", GREEN
        state["you"] += 1
    elif win_piece == AI:
        state["msg"], state["col"] = "CPU wins!", RED
        state["cpu"] += 1
    else:
        state["msg"], state["col"] = "Draw.", WHITE
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


# ---- Loop -------------------------------------------------------------------
def run():
    new_game()
    redraw()
    print("C4_RUN free=%d" % gc.mem_free())
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
        c = col_at(x)
        if c is None or grid[c] != EMPTY:
            continue
        drop(c, HUMAN)
        if resolve(HUMAN):
            redraw()
            continue
        state["msg"], state["col"] = "CPU thinking...", YELLOW
        redraw()
        aic = ai_choose()
        drop(aic, AI)
        if not resolve(AI):
            state["msg"], state["col"] = "Your turn", RED
        redraw()


def selftest():
    print("SELFTEST_START free=%d" % gc.mem_free())
    for c in range(4):
        drop(c, HUMAN)
    print("SELFTEST find_win(RED)=%s" % find_win(HUMAN))
    over = resolve(HUMAN)
    redraw()
    print("SELFTEST winner=%s over=%s rendered free=%d" % (state["msg"], over, gc.mem_free()))
    time.sleep(2)
    new_game()
    t0 = time.ticks_ms()
    c = ai_choose()
    dt = time.ticks_diff(time.ticks_ms(), t0)
    print("SELFTEST ai_choose(depth=%d)=col%d in %dms" % (DEPTH, c, dt))
    new_game()


if __name__ == "__main__":
    refresh(ssd, True)
    if SELFTEST:
        selftest()
    run()
