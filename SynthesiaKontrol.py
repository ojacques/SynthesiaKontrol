# The MIT License
#
# Copyright (c) 2018-2021 Olivier Jacques
#
# Synthesia Kontrol: an app to light the keys of Native Instruments
#                    Komplete Kontrol MK2 keyboard, driven by Synthesia

import os
import sys
import time
import platform
import subprocess
import threading
import hid
import mido

NATIVE_INSTRUMENTS = 0x17cc

# Supported Komplete Kontrol models (USB product id -> config)
KEYBOARDS = {
    0x1620: {
        "name": "Komplete Kontrol S61 MK2",
        "mode": "MK2",
        "keys": 61,
        "offset": -36,
        "menu": "1",
    },
    0x1630: {
        "name": "Komplete Kontrol S88 MK2",
        "mode": "MK2",
        "keys": 88,
        "offset": -21,
        "menu": "2",
    },
    0x1610: {
        "name": "Komplete Kontrol S49 MK2",
        "mode": "MK2",
        "keys": 49,
        "offset": -36,
        "menu": "3",
    },
    0x1360: {
        "name": "Komplete Kontrol S61 MK1",
        "mode": "MK1",
        "keys": 61,
        "offset": -36,
        "menu": "4",
    },
    0x1410: {
        "name": "Komplete Kontrol S88 MK1",
        "mode": "MK1",
        "keys": 88,
        "offset": -21,
        "menu": "5",
    },
    0x1350: {
        "name": "Komplete Kontrol S49 MK1",
        "mode": "MK1",
        "keys": 49,
        "offset": -36,
        "menu": "6",
    },
    0x1340: {
        "name": "Komplete Kontrol S25 MK1",
        "mode": "MK1",
        "keys": 25,
        "offset": -21,
        "menu": "7",
    },
}

# Menu number -> product id (for manual fallback)
MENU_TO_PID = {cfg["menu"]: pid for pid, cfg in KEYBOARDS.items()}

# Runtime state set after keyboard selection
MODE = "MK2"
INSTR_ADDR = 0x1620
NB_KEYS = 61
OFFSET = -36
KEYBOARD_NAME = ""


# ---------------------------------------------------------------------------
# Terminal styling
# ---------------------------------------------------------------------------

