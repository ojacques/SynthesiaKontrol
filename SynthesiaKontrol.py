# The MIT License
# 
# Copyright (c) 2018, 2019 Olivier Jacques
# 
# Synthesia Kontrol: an app to light the keys of Native Instruments
#                    Komplete Kontrol MK2 keyboard, driven by Synthesia

import hid
import mido
import time
import sys

NATIVE_INSTRUMENTS = 0x17cc
INSTR_ADDR = 0x1620
NB_KEYS = 61
MODE = "MK2"

def init():
    """Connect to the keyboard, switch all lights off"""
    global bufferC  # Buffer with the full key/lights mapping
    global device

    print("Opening Keyboard device...")
    device=hid.device()
    try:
        device.open(NATIVE_INSTRUMENTS, INSTR_ADDR)
    except Exception as e:
        print("Error: " + str(e))
        quit()

    device.write([0xa0])
    
    bufferC = [0x00] * 249
    notes_off()

    return True

def notes_off():
    """Turn off lights for all notes"""

    print("Turn off lights for all notes")

    bufferC = [0x00] * 249
    if (MODE == "MK2"):
        device.write([0x81] + bufferC)
    elif (MODE == "MK1"):
        device.write([0x82] + bufferC)
    else:
        print ("Error: unsupported mode - should be MK1 or MK2")
        quit()

def accept_notes(port):
    """Only let note_on and note_off messages through."""
    for message in port:
        if message.type in ('note_on', 'note_off'):
            yield message
        if message.type == 'control_change' and message.channel == 0 and message.control == 16:
            if (message.value & 4):
                print ("User is playing")
            if (message.value & 1):
                print ("Playing Right Hand")
            if (message.value & 2):
                print ("Playing Left Hand")
            notes_off()

def CoolDemoSweep(loopcount):
    speed = 0.01
    for loop in range(0,loopcount):
        # Forward
        for x in range(0, NB_KEYS-3):
            if (MODE == "MK2"):
                bufferC = [0x00] * NB_KEYS
                bufferC[0] = 0x81
                bufferC[x] = (0x04 + x % 4)
                bufferC[x+1] = (0x08 + x % 4)
                bufferC[x+2] = (0x0c + x % 4)
                bufferC[x+3] = (0x10 + x % 4)
            else:
                bufferC = [0x00] * 3 * NB_KEYS
                bufferC[0] = 0x82
                bufferC[x*3-2] = 0xFF
            device.write(bufferC)
            time.sleep(speed)
        # Backward
        for x in range(NB_KEYS - 1, 0, -1):
            if (MODE == "MK2"):
                bufferC = [0x00] * NB_KEYS
                bufferC[0] = 0x81
                bufferC[x] = (0x2c + x % 4)
                bufferC[x-1] = (0x2d + x % 4)
                bufferC[x-2] = (0x2e + x % 4)
                bufferC[x-3] = (0x2f + x % 4)
            else:
                bufferC = [0x00] * 3 * NB_KEYS
                bufferC[0] = 0x82
                bufferC[x*3-2] = 0xFF
            device.write(bufferC)
            time.sleep(speed)
    notes_off()
   
