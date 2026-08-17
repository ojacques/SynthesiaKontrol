# The MIT License
#
# Copyright (c) 2018-2025 Olivier Jacques
#
# Synthesia Kontrol: an app to light the keys of Native Instruments
#                    Komplete Kontrol MK2 keyboard, driven by Synthesia

import os
import sys
import time
import signal
import platform
import subprocess
import hid
import mido

NATIVE_INSTRUMENTS = 0x17cc

# ---------------------------------------------------------------------------
# Supported keyboards: product_id -> config
# To add a new model, add a single entry here.
# ---------------------------------------------------------------------------
KEYBOARDS = {
    0x1620: {"name": "Komplete Kontrol S61 MK2", "mode": "MK2", "keys": 61, "offset": -36, "menu": "1"},
    0x1630: {"name": "Komplete Kontrol S88 MK2", "mode": "MK2", "keys": 88, "offset": -21, "menu": "2"},
    0x1610: {"name": "Komplete Kontrol S49 MK2", "mode": "MK2", "keys": 49, "offset": -36, "menu": "3"},
    0x1360: {"name": "Komplete Kontrol S61 MK1", "mode": "MK1", "keys": 61, "offset": -36, "menu": "4"},
    0x1410: {"name": "Komplete Kontrol S88 MK1", "mode": "MK1", "keys": 88, "offset": -21, "menu": "5"},
    0x1350: {"name": "Komplete Kontrol S49 MK1", "mode": "MK1", "keys": 49, "offset": -36, "menu": "6"},
    0x1340: {"name": "Komplete Kontrol S25 MK1", "mode": "MK1", "keys": 25, "offset": -21, "menu": "7"},
}

MENU_TO_PID = {cfg["menu"]: pid for pid, cfg in KEYBOARDS.items()}

# Runtime state (set after keyboard selection)
MODE = "MK2"
INSTR_ADDR = 0x1620
NB_KEYS = 61
OFFSET = -36
device = None
bufferC = None


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------

def detect_keyboards():
    """Return list of supported keyboards currently connected via USB HID."""
    found = {}
    try:
        for dev in hid.enumerate(NATIVE_INSTRUMENTS):
            pid = dev.get("product_id")
            if pid in KEYBOARDS and pid not in found:
                cfg = KEYBOARDS[pid].copy()
                cfg["product_id"] = pid
                found[pid] = cfg
    except Exception:
        pass
    return list(found.values())


def apply_keyboard_config(cfg):
    """Apply a keyboard config dict to global state."""
    global MODE, INSTR_ADDR, NB_KEYS, OFFSET
    MODE = cfg["mode"]
    INSTR_ADDR = cfg["product_id"]
    NB_KEYS = cfg["keys"]
    OFFSET = cfg["offset"]


