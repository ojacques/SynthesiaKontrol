@echo off
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
  py -3 SynthesiaKontrol.py
) else (
  python SynthesiaKontrol.py
)

echo.
echo ---- Program finished. Press any key to close. ----
pause >nul
