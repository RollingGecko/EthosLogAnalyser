@echo off
rem Builds dist\EthosLogAnalyser.exe with PyInstaller.
rem Activate a virtual environment first (see docs\usage.md).

cd /d "%~dp0.."
python -m pip install -e ".[build]" || exit /b 1
pyinstaller --noconfirm --onefile --windowed --name EthosLogAnalyser --paths src src\ethosloganalyser\__main__.py || exit /b 1
echo.
echo Done: dist\EthosLogAnalyser.exe
