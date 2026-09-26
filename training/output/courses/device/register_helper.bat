@echo off
chcp 65001 >nul
rem =========================================================================
rem  One-time registration of the eai-helper:// custom protocol (HKCU only,
rem  no admin required). The registry command points to start_helper_hidden.vbs,
rem  a portable launcher that locates python at launch time - so this .bat can
rem  be copied to any Windows machine and will keep working.
rem
rem  Usage:  register_helper.bat            (interactive, pause at the end)
rem          register_helper.bat --silent   (called by start_helper.bat, no pause)
rem  Undo:   reg delete "HKCU\Software\Classes\eai-helper" /f
rem =========================================================================
set "DIR=%~dp0"
set "SILENT="
if /i "%~1"=="--silent" set "SILENT=1"

if not exist "%DIR%start_helper_hidden.vbs" (
    echo [x] start_helper_hidden.vbs not found. Run this from its own directory.
    if not defined SILENT pause
    exit /b 1
)

rem ---- python must exist on PATH (the vbs resolves it at launch time) ----
where py >nul 2>&1
if errorlevel 1 where python >nul 2>&1
if errorlevel 1 (
    echo [x] Python not found on PATH. Install Python 3 and check "Add to PATH",
    echo     then run this script again.
    if not defined SILENT pause
    exit /b 1
)

rem "%1" passes eai-helper://start?port=NNN verbatim; start_helper.py parses the port.
reg add "HKCU\Software\Classes\eai-helper" /ve /d "URL:EAI Device Helper" /f >nul
reg add "HKCU\Software\Classes\eai-helper" /v "URL Protocol" /d "" /f >nul
reg add "HKCU\Software\Classes\eai-helper\DefaultIcon" /ve /d "%DIR%start_helper_hidden.vbs,0" /f >nul
rem "%%1" - batch-level escaping: the REGISTRY value must literally end with "%1", so
rem Windows substitutes the eai-helper:// URL when the protocol fires, and
rem start_helper.py parses the port. A single %1 would be expanded to this
rem script's own first argument (e.g. "--silent") and break the hand-off.
reg add "HKCU\Software\Classes\eai-helper\shell\open\command" /ve /d "\"C:\Windows\System32\wscript.exe\" \"%DIR%start_helper_hidden.vbs\" \"%%1\"" /f >nul

if errorlevel 1 (
    echo [x] Registration failed. Try again as Administrator, or just double-click
    echo     start_helper.bat instead.
    if not defined SILENT pause
    exit /b 1
)

echo [+] eai-helper:// protocol registered (HKCU, current user only).
if defined SILENT exit /b 0
echo     Browser will auto-start the helper (hidden, log in helper.log) whenever a
echo     page fires eai-helper://. First time: allow the external-protocol prompt
echo     and tick "always allowed".
echo     Undo: reg delete "HKCU\Software\Classes\eai-helper" /f
pause
exit /b 0