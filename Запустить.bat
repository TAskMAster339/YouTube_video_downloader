@echo off
if not exist "%~dp0YouTube_Downloader.exe" (
    echo YouTube_Downloader.exe not found. Download it from GitHub Releases into this folder.
    pause
    exit /b 1
)
start "" /D "%~dp0" "%~dp0YouTube_Downloader.exe"
