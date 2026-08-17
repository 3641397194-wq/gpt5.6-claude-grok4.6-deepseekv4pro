@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 冷咖啡 ColdBrew Hub
where python >nul 2>nul
if %errorlevel%==0 (
    python coldbrew_hub.py
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py coldbrew_hub.py
    ) else (
        echo [错误] 未找到 Python 3，请先安装 Python 3.10+ 并勾选 "Add to PATH"
        echo 下载地址: https://www.python.org/downloads/
        pause
    )
)
if errorlevel 1 (
    echo.
    echo 面板异常退出，请把上面的报错截图。
    pause
)
