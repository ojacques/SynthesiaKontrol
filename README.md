# Synthesia Kontrol Guide
Use Native Instruments Komplete Kontrol mk2 light guide in Synthesia to learn keyboard.

This is a project for my son, which you may find useful.

# Status

This is work in progress. At this time, I'm figuring out the protocol and a way forward.

# To do

- [X] Proof of concept: light keys from Komplete Kontrol MK2 S61
- [ ] Figure out all the possible colors
- [ ] Python app to listen to midi events from Synthesia and light keys
- [ ] Leverage finger based channel light mode from Synthesia, introduced in r4376 (and withdrawn?) to show left and right hands on KK

# Acknowledgements
Thanks to [AnykeyNL](https://github.com/AnykeyNL) to figure out an initial scheme for Komplete 
Kontrol MK1 USB protocol, and to [Jason Bret](https://github.com/jasonbrent) to have figured out 
the MK2 version, and the `0x81` endpoint which I use in this app.

