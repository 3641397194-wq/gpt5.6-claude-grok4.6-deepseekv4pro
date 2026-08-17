@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 冷咖啡 ColdBrew Hub

rem ---- 找到真正可用的 Python（排除 Microsoft Store 假占位） ----
set "PY="
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=python"
if not defined PY (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY=py -3"
)

if defined PY goto :run

echo [错误] 未找到可用的 Python 3.10 或更高版本
echo.
echo 解决办法（任选其一）：
echo   1. 到 https://www.python.org/downloads/ 下载安装 Python 3.10+，
echo      安装时务必勾选 "Add python.exe to PATH"；
echo   2. 如果已经装了 Python 仍报这个错，多半是 Microsoft Store 的
echo      假 Python 占位在捣乱：打开 设置 - 应用 - 高级应用设置 -
echo      应用执行别名，把 python.exe 和 python3.exe 的开关关掉。
echo.
echo 修好后重新双击本文件即可。
echo.
pause
exit /b 1

:run
echo 正在启动冷咖啡 ColdBrew Hub...
%PY% coldbrew_hub.py 2>"面板启动错误日志.txt"
if not errorlevel 1 exit /b 0

echo.
echo [启动失败] 面板异常退出，详细报错已写入本目录的 "面板启动错误日志.txt"。
echo 把日志内容发给冷咖啡社区 QQ 群（1057540028 / 1077074552）可快速定位。
echo.
pause
exit /b 1
