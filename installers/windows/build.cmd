@echo off
rem Developer build: produces dist\Haste2Battery-Setup.exe (end users do NOT need this or Python).
setlocal
cd /d "%~dp0\..\.."
set "PY=py"
where py >nul 2>&1 || set "PY=python"
%PY% -m venv build\venv || goto :fail
build\venv\Scripts\python.exe -m pip install --only-binary=:all: hidapi==0.15.0 pystray==0.19.5 "Pillow>=10.1,<14" "pyinstaller>=6.11,<7" || goto :fail
build\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name Haste2Battery-Setup ^
  --icon assets\haste2.ico --version-file installers\windows\version_info.txt ^
  --hidden-import pystray._win32 --paths src ^
  --workpath build\pyinstaller --specpath build installers\windows\launcher.pyw || goto :fail
echo.
echo Done: dist\Haste2Battery-Setup.exe
pause
exit /b 0
:fail
echo.
echo BUILD FAILED
pause
exit /b 1
