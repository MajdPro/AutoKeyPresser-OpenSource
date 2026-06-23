@echo off
cd /d "%~dp0"
title Building Auto Key Presser...

echo Installing required packages...
pip install -U nuitka ordered-set zstandard keyboard pyautogui PyQt6

echo.
echo Building executable...
echo Please wait, this may take a few minutes during the linking stage...
echo.

python -m nuitka ^
--onefile ^
--enable-plugin=pyqt6 ^
--windows-console-mode=disable ^
--company-name="Majd Pro" ^
--product-name="Auto Key Presser" ^
--file-version=1.0.0 ^
--product-version=1.0.0 ^
--file-description="Professional Auto Key Presser" ^
--copyright="Copyright 2026" ^
main.py

echo.
echo Build complete!
pause