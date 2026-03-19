@echo off
setlocal

cd /d "%~dp0"

set "APP_ROOT=%~dp0"
set "PORTABLE_PYTHON=%APP_ROOT%.portable\python\python.exe"
set "PYTHON_EXE="

if exist "%PORTABLE_PYTHON%" (
  set "PYTHON_EXE=%PORTABLE_PYTHON%"
)

if not defined PYTHON_EXE (
  if exist "%APP_ROOT%python\python.exe" (
    set "PYTHON_EXE=%APP_ROOT%python\python.exe"
  )
)

if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=py"
)

if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=python"
)

if exist "%APP_ROOT%.vendor\site-packages" (
  if defined PYTHONPATH (
    set "PYTHONPATH=%APP_ROOT%.vendor\site-packages;%APP_ROOT%;%PYTHONPATH%"
  ) else (
    set "PYTHONPATH=%APP_ROOT%.vendor\site-packages;%APP_ROOT%"
  )
)

if not defined PYTHON_EXE (
  echo Не удалось найти Python для запуска приложения.
  echo.
  echo Для запуска без установки Python:
  echo 1. Соберите переносимую папку командой:
  echo    powershell -ExecutionPolicy Bypass -File scripts\build_windows_portable.ps1
  echo 2. Откройте готовую папку dist\Raschet_ZHKH_Windows_Portable
  echo 3. Запустите из нее run_local.bat
  echo.
  echo Если Python уже установлен, добавьте его в PATH и повторите запуск.
  pause
  exit /b 1
)

echo Запуск локальной версии ЖКХ...
echo Откройте в браузере: http://127.0.0.1:8000
echo.
start "" "http://127.0.0.1:8000"

if /i "%PYTHON_EXE%"=="py" (
  py app.py
) else (
  "%PYTHON_EXE%" app.py
)

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Приложение завершилось с кодом %EXIT_CODE%.
  pause
)

exit /b %EXIT_CODE%
