# SynthesiaKontrol Project Conventions

## Overview

SynthesiaKontrol lights up Native Instruments Komplete Kontrol keyboard keys driven by Synthesia (piano learning software). It communicates with the keyboard via HID and listens to MIDI messages via LoopBe virtual MIDI port.

## Technical Stack

- Python 3.12+
- cx_Freeze for packaging into standalone Windows executables
- hidapi for USB HID communication with the keyboard
- mido + python-rtmidi for MIDI input
- GitHub Actions for CI/CD (Windows build + release)

## Coding Conventions

- Single-file application: `SynthesiaKontrol.py`
- Use `sys.exit()` for program termination — never use `quit()` or `exit()` (they don't work in frozen cx_Freeze executables)
- Keep keyboard models configurable via the selection menu
- Support both MK1 and MK2 keyboard modes

## Build & Release

- Build with: `python setup.py build`
- The build produces a standalone Windows exe via cx_Freeze
- Releases are triggered by pushing a git tag `v*` (e.g., `git tag v1.5 && git push origin v1.5`)
- GitHub Actions workflow `.github/workflows/build-windows.yml` handles automated builds
- Version number must be updated in `setup.py` before tagging a release

## Dependencies

- All dependencies are in `requirements.txt`
- Pre-built wheels are required for Windows (no C++ compiler expected) — use Python versions with available wheels
- python-rtmidi does NOT have pre-built wheels for Python 3.13+ on Windows — stick to Python 3.12

## Target Platform

- Primary target: Windows (with LoopBe1 virtual MIDI port)
- Secondary: macOS (with IAC MIDI device named "LoopBe")
- The keyboard requires USB HID access (may need "Run as Administrator" on some systems)
