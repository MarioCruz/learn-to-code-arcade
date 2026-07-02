# CLAUDE.md — learn-to-code-arcade

> Repo renamed 2026-07-01 from `esp32-st7796-nanogui` to **`learn-to-code-arcade`** and
> repositioned as a beginner "learn to code" kit: a ~$15 ESP32 touchscreen + five touch
> games + a README that teaches kids to buy the board, load the games, and learn coding by
> changing them with Claude Code. The local folder is still `esp32-st7796-nanogui`.
> Board buy link: https://www.amazon.com/dp/B0GGB5W5XK (AITRIP 4.0" ESP32 ST7796).

Context for Claude Code. Read this before working here.

## What this is

Peter Hinch's **nano-gui** + **XPT2046** resistive touch running on a **4.0" ST7796S**
480×320 TFT, driven by a **plain ESP32 (no PSRAM)** under stock MicroPython v1.27.0.
Tests + a game launcher: `nanogui_test.py` (display render), `touch_test.py` (touch),
and five games — `tictactoe_test.py` (the reference interactive-UI pattern),
`connect4_test.py` (minimax + alpha-beta AI), `minesweeper_test.py` (DIG/FLAG mode toggle),
`hangman_test.py` (self-drawn on-screen A-Z keyboard; nano-gui has no keyboard widget),
`2048_test.py` (swipe-driven; gesture = finger-down→up vector). `menu.py` is a touch
launcher that runs any of the five; shared display+touch code is in `game_common.py`. The games are both standalone-runnable and importable (guarded by
`if __name__ == "__main__"`); the menu unloads each game's module on exit so only one is
resident at a time (no PSRAM). Extracted from `ESP32-EnvMonitor-v2` on 2026-07-01.

## Hardware (measured / confirmed)

| Item | Detail |
|------|--------|
| Board | E32R40T / E32N40T |
| MCU | ESP32-D0WD-V3, dual-core 240 MHz, 4 MB flash, **NO PSRAM** (confirmed by flashing SPIRAM firmware — free RAM stayed ~114 KB, did not jump to MBs) |
| Display | ST7796S 480×320 landscape, SPI(1) @ 20 MHz — sck=14, mosi=13, miso=12, cs=15, dc=2; backlight=27 (active-high); **no reset pin** (software reset 0x01) |
| Touch | XPT2046, **shares SPI(1)** — CS=33, IRQ=36; bus slowed to 2 MHz per read then restored to 20 MHz |

## CRITICAL: RAM / framebuffer

nano-gui uses a full-screen framebuffer: 480×320 4-bit = **76,800 bytes, one contiguous block**.

- **Factory-clean boot:** ~165 KB free, ~107 KB largest contiguous block → framebuffer fits, **~60 KB free** after nano-gui loads and renders.
- **With a large app already resident** (e.g. the original EnvMonitor firmware), the heap fragments to a ~57 KB max contiguous block → `MemoryError` on the framebuffer alloc.
- **Therefore: run on a clean device / make the GUI the main app.** Do not run alongside a big existing application.

## ST7796 driver (`drivers/st7796/st7796.py`)

Reuses the framebuffer + `show()` logic (4-bit color, **software landscape rotation**)
from Peter Hinch's ILI9486 nano-gui driver, with the ST7796S power/gamma **init
sequence** grafted in (proven on this exact panel; originally from the EnvMonitor
`display.py`). The panel is driven in its native **PORTRAIT** orientation
(`MADCTL 0x88`); nano-gui rotates to landscape in software.
**Do not switch to a landscape MADCTL without rewriting `show()`** — the rotation
math depends on portrait hardware.

## Touch

`touch_test.py` reads the XPT2046 on the shared bus. Calibration (both axes inverted,
high raw = low screen coord):

```
X_MIN, X_MAX = 270, 3850
Y_MIN, Y_MAX = 380, 3720
```

Accurate to ~10–15 px on the test unit. Verified: taps land on the on-screen targets,
which **also confirms the display orientation is correct** (mismatched orientation
would misalign the calibration).

## Deploy / run

Firmware: `ESP32_GENERIC` v1.27.0. Serial port on this Mac: `/dev/cu.usbserial-110`.

```bash
./deploy.sh /dev/cu.usbserial-110                          # copy project to board
mpremote connect /dev/cu.usbserial-110 run nanogui_test.py # display test
mpremote connect /dev/cu.usbserial-110 run touch_test.py   # touch test (tap during ~35s)
mpremote connect /dev/cu.usbserial-110 run tictactoe_test.py # touch game (tap to play, Ctrl-C to stop)
mpremote connect /dev/cu.usbserial-110 run connect4_test.py  # Connect Four vs minimax AI (tap a column)
mpremote connect /dev/cu.usbserial-110 run minesweeper_test.py # Minesweeper (MODE toggles DIG/FLAG)
mpremote connect /dev/cu.usbserial-110 run hangman_test.py   # Hangman (on-screen A-Z keyboard)
mpremote connect /dev/cu.usbserial-110 run 2048_test.py      # 2048 (swipe to slide tiles)
mpremote connect /dev/cu.usbserial-110 run menu.py           # game launcher (tap a game; MENU returns)
# boot into the menu on power-up:
mpremote connect /dev/cu.usbserial-110 fs cp menu.py :main.py
```