def select_keyboard():
    """Auto-detect keyboard or fall back to interactive menu."""
    detected = detect_keyboards()

    if len(detected) == 1:
        cfg = detected[0]
        apply_keyboard_config(cfg)
        print(f"  Auto-detected: {cfg['name']} ({cfg['keys']} keys, {cfg['mode']})")
        return True

    if len(detected) > 1:
        print("  Multiple keyboards found — pick one:")
        for i, cfg in enumerate(detected, start=1):
            print(f"    {i}) {cfg['name']}")
        choice = input("  Your choice: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(detected):
                apply_keyboard_config(detected[idx])
                return True
        except ValueError:
            pass
        print("  Invalid selection.")
        return False

    # Nothing detected — manual menu (same as before)
    print("Select your keyboard (1, 2, 3, ...) and press 'Enter':")
    for pid, cfg in sorted(KEYBOARDS.items(), key=lambda x: int(x[1]["menu"])):
        print(f"  {cfg['menu']}-{cfg['name']}")
    keyboard = input()

    if keyboard in MENU_TO_PID:
        pid = MENU_TO_PID[keyboard]
        cfg = KEYBOARDS[pid].copy()
        cfg["product_id"] = pid
        apply_keyboard_config(cfg)
        return True
    else:
        print("Got '" + keyboard +
              "' - please type a number which corresponds to your keyboard, then Enter")
        return False


# ---------------------------------------------------------------------------
# Status checks
# ---------------------------------------------------------------------------

def is_synthesia_running():
    """Return True if a Synthesia process is running."""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Synthesia.exe", "/NH"],
                capture_output=True, text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return "synthesia.exe" in (result.stdout or "").lower()
        else:
            result = subprocess.run(
                ["pgrep", "-if", "synthesia"],
                capture_output=True, text=True,
            )
            return result.returncode == 0
    except Exception:
        return False


def find_loopbe_port():
    """Return LoopBe MIDI input port name, or empty string if not found."""
    try:
        for port in mido.get_input_names():
            if "LoopBe" in port:
                return port
    except Exception:
        pass
    return ""


def print_status():
    """Print startup status panel."""
    print()
    print("── Status ──────────────────────────────────────────")
    synth = is_synthesia_running()
    loopbe = find_loopbe_port()
    print(f"  Synthesia:  {'running' if synth else 'NOT running'}")
    print(f"  LoopBe:     {loopbe if loopbe else 'NOT found'}")
    print(f"  Keyboard:   {KEYBOARDS.get(INSTR_ADDR, {}).get('name', 'Unknown')}")
    print("────────────────────────────────────────────────────")
    if not synth:
        print()
        print("  Tip: Start Synthesia, set Music Output -> LoopBe")
        print("       with 'Finger-based channel' key lights.")
    print()
    return loopbe


# ---------------------------------------------------------------------------
# Device / lighting
# ---------------------------------------------------------------------------

def init():
    """Connect to the keyboard, switch all lights off."""
    global bufferC, device

    print("Opening Keyboard device...")
    device = hid.device()
    try:
        device.open(NATIVE_INSTRUMENTS, INSTR_ADDR)
    except Exception as e:
        print("Error: " + str(e))
        sys.exit(1)

    # Enter light-guide mode (thanks @xample)
    device.write([0xa0, 0x00, 0x00])

    bufferC = [0x00] * (3 * NB_KEYS if MODE == "MK1" else NB_KEYS)
    notes_off()

    return True


def notes_off():
    """Turn off lights for all notes."""
    global bufferC
    bufferC = [0x00] * (3 * NB_KEYS if MODE == "MK1" else NB_KEYS)
    if MODE == "MK2":
        device.write([0x81] + bufferC)
    elif MODE == "MK1":
        device.write([0x82] + bufferC)
    else:
        print("Error: unsupported mode - should be MK1 or MK2")
        sys.exit(1)


def shutdown(signum=None, frame=None):
    """Graceful shutdown: turn lights off and exit."""
    print()
    print("Shutting down — lights off...")
    try:
        notes_off()
    except Exception:
        pass
    print("Bye!")
    sys.exit(0)


def accept_notes(port):
    """Only let note_on and note_off messages through."""
    for message in port:
        if message.type in ('note_on', 'note_off'):
            yield message
        if message.type == 'control_change' and message.channel == 0 and message.control == 16:
            if (message.value & 4):
                print("User is playing")
            if (message.value & 1):
                print("Playing Right Hand")
            if (message.value & 2):
                print("Playing Left Hand")
            notes_off()


def CoolDemoSweep(loopcount):
    """Startup light sweep animation."""
    speed = 0.01
    for _ in range(loopcount):
        # Forward
        for x in range(0, NB_KEYS - 3):
            if MODE == "MK2":
                buf = [0x00] * NB_KEYS
                buf[x] = 0x04 + x % 4
                buf[x + 1] = 0x08 + x % 4
                buf[x + 2] = 0x0c + x % 4
                buf[x + 3] = 0x10 + x % 4
                device.write([0x81] + buf)
            else:
                buf = [0x00] * (3 * NB_KEYS)
                buf[x * 3] = 0xFF
                device.write([0x82] + buf)
            time.sleep(speed)
        # Backward
        for x in range(NB_KEYS - 1, 0, -1):
            if MODE == "MK2":
                buf = [0x00] * NB_KEYS
                buf[x] = 0x2c + x % 4
                buf[x - 1] = 0x2d + x % 4
                buf[x - 2] = 0x2e + x % 4
                buf[x - 3] = 0x2f + x % 4
                device.write([0x81] + buf)
            else:
                buf = [0x00] * (3 * NB_KEYS)
                buf[x * 3] = 0xFF
                device.write([0x82] + buf)
            time.sleep(speed)
    notes_off()


def LightNote(note, status, channel, velocity):
    """Light a note ON or OFF."""
    key = note + OFFSET

    if key < 0 or key >= NB_KEYS:
        return

    # Determine color
    if MODE == "MK2":
        left = 0x2d        # Blue
        left_thumb = 0x2f  # Lighter Blue
        right = 0x1d       # Green
        right_thumb = 0x1f # Lighter Green
    elif MODE == "MK1":
        left = [0x00, 0x00, 0xFF]        # Blue
        left_thumb = [0x00, 0x00, 0x80]  # Lighter Blue
        right = [0x00, 0xFF, 0x00]       # Green
        right_thumb = [0x00, 0x80, 0x00] # Lighter Green
    else:
        print("Error: unsupported mode - should be MK1 or MK2")
        sys.exit(1)

    color = right  # default

    # Finger-based channel protocol from Synthesia
    # Reference: https://www.synthesiagame.com/forum/viewtopic.php?p=43585#p43585
    if channel == 0:
        color = right
    elif 1 <= channel <= 5:
        color = left_thumb if channel == 1 else left
    elif 6 <= channel <= 10:
        color = right_thumb if channel == 6 else right
    elif channel == 11:
        color = left
    elif channel == 12:
        color = right

    if status == 'note_on' and velocity != 0:
        if MODE == "MK2":
            bufferC[key] = color
        else:
            bufferC[3 * key:3 * key + 3] = color
    if status == 'note_off' or velocity == 0:
        if MODE == "MK2":
            bufferC[key] = 0x00
        else:
            bufferC[3 * key:3 * key + 3] = [0x00] * 3

    if MODE == "MK2":
        device.write([0x81] + bufferC)
    else:
        device.write([0x82] + bufferC)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("SynthesiaKontrol — Komplete Kontrol light guide bridge")
    print()

    # Select keyboard (auto-detect or manual)
    if not select_keyboard():
        sys.exit(1)

    # Show status
    loopbe_port = print_status()

    # Connect to keyboard
    print("Connecting to Komplete Kontrol Keyboard")
    connected = init()

    if connected:
        # Register graceful shutdown (Ctrl+C)
        signal.signal(signal.SIGINT, shutdown)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, shutdown)

        print("Connected to Komplete Kontrol!")
        CoolDemoSweep(2)    # Happy dance

        # Find LoopBe port
        if not loopbe_port:
            loopbe_port = find_loopbe_port()
        if not loopbe_port:
            print("Error: can't find 'LoopBe' midi port.")
            print("  Install LoopBe1: http://www.nerds.de/en/download.html (Windows)")
            print("  Or name your IAC midi device 'LoopBe' (macOS).")
            sys.exit(1)

        print(f"Listening to MIDI on: {loopbe_port}")
        print("Press Ctrl+C to quit.")
        print()

        try:
            with mido.open_input(loopbe_port) as midiPort:
                for message in accept_notes(midiPort):
                    print('Received {}'.format(message))
                    LightNote(message.note, message.type,
                              message.channel, message.velocity)
        except KeyboardInterrupt:
            shutdown()
