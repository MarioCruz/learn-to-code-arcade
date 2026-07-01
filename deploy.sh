#!/usr/bin/env bash
# Deploy this project to an ESP32 running MicroPython via mpremote.
# Usage: ./deploy.sh [PORT]
#   e.g. ./deploy.sh /dev/cu.usbserial-110   (macOS)
#        ./deploy.sh /dev/ttyUSB0            (Linux)
set -e
PORT="${1:-/dev/ttyUSB0}"

echo "Deploying to $PORT ..."
mpremote connect "$PORT" fs cp -r drivers gui :
mpremote connect "$PORT" fs cp color_setup.py nanogui_test.py touch_test.py tictactoe_test.py connect4_test.py :

echo
echo "Done. Run a test:"
echo "  mpremote connect $PORT run nanogui_test.py"
echo "  mpremote connect $PORT run touch_test.py"
echo "  mpremote connect $PORT run tictactoe_test.py"
echo "  mpremote connect $PORT run connect4_test.py"
