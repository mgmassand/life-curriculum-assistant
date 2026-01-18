@echo off
echo Creating desktop shortcut...

set SCRIPT_DIR=%~dp0
set SHORTCUT_NAME=Life Curriculum Assistant

:: Create VBS script to make shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\Desktop\%SHORTCUT_NAME%.lnk") >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%SCRIPT_DIR%start.bat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Launch Life Curriculum Assistant" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "C:\Windows\System32\shell32.dll,21" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo.
echo Desktop shortcut created: "%SHORTCUT_NAME%"
echo.
pause
