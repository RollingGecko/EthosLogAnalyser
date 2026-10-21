@echo off
rem Baut dist\EthosLogAnalyser.exe mit PyInstaller.
rem Am besten vorher eine virtuelle Umgebung aktivieren (siehe docs\benutzung.md).

cd /d "%~dp0.."
python -m pip install -e ".[build]" || exit /b 1
pyinstaller --noconfirm --onefile --windowed --name EthosLogAnalyser --paths src src\ethosloganalyser\__main__.py || exit /b 1
echo.
echo Fertig: dist\EthosLogAnalyser.exe
