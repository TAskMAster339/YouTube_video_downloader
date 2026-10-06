$ErrorActionPreference = 'Stop'

# GitHub rewrites non-ASCII asset names. Use distinct ASCII names to avoid
# collisions and the action's additional PATCH request to restore asset labels.
$scripts = [ordered]@{
    'Обновить(приложение).bat' = 'update-app.bat'
    'Обновить.bat' = 'update-source.bat'
    'Запустить.bat' = 'launch.bat'
}
foreach ($source in $scripts.Keys) {
    Copy-Item -LiteralPath $source -Destination (Join-Path 'dist' $scripts[$source]) -Force
}

# Preserve the original filenames inside a safely named release asset.
Compress-Archive -LiteralPath @($scripts.Keys) -DestinationPath 'dist/windows-scripts.zip' -Force
$hash = (Get-FileHash -LiteralPath 'dist/YouTube_Downloader.exe' -Algorithm SHA256).Hash.ToLower()
"$hash  YouTube_Downloader.exe" | Set-Content -Encoding ascii 'dist/SHA256SUMS.txt'