def LightNote(note, status, channel, velocity):
    """Light a note ON or OFF"""

    #bufferC[0] = 0x81    # For Komplete Kontrol MK2
    offset = OFFSET
    key = (note + offset)

    if key < 0 or key >= NB_KEYS:
        return  

    # Determine color
    if (MODE == "MK2"):
        left        = 0x2d   # Blue
        left_thumb  = 0x2f   # Lighter Blue
        right       = 0x1d   # Green
        right_thumb = 0x1f   # Lighter Green
    elif (MODE == "MK1"):
        left        = [0x00] + [0x00] + [0xFF]   # Blue
        left_thumb  = [0x00] + [0x00] + [0x80]   # Lighter Blue
        right       = [0x00] + [0xFF] + [0x00]   # Green
        right_thumb = [0x00] + [0x80] + [0x00]   # Lighter Green
    else:
        print ("Error: unsupported mode - should be MK1 or MK2")
        quit()

    default = right
    color = default

    # Finger based channel protocol from Synthesia
    # Reference: https://www.synthesiagame.com/forum/viewtopic.php?p=43585#p43585
    if channel == 0:
        # we don't know who or what this note belongs to, but light something up anyway
        color = default
    if channel >= 1 and channel <= 5:
        # left hand fingers, thumb through pinky
        if channel == 1:
            color = left_thumb
        else:
            color = left
    if channel >= 6 and channel <= 10:
        # right hand fingers, thumb through pinky
        if channel == 6:
            color = right_thumb
        else:
            color = right
    if channel == 11:
        # left hand, unknown finger
        color = left
    if channel == 12:
        # right hand, unknown finger
        color = right

    if status == 'note_on' and velocity != 0:
        if (MODE == "MK2"):
            bufferC[key] = color     # Set color
        else:
            bufferC[3*key:3*key+3] = color
    if (status == 'note_off' or velocity == 0):
        # Note off or velocity 0 (equals note off)
        if (MODE == "MK2"):
            bufferC[key] = 0x00      # Switch key light off
        else:
            bufferC[3*key:3*key+3] = [0x00] * 3

    if (MODE == "MK2"):
        device.write([0x81] + bufferC)
    else:
        device.write([0x82] + bufferC)

if __name__ == '__main__':
    """Main: connect to keyboard, open midi input port, listen to midi"""
    print ("Select your keyboard (1,2,3,...):")
    print ("  1-Komplete Kontrol S61 MK2")
    print ("  2-Komplete Kontrol S88 MK2")
    print ("  3-Komplete Kontrol S49 MK2")
    print ("  4-Komplete Kontrol S61 MK1")
    print ("  5-Komplete Kontrol S88 MK1")
    print ("  6-Komplete Kontrol S49 MK1")
    print ("  7-Komplete Kontrol S25 MK1")
    keyboard = input()
    
    # Customize here for new keyboards
    # Pull requests welcome!
    if keyboard == "1":
        MODE = "MK2"
        INSTR_ADDR = 0x1620 # KK S61 MK2
        NB_KEYS = 61
        OFFSET = -36
    elif keyboard == "2":
        MODE = "MK2"
        INSTR_ADDR = 0x1630 # KK S88 MK2
        NB_KEYS = 88
        OFFSET = -21
    elif keyboard == "3":
        MODE = "MK2"
        INSTR_ADDR = 0x1610 # KK S49 MK2
        NB_KEYS = 49
        OFFSET = -36
    elif keyboard == "4":
        MODE = "MK1"
        INSTR_ADDR = 0x1360 # KK S61 MK1
        NB_KEYS = 61
        OFFSET = -36
    elif keyboard == "5":
        MODE = "MK1"
        INSTR_ADDR = 0x1410 # KK S88 MK1
        NB_KEYS = 88
        OFFSET = -21
    elif keyboard == "6":
        MODE = "MK1"
        INSTR_ADDR = 0x1350 # KK S49 MK1
        NB_KEYS = 49
        OFFSET = -21
    elif keyboard == "7":
        MODE = "MK1"
        INSTR_ADDR = 0x1340 # KK S25 MK1
        NB_KEYS = 25
        OFFSET = -21
    else:
        print ("Sorry, keyboard not supported yet!")
        quit()
    
    print ("Connecting to Komplete Kontrol Keyboard")
    connected = init()
    portName = ""
    if connected:
        print("Connected to Komplete Kontrol!")
        CoolDemoSweep(2)    # Happy dance
        print ("Opening LoopBe input port")
        ports = mido.get_input_names()
        for port in ports:
            print("  Found MIDI port " + port + "...")
            if "LoopBe" in port:
                portName = port
        if portName == "":
            print("Error: can't find 'LoopBe' midi port. Please install LoopBe1 from http://www.nerds.de/en/download.html (Windows) or name your IAC midi device 'LoopBe' (on Mac).")
            exit(1)

        print ("Listening to Midi on LoopBe midi port")
        with mido.open_input(portName) as midiPort:
            for message in accept_notes(midiPort):
                print('Received {}'.format(message))
                LightNote(message.note, message.type, message.channel, message.velocity)