class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    # Foreground
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def enable_ansi():
    """Enable ANSI colors on Windows consoles when possible."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        pass
    # Also helps some older Windows terminals
    os.system("")


def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")


def print_banner():
    bar = f"{Style.CYAN}{'─' * 56}{Style.RESET}"
    print()
    print(bar)
    print(
        f"{Style.BOLD}{Style.CYAN}  ♪  SynthesiaKontrol{Style.RESET}"
        f"{Style.DIM}  ·  light guide bridge{Style.RESET}"
    )
    print(bar)
    print()


def status_line(label, ok, ok_text, bad_text, detail=""):
    if ok:
        badge = f"{Style.GREEN}{Style.BOLD}● ON {Style.RESET}"
        text = f"{Style.GREEN}{ok_text}{Style.RESET}"
    else:
        badge = f"{Style.RED}{Style.BOLD}● OFF{Style.RESET}"
        text = f"{Style.YELLOW}{bad_text}{Style.RESET}"
    extra = f"  {Style.DIM}{detail}{Style.RESET}" if detail else ""
    print(f"  {badge}  {Style.BOLD}{label:<14}{Style.RESET} {text}{extra}")


def info(msg):
    print(f"  {Style.BLUE}ℹ{Style.RESET}  {msg}")


def success(msg):
    print(f"  {Style.GREEN}✓{Style.RESET}  {msg}")


def warn(msg):
    print(f"  {Style.YELLOW}!{Style.RESET}  {msg}")


def error(msg):
    print(f"  {Style.RED}✗{Style.RESET}  {msg}")


def section(title):
    print(f"  {Style.DIM}── {title} {'─' * max(1, 40 - len(title))}{Style.RESET}")


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def detect_keyboards():
    """Return unique supported keyboards currently connected via USB HID."""
    found = {}
    try:
        for dev in hid.enumerate(NATIVE_INSTRUMENTS):
            pid = dev.get("product_id")
            if pid in KEYBOARDS and pid not in found:
                cfg = KEYBOARDS[pid].copy()
                cfg["product_id"] = pid
                # Prefer non-empty product string from USB
                product = (dev.get("product_string") or "").strip()
                if product:
                    cfg["usb_name"] = product
                found[pid] = cfg
    except Exception as e:
        warn(f"USB enumeration failed: {e}")
    return list(found.values())


def is_synthesia_running():
    """Return True if a Synthesia process is running."""
    system = platform.system()
    try:
        if system == "Windows":
            # tasklist is available on all modern Windows installs
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Synthesia.exe", "/NH"],
                capture_output=True,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            out = (result.stdout or "").lower()
            return "synthesia.exe" in out
        else:
            # macOS / Linux
            result = subprocess.run(
                ["pgrep", "-if", "synthesia"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0 and bool((result.stdout or "").strip())
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


def apply_keyboard_config(cfg):
    global MODE, INSTR_ADDR, NB_KEYS, OFFSET, KEYBOARD_NAME
    MODE = cfg["mode"]
    INSTR_ADDR = cfg["product_id"]
    NB_KEYS = cfg["keys"]
    OFFSET = cfg["offset"]
    KEYBOARD_NAME = cfg["name"]


def select_keyboard():
    """Auto-detect keyboard, or fall back to interactive menu."""
    section("Keyboard")
    detected = detect_keyboards()

    if len(detected) == 1:
        cfg = detected[0]
        apply_keyboard_config(cfg)
        success(f"Auto-detected: {Style.BOLD}{cfg['name']}{Style.RESET}")
        usb = cfg.get("usb_name")
        if usb and usb != cfg["name"]:
            info(f"USB reports: {Style.DIM}{usb}{Style.RESET}")
        info(
            f"{cfg['keys']} keys · {cfg['mode']} · "
            f"USB {Style.DIM}0x{cfg['product_id']:04x}{Style.RESET}"
        )
        return True

    if len(detected) > 1:
        warn("Several supported keyboards found — pick one:")
        print()
        for i, cfg in enumerate(detected, start=1):
            print(
                f"     {Style.CYAN}{i}{Style.RESET}) "
                f"{cfg['name']}  {Style.DIM}(0x{cfg['product_id']:04x}){Style.RESET}"
            )
        print()
        choice = input(f"  {Style.BOLD}Your choice:{Style.RESET} ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(detected):
                apply_keyboard_config(detected[idx])
                success(f"Selected: {Style.BOLD}{KEYBOARD_NAME}{Style.RESET}")
                return True
        except ValueError:
            pass
        error("Invalid selection.")
        return False

    # Nothing detected — manual menu
    warn("No Komplete Kontrol keyboard detected over USB.")
    info("Plug it in, or choose a model manually:")
    print()
    # Stable menu order by menu number
    ordered = sorted(KEYBOARDS.items(), key=lambda item: int(item[1]["menu"]))
    for pid, cfg in ordered:
        print(
            f"     {Style.CYAN}{cfg['menu']}{Style.RESET}) {cfg['name']}"
            f"  {Style.DIM}MK{cfg['mode'][-1]} · {cfg['keys']} keys{Style.RESET}"
        )
    print()
    choice = input(f"  {Style.BOLD}Your choice:{Style.RESET} ").strip()
    if choice not in MENU_TO_PID:
        error(
            f"Got '{choice}' — please type a number from the list, then Enter."
        )
        return False
    pid = MENU_TO_PID[choice]
    cfg = KEYBOARDS[pid].copy()
    cfg["product_id"] = pid
    apply_keyboard_config(cfg)
    success(f"Selected: {Style.BOLD}{KEYBOARD_NAME}{Style.RESET}")
    return True


def print_status_panel():
    """Print Synthesia / LoopBe / Keyboard status block."""
    section("Status")
    synth_ok = is_synthesia_running()
    loopbe = find_loopbe_port()
    loopbe_ok = bool(loopbe)

    status_line(
        "Synthesia",
        synth_ok,
        "running",
        "not running — start the game",
    )
    status_line(
        "LoopBe MIDI",
        loopbe_ok,
        "connected",
        "port not found (install LoopBe1)",
        detail=loopbe if loopbe_ok else "",
    )
    status_line(
        "Keyboard",
        bool(KEYBOARD_NAME),
        KEYBOARD_NAME or "selected",
        "not selected",
    )
    print()
    if not synth_ok:
        info(
            f"Launch {Style.BOLD}Synthesia{Style.RESET}, then set Music Output → "
            f"{Style.CYAN}LoopBe{Style.RESET} with "
            f"{Style.CYAN}Finger-based channel{Style.RESET}."
        )
        print()
    return synth_ok, loopbe


# ---------------------------------------------------------------------------
# Device / lighting
# ---------------------------------------------------------------------------

def init():
    """Connect to the keyboard, switch all lights off."""
    global bufferC, device

    info(f"Opening {Style.BOLD}{KEYBOARD_NAME}{Style.RESET}…")
    device = hid.device()
    try:
        device.open(NATIVE_INSTRUMENTS, INSTR_ADDR)
    except Exception as e:
        error(f"Could not open keyboard: {e}")
        error("Is it plugged in and not used by another app?")
        sys.exit(1)

    # Enter light-guide mode (thanks @xample)
    device.write([0xA0, 0x00, 0x00])

    bufferC = [0x00] * 249
    notes_off()
    return True


def notes_off():
    """Turn off lights for all notes."""
    global bufferC
    bufferC = [0x00] * 249
    if MODE == "MK2":
        device.write([0x81] + bufferC)
    elif MODE == "MK1":
        device.write([0x82] + bufferC)
    else:
        error("Unsupported mode — should be MK1 or MK2")
        sys.exit(1)


def accept_notes(port):
    """Only let note_on and note_off messages through."""
    for message in port:
        if message.type in ("note_on", "note_off"):
            yield message
        if (
            message.type == "control_change"
            and message.channel == 0
            and message.control == 16
        ):
            flags = []
            if message.value & 4:
                flags.append("user playing")
            if message.value & 1:
                flags.append("right hand")
            if message.value & 2:
                flags.append("left hand")
            if flags:
                info(f"Synthesia: {Style.MAGENTA}{', '.join(flags)}{Style.RESET}")
            notes_off()


def CoolDemoSweep(loopcount):
    speed = 0.01
    for _ in range(loopcount):
        # Forward
        for x in range(0, NB_KEYS - 3):
            if MODE == "MK2":
                buf = [0x00] * NB_KEYS
                buf[0] = 0x81
                buf[x] = 0x04 + x % 4
                buf[x + 1] = 0x08 + x % 4
                buf[x + 2] = 0x0C + x % 4
                buf[x + 3] = 0x10 + x % 4
            else:
                buf = [0x00] * 3 * NB_KEYS
                buf[0] = 0x82
                buf[x * 3 - 2] = 0xFF
            device.write(buf)
            time.sleep(speed)
        # Backward
        for x in range(NB_KEYS - 1, 0, -1):
            if MODE == "MK2":
                buf = [0x00] * NB_KEYS
                buf[0] = 0x81
                buf[x] = 0x2C + x % 4
                buf[x - 1] = 0x2D + x % 4
                buf[x - 2] = 0x2E + x % 4
                buf[x - 3] = 0x2F + x % 4
            else:
                buf = [0x00] * 3 * NB_KEYS
                buf[0] = 0x82
                buf[x * 3 - 2] = 0xFF
            device.write(buf)
            time.sleep(speed)
    notes_off()


def LightNote(note, status, channel, velocity):
    """Light a note ON or OFF."""
    key = note + OFFSET
    if key < 0 or key >= NB_KEYS:
        return

    if MODE == "MK2":
        left = 0x2D          # Blue
        left_thumb = 0x2F    # Lighter Blue
        right = 0x1D         # Green
        right_thumb = 0x1F   # Lighter Green
    elif MODE == "MK1":
        left = [0x00, 0x00, 0xFF]
        left_thumb = [0x00, 0x00, 0x80]
        right = [0x00, 0xFF, 0x00]
        right_thumb = [0x00, 0x80, 0x00]
    else:
        error("Unsupported mode — should be MK1 or MK2")
        sys.exit(1)

    color = right  # default

    # Finger-based channel protocol from Synthesia
    # https://www.synthesiagame.com/forum/viewtopic.php?p=43585#p43585
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

    if status == "note_on" and velocity != 0:
        if MODE == "MK2":
            bufferC[key] = color
        else:
            bufferC[3 * key : 3 * key + 3] = color
    if status == "note_off" or velocity == 0:
        if MODE == "MK2":
            bufferC[key] = 0x00
        else:
            bufferC[3 * key : 3 * key + 3] = [0x00, 0x00, 0x00]

    if MODE == "MK2":
        device.write([0x81] + bufferC)
    else:
        device.write([0x82] + bufferC)


# ---------------------------------------------------------------------------
# Background Synthesia watcher
# ---------------------------------------------------------------------------

class SynthesiaWatcher(threading.Thread):
    """Poll whether Synthesia is running and print changes."""

    def __init__(self, interval=3.0):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop = threading.Event()
        self._last = None

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            running = is_synthesia_running()
            if self._last is None:
                self._last = running
            elif running != self._last:
                self._last = running
                if running:
                    success(
                        f"Synthesia {Style.GREEN}started{Style.RESET} — light guide active"
                    )
                else:
                    warn(
                        f"Synthesia {Style.YELLOW}closed{Style.RESET} — waiting for it to launch…"
                    )
                    try:
                        notes_off()
                    except Exception:
                        pass
            self._stop.wait(self.interval)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    enable_ansi()
    clear_screen()
    print_banner()

    if not select_keyboard():
        sys.exit(1)

    print()
    synth_ok, loopbe_port = print_status_panel()

    section("Connect")
    init()
    success(f"Connected to {Style.BOLD}{KEYBOARD_NAME}{Style.RESET}")
    info("Startup light sweep…")
    CoolDemoSweep(2)
    success("Keyboard ready")
    print()

    if not loopbe_port:
        # Re-check once more after connection phase
        loopbe_port = find_loopbe_port()

    if not loopbe_port:
        error("Can't find a MIDI port with 'LoopBe' in the name.")
        info(
            "Install LoopBe1: "
            f"{Style.CYAN}http://www.nerds.de/en/download.html{Style.RESET} (Windows)"
        )
        info(
            "Or name your IAC device "
            f"{Style.CYAN}LoopBe{Style.RESET} (macOS)."
        )
        sys.exit(1)

    section("Listening")
    success(f"MIDI input: {Style.BOLD}{loopbe_port}{Style.RESET}")
    if synth_ok:
        success("Synthesia is running — play a song to light the keys")
    else:
        warn("Synthesia is not running yet — start it when you're ready")
    info("Press Ctrl+C to quit")
    print()
    print(f"  {Style.DIM}{'─' * 56}{Style.RESET}")
    print()

    watcher = SynthesiaWatcher(interval=3.0)
    watcher.start()

    try:
        with mido.open_input(loopbe_port) as midi_port:
            for message in accept_notes(midi_port):
                hand = ""
                ch = message.channel
                if 1 <= ch <= 5 or ch == 11:
                    hand = f"{Style.BLUE}L{Style.RESET}"
                elif 6 <= ch <= 10 or ch == 12:
                    hand = f"{Style.GREEN}R{Style.RESET}"
                else:
                    hand = f"{Style.GRAY}?{Style.RESET}"

                on = message.type == "note_on" and message.velocity != 0
                state = (
                    f"{Style.GREEN}ON {Style.RESET}"
                    if on
                    else f"{Style.DIM}off{Style.RESET}"
                )
                print(
                    f"  {hand}  note {Style.BOLD}{message.note:>3}{Style.RESET}  "
                    f"{state}  {Style.DIM}ch{ch} vel{message.velocity}{Style.RESET}"
                )
                LightNote(
                    message.note,
                    message.type,
                    message.channel,
                    message.velocity,
                )
    except KeyboardInterrupt:
        print()
        info("Shutting down…")
    finally:
        watcher.stop()
        try:
            notes_off()
        except Exception:
            pass
        success("Bye!")
        print()
