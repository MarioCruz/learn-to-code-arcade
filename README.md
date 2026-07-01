# esp32-st7796-nanogui

Running [Peter Hinch's **nano-gui**](https://github.com/peterhinch/micropython-nano-gui)
on a **4.0" ST7796S** (480×320) TFT with **XPT2046** resistive touch, driven by a
plain ESP32 under stock MicroPython — no PSRAM, no custom firmware.

Ready-to-run tests:

| File | What it does |
|------|--------------|
| `nanogui_test.py`   | Full-screen nano-gui render: color bars, border, text labels, shapes. |
| `touch_test.py`     | Reads the XPT2046 over the shared SPI bus and draws a marker where you touch, with 5 on-screen calibration targets. |
| `tictactoe_test.py` | Full touch-driven game: tap a cell to play X, a heuristic AI plays O, on-screen scoreboard + **NEW GAME** button. Demonstrates the complete touch → state → redraw loop. |

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
- **ST7796 driver, hardware setup, and tests** (`drivers/st7796/st7796.py`,
  `color_setup.py`, `nanogui_test.py`, `touch_test.py`, `tictactoe_test.py`) —
  © Mario Cruz, MIT. See `LICENSE`. The ST7796 driver derives from Peter Hinch's
  ILI9486 driver (MIT).
