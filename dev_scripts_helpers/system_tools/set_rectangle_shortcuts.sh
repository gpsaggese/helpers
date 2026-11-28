#!/bin/bash
# """
# Set the Rectangle window-manager shortcuts to cmd+ctrl+<digit>. Use 1 for
# left half, 2 for right half, 0 for center half, 3 for first third, and 4 for
# first fourth. Add opt for the mirrored version (last third, last fourth). The
# script backs up the preferences, kills Rectangle, clears clashing shortcuts,
# sets the new shortcuts, and restarts Rectangle.
#
# Usage:
#   > ./set_rectangle_shortcuts.sh
# """

set -euo pipefail

DOMAIN="com.knollsoft.Rectangle"

# NSEvent modifier flags.
CTRL=262144
OPT=524288
CMD=1048576
MOD=$((CMD + CTRL))
# Do not use shift for the mirrored shortcuts: ctrl+cmd+shift+3 and
# ctrl+cmd+shift+4 are the macOS screenshot-to-clipboard shortcuts.
MOD_MIRROR=$((CMD + CTRL + OPT))

# Key codes for the digits 0-4 on an ANSI keyboard.
KEY_0=29
KEY_1=18
KEY_2=19
KEY_3=20
KEY_4=21

set_shortcut() {
  # """
  # Set the shortcut of a Rectangle action.
  #
  # :param action: Rectangle action name (e.g., `centerHalf`)
  # :param key_code: macOS key code
  # :param flags: NSEvent modifier flags
  # """
  local action=$1
  local key_code=$2
  local flags=$3
  echo "Set ${action}: keyCode=${key_code} modifierFlags=${flags}"
  defaults write "${DOMAIN}" "${action}" -dict \
    keyCode -int "${key_code}" modifierFlags -int "${flags}"
}

clear_shortcut() {
  # """
  # Remove the shortcut of a Rectangle action.
  #
  # Rectangle stores a cleared shortcut as an empty dict.
  #
  # :param action: Rectangle action name (e.g., `firstTwoThirds`)
  # """
  local action=$1
  echo "Clear ${action}"
  defaults write "${DOMAIN}" "${action}" -dict
}

is_rectangle_running() {
  # """
  # Check if the Rectangle process is running.
  # """
  pgrep -x Rectangle >/dev/null
}

wait_rectangle_exit() {
  # """
  # Wait until Rectangle exits, for up to `timeout` seconds.
  #
  # :param timeout: max seconds to wait
  # :return: 0 if Rectangle exited, 1 otherwise
  # """
  local timeout=$1
  local i
  for ((i = 0; i < timeout * 10; i++)); do
    if ! is_rectangle_running; then
      return 0
    fi
    sleep 0.1
  done
  ! is_rectangle_running
}

kill_rectangle() {
  # """
  # Stop Rectangle, escalating from a graceful quit to SIGKILL.
  # """
  if ! is_rectangle_running; then
    echo "Rectangle is not running"
    return 0
  fi
  echo "Kill Rectangle"
  osascript -e 'tell application "Rectangle" to quit' 2>/dev/null || true
  if wait_rectangle_exit 3; then
    return 0
  fi
  pkill -x Rectangle || true
  if wait_rectangle_exit 3; then
    return 0
  fi
  pkill -9 -x Rectangle || true
  if ! wait_rectangle_exit 3; then
    echo "ERROR: Cannot kill Rectangle" >&2
    exit 1
  fi
}

start_rectangle() {
  # """
  # Start Rectangle and check that it is running.
  # """
  echo "Start Rectangle"
  open -a Rectangle
  local i
  for ((i = 0; i < 50; i++)); do
    if is_rectangle_running; then
      return 0
    fi
    sleep 0.1
  done
  echo "ERROR: Rectangle did not start" >&2
  exit 1
}

# Back up the current preferences.
BACKUP="${HOME}/rectangle_prefs_backup.$(date +%Y%m%d_%H%M%S).plist"
defaults export "${DOMAIN}" "${BACKUP}"
echo "Backup: ${BACKUP}"

# Rectangle caches its preferences, so kill it before writing.
kill_rectangle

# Clear old shortcuts that clash with text editing and Chrome:
# - cmd+shift+left/right select text to line start/end.
# - cmd+opt+left/right switch Chrome tabs.
clear_shortcut firstTwoThirds
clear_shortcut centerTwoThirds
clear_shortcut centerThird

# Clear shortcuts that an earlier version of this script set.
clear_shortcut centerThreeFourths

# New shortcuts.
set_shortcut leftHalf "${KEY_1}" "${MOD}"
set_shortcut rightHalf "${KEY_2}" "${MOD}"
set_shortcut centerHalf "${KEY_0}" "${MOD}"
set_shortcut firstThird "${KEY_3}" "${MOD}"
set_shortcut firstFourth "${KEY_4}" "${MOD}"

# Mirrored shortcuts with opt.
set_shortcut lastThird "${KEY_3}" "${MOD_MIRROR}"
set_shortcut lastFourth "${KEY_4}" "${MOD_MIRROR}"

# Restart Rectangle so that it loads the new shortcuts.
start_rectangle
