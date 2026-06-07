@echo off
echo Installing build tools...
pip install pyinstaller pillow pystray requests

echo.
echo Building installer.exe...
pyinstaller --onefile --noconsole --name "JoyAI-Setup" ^
  --add-data "assets;assets" ^
  --icon "assets\logo.png" ^
  installer.py

echo.
echo Building joyai.exe...
pyinstaller --onefile --noconsole --name "JoyAI" ^
  --add-data "assets;assets" ^
  --add-data "push_url.py;." ^
  --icon "assets\logo.png" ^
  joyai.py

echo.
echo Done! Check the dist\ folder.
pause
