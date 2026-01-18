@echo off
echo Adding to Windows Startup...

set SCRIPT_DIR=%~dp0
set SHORTCUT_NAME=Life Curriculum Assistant
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

:: Create VBS script to make shortcut in Startup folder
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateStartup.vbs"
echo sLinkFile = "%STARTUP_FOLDER%\%SHORTCUT_NAME%.lnk" >> "%TEMP%\CreateStartup.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateStartup.vbs"
echo oLink.TargetPath = "%SCRIPT_DIR%start.bat" >> "%TEMP%\CreateStartup.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateStartup.vbs"
echo oLink.Description = "Auto-launch Life Curriculum Assistant" >> "%TEMP%\CreateStartup.vbs"
echo oLink.WindowStyle = 7 >> "%TEMP%\CreateStartup.vbs"
echo oLink.Save >> "%TEMP%\CreateStartup.vbs"

cscript //nologo "%TEMP%\CreateStartup.vbs"
del "%TEMP%\CreateStartup.vbs"

echo.
echo Added to Windows Startup!
echo The app will auto-launch when you log in.
echo.
echo To remove from startup, delete:
echo %STARTUP_FOLDER%\%SHORTCUT_NAME%.lnk
echo.
pause
