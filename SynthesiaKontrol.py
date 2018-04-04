# The MIT License
# 
# Copyright (c) 2018 Olivier Jacques
# 
# Synthesia Kontrol: an app to light the keys of Native Instruments
#                    Komplete Kontrol MK2 keyboard, driven by Synthesia

import hid
import mido
from msvcrt import getch

def init():
    """Connect to the keyboard, switch all lights off"""
    global bufferC  # Buffer with the full key/lights mapping
    global device

    device=hid.device()
    # 0x17cc: Native Instruments. 0x1620: KK S61 MK2
    device.open(0x17cc, 0x1620)
    device.write([0xa0])

    # Turn off lights for all 61 notes
    bufferC = [0x00] * 61
    device.write([0x81] + bufferC)

    return True

def accept_notes(port):
    """Only let note_on and note_off messages through."""
    for message in port:
        if message.type in ('note_on', 'note_off'):
            yield message

def LightNote(note, status, channel):
    """Light a note ON or OFF"""

    bufferC[0] = 0x81    # For Komplete Kontrol MK2
    offset = -36         # To change when keyboard is not 61 keys
    key = (note + offset) 

    # Determine color
    left        = 0x2d   # Blue
    left_thumb  = 0x2f   # Lighter Blue
    right       = 0x1d   # Green
    right_thumb = 0x1f   # Lighter Green
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

    if status == 'note_on':
        bufferC[key] = color     # Set color
    if status == 'note_off':
        bufferC[key] = 0x00      # Switch key light off
    device.write([0x81] + bufferC)

if __name__ == '__main__':
    """Main: connect to keyboard, open midi input port, listen to midi"""
    print ("Connecting to Komplete Kontrol Keyboard")
    connected = init()
    if connected:
        print ("Opening LoopBe input port")
        ports = mido.get_input_names()
        for port in ports:
            if "LoopBe" in port:
                portName = port
        print ("Listening to Midi")
        with mido.open_input(portName) as midiPort:
            for message in accept_notes(midiPort):
                print('Received {}'.format(message))
                LightNote(message.note, message.type, message.channel)