Interactive touch capture: `run touch_test.py` blocks ~35 s and prints each tap's
`raw=(rx,ry) screen=(x,y)`; tap the 5 yellow targets during that window.

## Status / next steps

- ✅ nano-gui full-resolution (480×320) display render — works, ~60 KB free.
- ✅ XPT2046 touch with accurate calibration on shared SPI.
- ✅ Display orientation confirmed correct (via touch calibration alignment).
- ✅ `tictactoe_test.py` — full touch→state→redraw interactive UI loop; renders clean,
  ~50 KB free at runtime. The reference pattern for the next step below.
- ✅ `connect4_test.py` — Connect Four (7×6) on the same skeleton, with a minimax +
  alpha-beta AI (DEPTH=4, ~1.5 s worst-case move on an empty board). ~46 KB free.
- ✅ `minesweeper_test.py` — Minesweeper (9×7, 10 mines) on the same skeleton. Resistive
  touch has no right-click, so a MODE button toggles DIG/FLAG. First dig safe, zero-cells
  flood, `random` seeded from `ticks_us`. Dips to ~37 KB during a large flood render.
- ✅ `hangman_test.py` — Hangman with a self-drawn on-screen A-Z keyboard (nano-gui has NO
  keyboard widget — display-only). 9/9/8 key grid, six misses draws the figure. ~35 KB free.
- ✅ `2048_test.py` — 2048 (4×4). Adds SWIPE input: `get_gesture()` follows the touch from
  down to up and classifies tap vs swipe (dir from the larger axis). Logic self-tested;
  ~53 KB free. 5-game menu confirmed on device: all five games load/unload via the launcher
  (all `run=True`), MENU_READY, ~62 KB free. Button-position layout (BTN_H=40, GAP=10) is
  computed from `len(GAMES)` and headlessly verified to load; visual placement not eyeballed.
  Full-code check 2026-07-01: all 20 .py files compile; menu hardened (game crash can't kill
  the launcher; menu draws before the boot selftest; no double-draw at startup).
- ✅ **Device boots standalone**: `menu.py` installed as `main.py` on the board 2026-07-01,
  so it starts the arcade on any USB power, untethered. Remember: `mpremote run` is
  tethered — the program stops when the connection drops; only `main.py` runs standalone.
  Remove with `mpremote connect <port> fs rm :main.py` if REPL-first behavior is needed.
- ⚠️ **Cold-boot black screen ≠ software** (debugged 2026-07-01): symptoms were black screen
  at power-on while the code ran fine underneath (verified via `mpremote resume exec` —
  no reset — showing all modules loaded and the menu loop alive). Root cause was a flaky
  USB cable/power connection: panel + backlight inrush browned out the init; eventually the
  USB link dropped entirely. Fixed by swapping the cable. Diagnostic path worth reusing:
  `resume exec` to inspect live state without wiping it; `sys.modules` populated = code
  runs behind the black screen. `color_setup.py` retains a 250 ms power-settle before panel
  init as cheap insurance (proper ST7796 post-VDD timing).
- ✅ `menu.py` — touch launcher for the four games; `game_common.py` holds the shared
  display+touch helpers. Games are standalone-runnable AND importable; menu unloads each
  game's module on exit (only one resident — no PSRAM). Labels centred via `wri.stringlen`.
  Can boot as `main.py`. Worst case (Minesweeper flood under the menu) leaves ~33 KB free.
- 🔜 **Bring hardware/sensor data onto the UI** — build a live dashboard reusing the
  `tictactoe_test.py` skeleton (`read_raw`/`get_tap` + `state` dict + `redraw`), driving
  redraws from sensor reads. Sensors on their own pins; touch and display share SPI(1).
- ⚠️ **Colors not yet confirmed by eye** — bars should read R/G/B/Y top-to-bottom.
  If red/blue are swapped, flip the `MADCTL` BGR bit (0x08) in the driver, or set
  `ST7796.COLOR_INVERT`.
- ⬜ **micropython-touch** (full touch-driven GUI widgets) — not yet tried; should
  fit at full res since the framebuffer is the same size and is the gating allocation.
- ⬜ **LVGL** — needs a custom C firmware build (`lvgl_micropython`) and realistically
  PSRAM; a much bigger lift. RAM is not the blocker for nano-gui, but LVGL is.

## Provenance / license

Vendored nano-gui subset (`gui/**`, `drivers/boolpalette.py`) © Peter Hinch, MIT —
see `LICENSE-nano-gui`, upstream https://github.com/peterhinch/micropython-nano-gui.
Original files (`drivers/st7796/st7796.py`, `color_setup.py`, `*_test.py`) MIT — see
`LICENSE`.
