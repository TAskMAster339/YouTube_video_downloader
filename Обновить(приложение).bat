@echo off
REM YouTube Downloader Auto-Update Script
REM Загрузить последний exe с GitHub и заменить текущий
REM Исправленная версия

setlocal enabledelayedexpansion

REM ==================== НАСТРОЙКИ ====================
set GITHUB_OWNER=TAskMAster339
set GITHUB_REPO=YouTube_video_downloader
set ASSET_NAME=YouTube_Downloader.exe

REM ==================== ПАПКИ ====================
set SCRIPT_DIR=%~dp0
set APP_PATH=%SCRIPT_DIR%%ASSET_NAME%
set TEMP_FILE=%SCRIPT_DIR%YouTube_Downloader.exe.tmp
set BACKUP_PATH=%SCRIPT_DIR%%ASSET_NAME%.backup
set JSON_FILE=%SCRIPT_DIR%release.json
set URL_FILE=%SCRIPT_DIR%download_url.txt
set VER_FILE=%SCRIPT_DIR%version.txt

REM ==================== ВЫВОД ====================
cls
echo.
echo ============================================================
echo 🔄 YouTube Downloader Auto-Update
echo ============================================================
echo.

REM ==================== ШАГ 1: Получаем информацию о релизе ====================
echo [*] Checking GitHub for updates...

set API_URL=https://api.github.com/repos/%GITHUB_OWNER%/%GITHUB_REPO%/releases/latest

REM Используем PowerShell для скачивания JSON
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%API_URL%' -OutFile '%JSON_FILE%' -TimeoutSec 10 -ErrorAction Stop } catch { exit 1 }" >nul 2>&1

if errorlevel 1 (
    echo [!] ERROR: Could not connect to GitHub
    echo.
    echo Make sure you have internet connection and GitHub is accessible
    echo.
    pause
    exit /b 1
)

if not exist "%JSON_FILE%" (
    echo [!] ERROR: Failed to download release info
    pause
    exit /b 1
)

REM ==================== ШАГ 2: Парсим JSON и получаем URL ====================
echo [*] Parsing release information...

powershell -NoProfile -Command ^
  "$json = Get-Content '%JSON_FILE%' -Raw | ConvertFrom-Json; " ^
  "$version = $json.tag_name; " ^
  "$asset = $json.assets | Where-Object { $_.name -eq '%ASSET_NAME%' } | Select-Object -First 1; " ^
  "if ($asset) { " ^
  "[System.IO.File]::WriteAllText('%URL_FILE%', $asset.browser_download_url); " ^
  "[System.IO.File]::WriteAllText('%VER_FILE%', $version); " ^
  "} else { " ^
  "exit 1 " ^
  "}" >nul 2>&1

if errorlevel 1 (
    echo [!] ERROR: Could not find %ASSET_NAME% in release
    del /f /q "%JSON_FILE%" 2>nul
    pause
    exit /b 1
)

REM Читаем значения
if not exist "%URL_FILE%" (
    echo [!] ERROR: Failed to parse URL
    pause
    exit /b 1
)

set /p DOWNLOAD_URL=<"%URL_FILE%"
set /p NEW_VERSION=<"%VER_FILE%"

if "!DOWNLOAD_URL!"=="" (
    echo [!] ERROR: Download URL is empty
    pause
    exit /b 1
)

echo [+] Found version: !NEW_VERSION!
echo.

REM ==================== ШАГ 3: Скачиваем файл ====================
echo ============================================================
echo ⬇️  Downloading update...
echo ============================================================
echo.

REM Проверяем наличие PowerShell (более надежный способ скачивания)
powershell -NoProfile -Command ^
  "try { " ^
  "$ProgressPreference = 'SilentlyContinue'; " ^
  "Invoke-WebRequest -Uri '!DOWNLOAD_URL!' -OutFile '%TEMP_FILE%' -TimeoutSec 300 -ErrorAction Stop; " ^
  "} catch { " ^
  "exit 1 " ^
  "}" >nul 2>&1

if errorlevel 1 (
    echo [!] ERROR: Failed to download
    del /f /q "%JSON_FILE%" "%URL_FILE%" "%VER_FILE%" 2>nul
    pause
    exit /b 1
)

if not exist "%TEMP_FILE%" (
    echo [!] ERROR: Downloaded file not found
    del /f /q "%JSON_FILE%" "%URL_FILE%" "%VER_FILE%" 2>nul
    pause
    exit /b 1
)

echo [+] Download complete
echo.

REM ==================== ШАГ 4: Останавливаем приложение ====================
echo [*] Stopping application...
taskkill /IM "%ASSET_NAME%" /F 2>nul
timeout /t 1 /nobreak >nul

REM ==================== ШАГ 5: Создаем резервную копию ====================
if exist "%APP_PATH%" (
    echo [*] Creating backup...
    if exist "%BACKUP_PATH%" del /f /q "%BACKUP_PATH%" 2>nul
    copy "%APP_PATH%" "%BACKUP_PATH%" >nul
    if errorlevel 1 (
        echo [!] WARNING: Backup failed, but continuing...
    )
)

REM ==================== ШАГ 6: Устанавливаем новую версию ====================
echo.
echo ============================================================
echo 📦 Installing update...
echo ============================================================
echo.

REM Удаляем старый файл
if exist "%APP_PATH%" (
    del /f /q "%APP_PATH%" 2>nul
    if errorlevel 1 (
        echo [!] ERROR: Could not delete old version
        echo Trying to restore backup...
        if exist "%BACKUP_PATH%" (
            copy "%BACKUP_PATH%" "%APP_PATH%" >nul
        )
        del /f /q "%TEMP_FILE%" 2>nul
        del /f /q "%JSON_FILE%" "%URL_FILE%" "%VER_FILE%" 2>nul
        pause
        exit /b 1
    )
)

REM Копируем новый файл
copy "%TEMP_FILE%" "%APP_PATH%" >nul
if errorlevel 1 (
    echo [!] ERROR: Installation failed
    if exist "%BACKUP_PATH%" (
        echo [*] Restoring backup...
        copy "%BACKUP_PATH%" "%APP_PATH%" >nul
    )
    del /f /q "%TEMP_FILE%" 2>nul
    del /f /q "%JSON_FILE%" "%URL_FILE%" "%VER_FILE%" 2>nul
    pause
    exit /b 1
)

if exist "%APP_PATH%" (
    echo [+] Update installed successfully!
) else (
    echo [!] ERROR: Installation verification failed
    del /f /q "%JSON_FILE%" "%URL_FILE%" "%VER_FILE%" 2>nul
    pause
    exit /b 1
)

REM ==================== ШАГ 7: Очищаем временные файлы ====================
echo [*] Cleaning up...
del /f /q "%TEMP_FILE%" 2>nul
del /f /q "%JSON_FILE%" 2>nul
del /f /q "%URL_FILE%" 2>nul
del /f /q "%VER_FILE%" 2>nul

REM ==================== ШАГ 8: Запускаем приложение ====================
echo.
echo 🚀 Launching application...
start "" "%APP_PATH%"

echo.
echo ✅ Update completed successfully!
echo.

timeout /t 2 /nobreak >nul
exit /b 0
