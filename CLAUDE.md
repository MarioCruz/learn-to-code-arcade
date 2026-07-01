# CLAUDE.md — esp32-st7796-nanogui

Context for Claude Code. Read this before working here.

## What this is

Peter Hinch's **nano-gui** + **XPT2046** resistive touch running on a **4.0" ST7796S**
480×320 TFT, driven by a **plain ESP32 (no PSRAM)** under stock MicroPython v1.27.0.
Four working tests: `nanogui_test.py` (display render), `touch_test.py` (touch),
`tictactoe_test.py` (touch-driven game — the reference interactive-UI pattern), and
`connect4_test.py` (Connect Four with a minimax + alpha-beta AI).
Extracted from the `ESP32-EnvMonitor-v2` project on 2026-07-01.

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
