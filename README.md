# Synthesia Kontrol Guide
Use Native Instruments Komplete Kontrol mk2 light guide in Synthesia to learn keyboard.

[![Synthesia Kontrol](https://img.youtube.com/vi/R143-vSd6Eg/0.jpg)](https://www.youtube.com/watch?v=R143-vSd6Eg)

This is a project for my son, which you may find useful.

This program listens to light events from Synthesia sent to a virtual `LoopBe1` midi port
and lights the keys on Komplete Kontrol keyboard accordingly.

# Install

## Pre-requisites

- Install [LoopBe1](http://www.nerds.de/en/download.html) virtual midi port driver.
- In [Synthesia](https://synthesiagame.com):
  - Go to settings/Music Devices
  - Select "nerds.de LoopBe1" from "Music Output"
  - In Keylight section of that output, select "Finger-based channel" (the last mode after 'channel 16')

## SynthesiaKontrol

### Windows

- Download the Windows package locally on your PC from [releases](https://github.com/ojacques/SynthesiaKontrol/releases/)
- Extract in a new folder
- Run SynthesiaKontrol

### Linux, MAC

Use the [Developer method](#developer).

# Developer

If you want to contribute to the project, you need to setup your Python environment.

## SynthesiaKontrol

- Install Python's module:

```
pip install hidapi
pip install mido
```

- Run the program: 

```
python SynthesiaKontrol.py
```

- Build executable:

```
python setup.py build
```

Result is in build directory.

# Status

- [X] Proof of concept: light keys from Komplete Kontrol MK2 S61
- [X] Figure out all the possible colors - see `color_scan.py`
- [X] Python app to listen to midi events from Synthesia and light keys - see `SynthesiaKontrol.py`
- [X] Leverage finger based channel light mode from Synthesia, introduced in r4376 to show left and right hands on KK
- [X] Address issue where notes are turned off too quickly (Forum post [here](https://www.synthesiagame.com/forum/viewtopic.php?p=45032#p45032))
- [X] Package as simple executable
- [ ] All notes off
- [ ] Customizable note colors
- [ ] Simpler / better instructions
- [ ] Support all Komplete Kontrol MK2 keyboard sizes (currently only S61)
- [ ] Support Komplete Kontrol MK1 keyboards
- [ ] Use different colors per channel

# Getting help

I prefer [GitHub issues](https://github.com/ojacques/SynthesiaKontrol/issues).
Otherwise, there is a Synthesia forum thread [here](https://www.synthesiagame.com/forum/viewtopic.php?f=16&t=9220).

# Acknowledgements
Thanks to
- [Nicholas Piegdon](https://github.com/npiegdon) for his dedication to Synthesia, and the great help he provides for his user community
- [AnykeyNL](https://github.com/AnykeyNL) to figure out an initial scheme for Komplete 
Kontrol MK1 USB protocol as well as the structure of an app
- [Jason Bret](https://github.com/jasonbrent) to have figured out the MK2 version, and the `0x81` endpoint which I use.

