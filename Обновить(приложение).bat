@echo off
REM YouTube Downloader Auto-Update Script
REM Загрузить последний exe с GitHub и заменить текущий
REM Исправленная версия

setlocal DisableDelayedExpansion

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
powershell -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri $env:API_URL -OutFile $env:JSON_FILE -TimeoutSec 30 -ErrorAction Stop } catch { exit 1 }" >nul 2>&1

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
  "$ErrorActionPreference='Stop'; $json = Get-Content -LiteralPath $env:JSON_FILE -Raw | ConvertFrom-Json; " ^
  "$version = $json.tag_name; " ^
  "$asset = $json.assets | Where-Object { $_.name -eq $env:ASSET_NAME } | Select-Object -First 1; " ^
  "if ($asset) { " ^
  "[System.IO.File]::WriteAllText($env:URL_FILE, $asset.browser_download_url); " ^
  "[System.IO.File]::WriteAllText($env:VER_FILE, $version); " ^
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

if "%DOWNLOAD_URL%"=="" (
    echo [!] ERROR: Download URL is empty
    pause
    exit /b 1
)

echo [+] Found version: %NEW_VERSION%
echo.

REM ==================== ШАГ 3: Скачиваем файл ====================
echo ============================================================
echo ⬇️  Downloading update...
echo ============================================================
echo.

REM Проверяем наличие PowerShell (более надежный способ скачивания)
powershell -NoProfile -Command ^
  "try { " ^
  "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; " ^
  "Invoke-WebRequest -UseBasicParsing -Uri $env:DOWNLOAD_URL -OutFile $env:TEMP_FILE -TimeoutSec 600 -ErrorAction Stop; " ^
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

powershell -NoProfile -Command "try { $ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $json=Get-Content -LiteralPath $env:JSON_FILE -Raw | ConvertFrom-Json; $asset=$json.assets | Where-Object name -eq 'SHA256SUMS.txt' | Select-Object -First 1; if ($asset) { $text=(Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -TimeoutSec 30).Content; $match=[regex]::Match($text,'(?im)^([a-f0-9]{64})\s+\*?YouTube_Downloader\.exe\s*$'); $sha=[Security.Cryptography.SHA256]::Create(); $stream=[IO.File]::OpenRead($env:TEMP_FILE); try {$hash=[BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','')} finally {$stream.Dispose(); $sha.Dispose()}; if (!$match.Success -or $hash -ne $match.Groups[1].Value) {exit 1} } } catch {exit 1}"
if errorlevel 1 (
    echo [!] ERROR: Checksum validation failed. Existing application kept.
    del /f /q "%TEMP_FILE%" 2>nul
    pause
    exit /b 1
)

REM Validate the size and PE header before touching the existing application.
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $json=Get-Content -LiteralPath $env:JSON_FILE -Raw | ConvertFrom-Json; $asset=$json.assets | Where-Object name -eq $env:ASSET_NAME | Select-Object -First 1; if ((Get-Item -LiteralPath $env:TEMP_FILE).Length -ne $asset.size) {exit 1}; $stream=[IO.File]::OpenRead($env:TEMP_FILE); try {if ($stream.ReadByte() -ne 77 -or $stream.ReadByte() -ne 90) {exit 1}} finally {$stream.Dispose()}"
if errorlevel 1 (
    echo [!] ERROR: Download validation failed. Existing application kept.
    del /f /q "%TEMP_FILE%" 2>nul
    pause
    exit /b 1
)

REM ==================== ШАГ 4: Останавливаем приложение ====================
echo [*] Checking whether the application is closed...
powershell -NoProfile -Command "if (Get-Process -Name YouTube_Downloader -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $env:APP_PATH }) {exit 1}"
if errorlevel 1 (
    echo [!] Close YouTube Downloader and run this updater again.
    del /f /q "%TEMP_FILE%" 2>nul
    pause
    exit /b 1
)

REM ==================== ШАГ 5: Создаем резервную копию ====================
if exist "%APP_PATH%" (
    echo [*] Creating backup...
    if exist "%BACKUP_PATH%" del /f /q "%BACKUP_PATH%" 2>nul
    copy "%APP_PATH%" "%BACKUP_PATH%" >nul
    if errorlevel 1 (
        echo [!] ERROR: Backup failed. Update cancelled.
        pause
        exit /b 1
    )
)

REM ==================== ШАГ 6: Устанавливаем новую версию ====================
echo.
echo ============================================================
echo 📦 Installing update...
echo ============================================================
echo.

REM Replace atomically; keep the old EXE if replacement fails.
powershell -NoProfile -Command "try { $ErrorActionPreference='Stop'; if (Test-Path -LiteralPath $env:APP_PATH) { [IO.File]::Replace($env:TEMP_FILE,$env:APP_PATH,$env:BACKUP_PATH) } else { Move-Item -LiteralPath $env:TEMP_FILE -Destination $env:APP_PATH } } catch {exit 1}"
if errorlevel 1 (
    echo [!] ERROR: Installation failed. Existing EXE and backup kept.
    del /f /q "%TEMP_FILE%" 2>nul
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
