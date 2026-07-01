#!/usr/bin/env bash
# Deploy this project to an ESP32 running MicroPython via mpremote.
# Usage: ./deploy.sh [PORT]
#   e.g. ./deploy.sh /dev/cu.usbserial-110   (macOS)
#        ./deploy.sh /dev/ttyUSB0            (Linux)
set -e
PORT="${1:-/dev/ttyUSB0}"

echo "Deploying to $PORT ..."
mpremote connect "$PORT" fs cp -r drivers gui :
mpremote connect "$PORT" fs cp color_setup.py game_common.py menu.py nanogui_test.py touch_test.py tictactoe_test.py connect4_test.py minesweeper_test.py hangman_test.py :

echo
echo "Done. Launch the game menu:"
echo "  mpremote connect $PORT run menu.py"
echo "  # or make it boot on power-up:  mpremote connect $PORT fs cp menu.py :main.py"
echo
echo "Or run an individual test:"
echo "  mpremote connect $PORT run nanogui_test.py"
echo "  mpremote connect $PORT run touch_test.py"
echo "  mpremote connect $PORT run tictactoe_test.py"
echo "  mpremote connect $PORT run connect4_test.py"
echo "  mpremote connect $PORT run minesweeper_test.py"
echo "  mpremote connect $PORT run hangman_test.py"
