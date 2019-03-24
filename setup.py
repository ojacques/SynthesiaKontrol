from cx_Freeze import setup, Executable
   
executables = [
        Executable("SynthesiaKontrol.py")
]
   
buildOptions = dict(
        includes = ["mido.backends.rtmidi"]
)
   
setup(
    name = "SynthesiaKontrol",
    version = "1.1",
    description = "Use Komplete Kontrol Keyboard lights in Synthesia",
    options = dict(build_exe = buildOptions),
    executables = executables
)