# Synthesia Kontrol Guide
Use Native Instruments Komplete Kontrol MK1 and MK2 light guide in Synthesia to learn keyboard.

[![Synthesia Kontrol](https://img.youtube.com/vi/R143-vSd6Eg/0.jpg)](https://www.youtube.com/watch?v=R143-vSd6Eg)

This is a project for my son, which you may find useful.

This program listens to light events from Synthesia sent to a virtual `LoopBe1` midi port
and lights the keys on Komplete Kontrol keyboard accordingly.

# Install

## Pre-requisites

- Install [LoopBe1](http://www.nerds.de/en/download.html) virtual midi port driver.

  💡 On Mac, you can use the built in "IAC Driver" - open "Audio midi setup" to create a device named "LoopBe" as [explained by D-One](https://www.youtube.com/watch?v=8fCx9_58kjU&t=220)

  **🆕New**: Since January 2023, check out [KompleteSynthesia](https://github.com/tillt/KompleteSynthesia): a MAC native project from [@tillt](https://github.com/tillt)
- In [Synthesia](https://synthesiagame.com):
  - Go to settings/Music Devices
  - Select "LoopBe Internal MIDI" from "Music Output"
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

⚠ SynthesiaKontrol only works with Python3. One of the symptom when using Python2 is that you will get an error message saying that the keyboard is not supported yet.

## SynthesiaKontrol

- Install Python's module:

```
pip3 install -r requirements.txt
```

- Run the program: 

```
python3 SynthesiaKontrol.py
```

- Build executable (Windows)

  - Install cx_Freeze: `pip3 install cx_Freeze`
  - Run build
    ```
    python3 setup.py build
    ```
  - Result is in build directory.

# Status

- [X] Proof of concept: light keys from Komplete Kontrol MK2 S61
- [X] Figure out all the possible colors - see `color_scan.py`
- [X] Python app to listen to midi events from Synthesia and light keys - see `SynthesiaKontrol.py`
- [X] Leverage finger based channel light mode from Synthesia, introduced in r4376 to show left and right hands on KK
- [X] Address issue where notes are turned off too quickly (Forum post [here](https://www.synthesiagame.com/forum/viewtopic.php?p=45032#p45032))
- [X] Package as simple executable
- [X] All notes off
- [ ] Customizable note colors
- [ ] Rainbow mode: when playing a note, make a rainbow on that note
- [X] Simpler / better instructions
- [X] Support all Komplete Kontrol MK2 keyboard sizes (currently only S61)
- [X] Support Komplete Kontrol MK1 keyboards
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
- [a1vv](https://github.com/a1vv/KompleteKontrolLightGuide) for the fork, and figuring out the changes for MK1 - which allowed me to create a version with support of MK1 and MK2
- [Nabume](https://www.synthesiagame.com/forum/memberlist.php?mode=viewprofile&u=115379) for the S88 MK2 info.
- [KompleteSynthesia](https://github.com/tillt/KompleteSynthesia): a MAC native project from @tillt
