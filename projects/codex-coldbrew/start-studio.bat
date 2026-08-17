@echo off
setlocal
set "ROOT=%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py "%ROOT%studio\coldbrew_studio.py" gui --profile "max"
  exit /b %errorlevel%
)
where python >nul 2>nul
if %errorlevel%==0 (
  python "%ROOT%studio\coldbrew_studio.py" gui --profile "max"
  exit /b %errorlevel%
)
echo Python 3 is required to launch ColdBrew Studio.
exit /b 2
