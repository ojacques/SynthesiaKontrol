#!/usr/bin/python

# Little tool to figure out Native Instruments Komplete Kontrol mk2 
# simple color scheme on 0x81

import hid
from msvcrt import getch

device=hid.device()
# 0x17cc: Native Instruments. 0x1620: KK S61 MK2
device.open(0x17cc, 0x1620)
device.write([0xa0])

color = 0
while True:
    key = ord(getch())
    if key == 27: #ESC
        break
    elif key == 224: #Special keys (arrows, f keys, ins, del, etc.)
        key = ord(getch())
        if key == 80: #Down arrow
            if color > 0: 
                color -= 1
        elif key == 72: #Up arrow
            if color < 254:
                color += 1

    print("color: ", hex(color))
    device.write([0x81,color,color,color,color,color,color,color])

#           Low, Medium, High, Saturated 
# RED:      0x04, 0x05, 0x06, 0x07
# ORANGE:   0x08, 0x09, 0x0a, 0x0b
# L ORANGE: 0x0c, 0x0d, 0x0e, 0x0f
# YELLOW:   0x10, 0x11, 0x12, 0x13
# YELLOW2:  0x14, 0x15, 0x16, x017
# L GREEN:  0x18, 0x19, 0x1a, 0x1b
# GREEN:    0x1c, 0x1d, 0x1e, 0x1f