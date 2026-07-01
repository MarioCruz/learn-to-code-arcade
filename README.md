# learn-to-code-arcade

**Build a real handheld game console — and learn to code doing it.**

Take a **~$15 ESP32 touchscreen**, load five classic games you can play right away —
**Tic-Tac-Toe, Connect Four, Minesweeper, Hangman, and 2048** — then open the code and start
changing it. Every game is written to be read and tinkered with, and paired with
[**Claude Code**](https://claude.com/claude-code) you get a patient tutor that explains any
file, makes changes alongside you, and helps you build your own games.

No experience needed. If you can copy and paste a few commands you'll have the games running
today; after that you learn the way real programmers do — change something, run it, see what
happens on actual hardware, and ask *why*.

## What you need to buy (~$15)

Just one board and a USB-C cable — **no soldering, no breadboard, no extra parts.**

| Part | What it is | Where |
|------|-----------|-------|
| ESP32 + 4" touchscreen board | The **[AITRIP 4.0″ ESP32 ST7796 touchscreen](https://www.amazon.com/dp/B0GGB5W5XK)** (480×320, model E32R40T / E32N40T): the ESP32 chip, a color display, and resistive touch all on one board with a USB-C port. | ~$15–20 on Amazon |
| USB-C cable | A **data** USB-C cable (not a charge-only one) to plug the board into your computer. | you likely have one |

This project was built and tested on that exact AITRIP board. The same hardware also shows
up elsewhere under *"ESP32 4.0 inch ST7796 480x320 touch"* (often ~$10 on AliExpress), and
usually ships as a small kit with a stylus.

## Load the games in ~10 minutes

You need a computer (Mac / Windows / Linux) with **Python** installed. Open a terminal:

```bash
# 1. install the two small tools that talk to the board
pip install esptool mpremote

# 2. get this project
git clone https://github.com/MarioCruz/learn-to-code-arcade
cd learn-to-code-arcade

# 3. one time: put MicroPython on the board. Download "ESP32_GENERIC" v1.27.0 from
#    https://micropython.org/download/ESP32_GENERIC/  then (swap in your port, see below):
esptool --chip esp32 --port YOUR_PORT erase-flash
esptool --chip esp32 --port YOUR_PORT --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-*.bin

# 4. copy the arcade onto the board and start the menu
./deploy.sh YOUR_PORT
mpremote connect YOUR_PORT run menu.py

# 5. optional: make it boot straight into the games whenever it is plugged in
mpremote connect YOUR_PORT fs cp menu.py :main.py
```

**Finding `YOUR_PORT`:** run `mpremote connect list`. It looks like `/dev/cu.usbserial-XXXX`
on macOS, `/dev/ttyUSB0` on Linux, or `COM3` on Windows.

Tap a game to play; each game's **MENU** button brings you back to the launcher.

## Learn to code with Claude Code

Now the fun part — **change it.** [Claude Code](https://claude.com/claude-code) is an AI
assistant that runs in your terminal, reads this project with you, explains what things do,
and does the typing while you learn. Install it, run `claude` inside this folder, and try
asking:

- *"Explain what `tictactoe_test.py` does, like I have never coded before."*
- *"Change the X marks to green and the O marks to orange."* — then re-run it and watch.
- *"Add BANANA, GUITAR and DRAGON to the Hangman word list."*
- *"Make the Connect Four computer easier to beat."* (hint: it is the `DEPTH` setting)
- *"Why does the screen only have 16 colors?"*
- *"Help me add a new game — Snake — to the menu."*

Every change is a tiny, safe experiment: edit a file, re-run it, and see the result on the
screen in seconds. That loop — **change → run → see → ask why** — is how you actually learn
to code, and doing it on real hardware you can hold in your hand makes it stick. Claude Code
is there for the *how* and the *why* the whole way.

> New to Claude Code? Get it at https://claude.com/claude-code, then run `claude` in this
> folder and say hello.

---

## Under the hood (the technical bits)

The arcade runs [Peter Hinch's **nano-gui**](https://github.com/peterhinch/micropython-nano-gui)
on a **4.0" ST7796S** (480×320) TFT with **XPT2046** resistive touch, driven by a plain
ESP32 under stock MicroPython — no PSRAM, no custom firmware.

The games and building blocks:

| File | What it does |
|------|--------------|
| `menu.py`           | **Game launcher** — a touch menu that runs any of the five games; each game's **MENU** button returns here. Can boot on power-up as `main.py`. |
| `tictactoe_test.py` | Tic-Tac-Toe: tap a cell to play X, a heuristic AI plays O, scoreboard + **NEW GAME**. The reference touch → state → redraw pattern. |
| `connect4_test.py`  | Connect Four: tap a column to drop a RED disc, a minimax + alpha-beta AI plays YELLOW, winning four ringed in white. |
| `minesweeper_test.py` | Minesweeper (9×7, 10 mines): a **MODE** button toggles DIG/FLAG (resistive touch has no right-click), first dig safe, zero-cells flood open. |
| `hangman_test.py`   | Hangman with a self-drawn on-screen A–Z keyboard: tap letters to guess, six misses draws the full figure. |
| `2048_test.py`      | 2048: **swipe** to slide the 4×4 board; equal tiles merge and double; reach 2048 to win. |
| `game_common.py`    | Shared display + touch helpers (imported by the menu and every game). |
| `nanogui_test.py`   | Full-screen nano-gui render smoke test: color bars, border, text, shapes. |
| `touch_test.py`     | XPT2046 touch read with 5 on-screen calibration targets. |

## Install the whole suite

Copy every driver, font, game, and the launcher to the board, then boot into the menu:

```bash
# 1. (first time only) flash MicroPython v1.27.0 — see "Flash & deploy" below
# 2. copy the whole project (drivers/, gui/, color_setup, game_common, menu, all games)
./deploy.sh /dev/cu.usbserial-110
# 3. run the menu now …
mpremote connect /dev/cu.usbserial-110 run menu.py
# 4. … or make it launch automatically on power-up
mpremote connect /dev/cu.usbserial-110 fs cp menu.py :main.py
```

`deploy.sh` copies `drivers/`, `gui/`, `color_setup.py`, `game_common.py`, `menu.py`, and
every test/game file. After step 4 the device boots straight into the game menu; remove it
with `mpremote connect <port> fs rm :main.py`.

## Game launcher (menu)

`menu.py` is a touch launcher that ties the five games together. It shows a button per
game; tapping one loads that game's module and calls its `run()`. Each game has a **MENU**
button that returns you to the launcher.

```bash
./deploy.sh /dev/cu.usbserial-110
mpremote connect /dev/cu.usbserial-110 run menu.py
# or make it boot on power-up:
mpremote connect /dev/cu.usbserial-110 fs cp menu.py :main.py
```

The game files are both **standalone-runnable** (`mpremote run tictactoe_test.py`
still works and plays a self-test first) **and importable** — the menu imports them and
calls `run()`, guarded by `if __name__ == "__main__"`. Because this board has no PSRAM and
the framebuffer is the gating allocation, the launcher **unloads a game's module**
(`del sys.modules[...]` + `gc.collect()`) when you leave it, so only one game's code is
resident at a time. Shared display + touch code lives in `game_common.py`, imported by the
menu and every game. Worst case (Minesweeper's large flood render under the menu) still
leaves ~33 KB free.

## Tic-tac-toe (touch game)

`tictactoe_test.py` is a complete touch app: **you play X** (tap a cell), a small
heuristic AI plays **O**, and the right-hand panel shows the title, whose turn it is, a
live scoreboard, and a **NEW GAME** button. X marks are cyan, O yellow, the winning line
red.

Install it onto the board and run it (see [Flash & deploy](#flash--deploy) for first-time
firmware/deps setup):

```bash
./deploy.sh /dev/cu.usbserial-110                          # install all project files
mpremote connect /dev/cu.usbserial-110 run tictactoe_test.py
```

On start it plays a ~2 s scripted self-test (this also confirms rendering + win detection
on a headless `run`), prints `TTT_READY`, then waits for taps. Tap a cell to move, tap
**NEW GAME** to reset, `Ctrl-C` to quit. Runs with ~50 KB free.

## Connect Four (touch game)

`connect4_test.py` is the standard 7×6 grid: **you play RED** (tap a column, the disc
drops to the lowest free slot), and a **minimax + alpha-beta** AI plays YELLOW. The
winning four are ringed in white; the right panel has the scoreboard and a **NEW GAME**
button.

```bash
./deploy.sh /dev/cu.usbserial-110
mpremote connect /dev/cu.usbserial-110 run connect4_test.py
```

Search depth is the `DEPTH` constant (default 4). On this ESP32 the AI's worst case (its
first move on an empty board) is ~1.5 s; mid-game it is faster thanks to alpha-beta
pruning and immediate win/block cutoffs, and it is masked by the "CPU thinking..." message.
Lower `DEPTH` for a snappier/weaker opponent, raise it for a stronger/slower one. The
startup self-test also prints the measured AI move time. Runs with ~46 KB free.

## Minesweeper (touch game)

`minesweeper_test.py` is a 9×7 board with 10 mines. Because resistive touch is
single-point (no right-click), a **MODE** button toggles between **DIG** and **FLAG** —
tap a cell to act in the current mode. The first dig is always safe (mines are placed
after it, avoiding the tapped cell and its neighbours), zero-cells flood open, numbers are
colour-coded 1–8, and the whole minefield is exposed on a loss. `Mines:` counts down as
you flag.

```bash
./deploy.sh /dev/cu.usbserial-110
mpremote connect /dev/cu.usbserial-110 run minesweeper_test.py
```

Tune `COLS`, `ROWS`, `MINES` at the top for a bigger/harder board (keep cells ≥ ~30 px so
they stay easy to tap). Runs with ~50 KB free (dips to ~37 KB during a large flood render).

## Hangman (touch game)

nano-gui has **no keyboard widget** (the vendored subset is display-only, with no input
widgets), so `hangman_test.py` draws its own on-screen **A–Z keyboard** — a 9/9/8 grid of
tap buttons built with the same pattern as the launcher. Tap letters to guess a word from
the built-in list; keys turn green (in the word) or red (a miss); six misses draws the full
figure and reveals the answer. **NEW** starts a new word, **MENU** returns to the launcher.

```bash
./deploy.sh /dev/cu.usbserial-110
mpremote connect /dev/cu.usbserial-110 run hangman_test.py
```

Edit the `WORDS` tuple to change the word list (keep entries A–Z and ≤ ~9 letters so they
fit the display). Runs with ~35 KB free.

## 2048 (touch game)

`2048_test.py` is the classic 4×4 slider. Because resistive touch is single-point, a
**swipe** is measured as the vector from finger-down to finger-up — swipe up/down/left/right
to slide every tile that way; equal tiles merge and double. A short press is treated as a
tap (for the **NEW GAME** / **MENU** buttons). Reach 2048 to win (keep going for a higher
score); when no move is possible it's game over. Tiles are colour-coded by value.

```bash
./deploy.sh /dev/cu.usbserial-110
mpremote connect /dev/cu.usbserial-110 run 2048_test.py
```

`SWIPE_MIN` (default 30 px) sets how far you must drag before it counts as a swipe rather
than a tap. Runs with ~53 KB free.

## Hardware

Target board: **E32R40T / E32N40T** (ESP32-D0WD-V3, 4 MB flash, **no PSRAM**),
4.0" ST7796S 480×320 landscape TFT, XPT2046 resistive touch.

| Signal | GPIO | Notes |
|--------|------|-------|
| Display SPI | SPI(1) @ 20 MHz | sck=14, mosi=13, miso=12 |
| Display CS / DC | 15 / 2 | |
| Backlight | 27 | active-high |
| Display reset | — | none wired; software reset (0x01) used |
| Touch (XPT2046) | shares SPI(1) | CS=33, IRQ=36, bus slowed to 2 MHz per read |

## ⚠️ Memory: run on a clean device

nano-gui uses a full-screen framebuffer. At 480×320 in 4-bit color that is
**76,800 bytes and must be one contiguous block**. This ESP32 has ~165 KB free on
a **factory-clean boot** with a ~107 KB largest contiguous block — so it fits, with
about **60 KB free** left after nano-gui loads and renders.

But if another large app (e.g. a full monitor firmware) is already resident, the
heap fragments and the framebuffer allocation fails with `MemoryError`. **Flash a
clean device (or make nano-gui your main app) — don't run this alongside a big
existing application.**

## Flash & deploy

Tested with MicroPython **v1.27.0** (`ESP32_GENERIC`). Using
[`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html):

```bash
# 1. (recommended) start from clean firmware
esptool --chip esp32 --port /dev/ttyUSB0 erase-flash
esptool --chip esp32 --port /dev/ttyUSB0 --baud 460800 \
        write-flash -z 0x1000 ESP32_GENERIC-<date>-v1.27.0.bin

# 2. copy this project to the board — the deploy.sh wrapper does the two cp calls below
./deploy.sh /dev/ttyUSB0
#   equivalently, by hand:
#   mpremote connect /dev/ttyUSB0 fs cp -r drivers gui :
#   mpremote connect /dev/ttyUSB0 fs cp color_setup.py nanogui_test.py touch_test.py tictactoe_test.py :

# 3. run a test (mpremote `run` executes the local file; deps from step 2 must be on the board)
mpremote connect /dev/ttyUSB0 run nanogui_test.py
mpremote connect /dev/ttyUSB0 run touch_test.py
mpremote connect /dev/ttyUSB0 run tictactoe_test.py   # tap to play; Ctrl-C to stop
```

(Adjust the serial port for your OS — on this Mac it is `/dev/cu.usbserial-110`.)

To iterate on a single file without re-copying everything, push just that file and re-run it:

```bash
mpremote connect /dev/cu.usbserial-110 fs cp tictactoe_test.py :
mpremote connect /dev/cu.usbserial-110 run tictactoe_test.py
```

## The ST7796 driver

`drivers/st7796/st7796.py` is a nano-gui display driver for the ST7796S. It reuses
the framebuffer + `show()` (4-bit color, software landscape rotation) logic from
Peter Hinch's ILI9486 nano-gui driver, but swaps in the ST7796S power/gamma
initialisation sequence (proven on this exact panel). The panel is driven in its
native **portrait** orientation and nano-gui rotates to landscape in software, so
`MADCTL` is left in portrait mode (0x88).

## Touch calibration

`touch_test.py` maps raw XPT2046 readings to screen coordinates with:

```
X_MIN, X_MAX = 270, 3850   # both axes inverted (high raw = low screen coord)
Y_MIN, Y_MAX = 380, 3720
```

These are accurate to ~10–15 px on the test unit. Adjust the four constants if your
panel reads differently.

## Building an interactive touch UI

`tictactoe_test.py` is the reference pattern for a touch-driven app on this stack, and
the starting point for bringing live hardware/sensor data onto the display. Its reusable
pieces:

- `read_raw()` / `to_screen()` — the calibrated XPT2046 read (same as `touch_test.py`):
  slow the shared bus to 2 MHz, read, then **always restore 20 MHz** for the display.
- `get_tap()` — blocks for one stable touch and waits for finger-release (debounce), so
  one physical tap yields exactly one event.
- A single `state` dict + `redraw()` that clears the framebuffer and repaints from state,
  then `refresh(ssd)` once. Full-redraw-per-change is simple and fast enough here (~50 KB
  free at runtime; a whole-screen `refresh` is well under a second at 20 MHz SPI).

For a sensor dashboard, keep that skeleton and drive `redraw()` from sensor reads on a
timer instead of (or alongside) taps. Note the XPT2046 and the display share SPI(1), so a
touch read must not overlap a `refresh` — the bus-speed switch in `read_raw()` handles the
handoff; do sensor I2C/1-Wire on their own pins.

## Credits & license

- **nano-gui** (everything under `gui/`, plus `drivers/boolpalette.py`) —
  © Peter Hinch, MIT. See `LICENSE-nano-gui`. Upstream:
  https://github.com/peterhinch/micropython-nano-gui
- **ST7796 driver, hardware setup, tests, games, and launcher**
  (`drivers/st7796/st7796.py`, `color_setup.py`, `game_common.py`, `menu.py`,
  `nanogui_test.py`, `touch_test.py`, `tictactoe_test.py`, `connect4_test.py`,
  `minesweeper_test.py`, `hangman_test.py`, `2048_test.py`) — © Mario Cruz, MIT. See
  `LICENSE`. The ST7796 driver derives from Peter Hinch's ILI9486 driver (MIT).
