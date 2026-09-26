@echo off
chcp 65001 >nul
title 具身智能课程 · 设备开发本机助手 (127.0.0.1:8100)
cd /d "%~dp0"

rem ---- 查找 Python 3（优先 py 启动器，其次 python） ----
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
    echo [x] 未找到 Python 3。
    echo     请先安装：https://www.python.org/downloads/  安装时勾选 "Add Python to PATH"。
    pause
    exit /b 1
)

rem ---- one-time protocol registration (idempotent, HKCU, no admin): ----
rem after this, pages can silently auto-start the helper via eai-helper:// ----
call "%~dp0register_helper.bat" --silent >nul 2>&1

echo [i] 启动本机助手（首次运行会自动安装依赖，约需 1~2 分钟）…
%PY% "%~dp0start_helper.py" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo [x] 启动失败（退出码 %RC%），请把上面的报错拍照反馈。
    pause
)
exit /b %RC%