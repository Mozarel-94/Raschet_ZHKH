@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE="

if exist "C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe" (
  set "PYTHON_EXE=C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe"
)

if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=py"
)

if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
  echo Не удалось найти Python для запуска локальной версии.
  echo Установите Python или поправьте путь в файле run_local.bat.
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
