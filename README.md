# esp32-st7796-nanogui

Running [Peter Hinch's **nano-gui**](https://github.com/peterhinch/micropython-nano-gui)
on a **4.0" ST7796S** (480×320) TFT with **XPT2046** resistive touch, driven by a
plain ESP32 under stock MicroPython — no PSRAM, no custom firmware.

Two ready-to-run tests:

| File | What it does |
|------|--------------|
| `nanogui_test.py` | Full-screen nano-gui render: color bars, border, text labels, shapes. |
| `touch_test.py`   | Reads the XPT2046 over the shared SPI bus and draws a marker where you touch, with 5 on-screen calibration targets. |

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

# 2. copy this project to the board
mpremote connect /dev/ttyUSB0 fs cp -r drivers gui :
mpremote connect /dev/ttyUSB0 fs cp color_setup.py nanogui_test.py touch_test.py :

# 3. run a test
mpremote connect /dev/ttyUSB0 run nanogui_test.py
mpremote connect /dev/ttyUSB0 run touch_test.py
```

(Adjust the serial port for your OS, e.g. `/dev/cu.usbserial-XXXX` on macOS.)

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

## Credits & license

- **nano-gui** (everything under `gui/`, plus `drivers/boolpalette.py`) —
  © Peter Hinch, MIT. See `LICENSE-nano-gui`. Upstream:
  https://github.com/peterhinch/micropython-nano-gui
- **ST7796 driver, hardware setup, and tests** (`drivers/st7796/st7796.py`,
  `color_setup.py`, `nanogui_test.py`, `touch_test.py`) — © Mario Cruz, MIT.
  See `LICENSE`. The ST7796 driver derives from Peter Hinch's ILI9486 driver (MIT).
