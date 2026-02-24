<#
build_exe.ps1 - Crear un .exe de Windows usando PyInstaller
Uso: Abrir PowerShell en la raíz del proyecto y ejecutar:
    .\build_exe.ps1

Este script crea/activa un entorno virtual, instala PyInstaller
y empaqueta `app.py` en un único ejecutable, incluyendo carpetas
de `templates`, `static`, `uploads` y `results`.
#>

try {
    # Activar o crear entorno virtual
    if (Test-Path .\venv\Scripts\Activate.ps1) {
        . .\venv\Scripts\Activate.ps1
    } else {
        py -3 -m venv venv
        .\venv\Scripts\Activate.ps1
    }

    python -m pip install --upgrade pip setuptools wheel
    pip install pyinstaller

    # Download Demucs model (htdemucs) if not already cached
    Write-Host "Ensuring Demucs models are available..."
    $demucsCache = Join-Path $env:USERPROFILE ".demucs"
    $htdemucsModel = Join-Path $demucsCache "htdemucs.pt"
    if (-Not (Test-Path $htdemucsModel)) {
        Write-Host "Downloading Demucs htdemucs model (this may take a few minutes)..."
        python -c "import demucs.pretrained; demucs.pretrained.get_model('htdemucs')" > $null 2>&1
        if (Test-Path $htdemucsModel) {
            Write-Host "Demucs model downloaded successfully."
        } else {
            Write-Host "Warning: Demucs model download may have failed." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Demucs model already cached."
    }

    # Copy whisper assets to a local folder for bundling
    Write-Host "Copying whisper assets for bundling..."
    $whisperAssetsDir = Join-Path (Get-Location) "whisper_assets"
    $venvWhisperAssetsDir = Join-Path (Get-Location) "venv\Lib\site-packages\whisper\assets"
    if (Test-Path $venvWhisperAssetsDir) {
        if (Test-Path $whisperAssetsDir) { Remove-Item -Recurse -Force $whisperAssetsDir }
        Copy-Item -Path $venvWhisperAssetsDir -Destination $whisperAssetsDir -Recurse -Force
        Write-Host "Whisper assets copied to: $whisperAssetsDir"
    } else {
        Write-Host "Warning: Whisper assets not found at $venvWhisperAssetsDir" -ForegroundColor Yellow
    }

    # Copy Demucs cache to local folder for bundling
    Write-Host "Copying Demucs models for bundling..."
    $demucsLocalDir = Join-Path (Get-Location) "demucs_models"
    $demucsCache = Join-Path $env:USERPROFILE ".demucs"
    if (Test-Path $demucsCache) {
        if (Test-Path $demucsLocalDir) { Remove-Item -Recurse -Force $demucsLocalDir }
        Copy-Item -Path $demucsCache -Destination $demucsLocalDir -Recurse -Force
        Write-Host "Demucs models copied to: $demucsLocalDir"
    } else {
        Write-Host "Warning: Demucs cache not found at $demucsCache" -ForegroundColor Yellow
    }

    # Ensure ffmpeg folder exists; if not, download a static Windows build and extract
    $ffmpegDir = Join-Path (Get-Location) "ffmpeg"
    if (-Not (Test-Path $ffmpegDir)) {
        Write-Host "ffmpeg not found in project. Downloading a static ffmpeg build (windows)..."
        $zipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        $zipPath = Join-Path $env:TEMP "ffmpeg_release.zip"
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
        $tmpExtract = Join-Path $env:TEMP "ffmpeg_extract"
        if (Test-Path $tmpExtract) { Remove-Item -Recurse -Force $tmpExtract }
        Expand-Archive -Path $zipPath -DestinationPath $tmpExtract -Force
        # Find the extracted folder that contains bin\ffmpeg.exe
        $extracted = Get-ChildItem $tmpExtract -Directory | Where-Object { Test-Path (Join-Path $_.FullName "bin\ffmpeg.exe") } | Select-Object -First 1
        if ($extracted) {
            New-Item -ItemType Directory -Path (Join-Path $ffmpegDir "bin") -Force | Out-Null
            Copy-Item -Path (Join-Path $extracted.FullName "bin\*") -Destination (Join-Path $ffmpegDir "bin") -Recurse -Force
            Write-Host "ffmpeg downloaded and extracted to: $ffmpegDir"
        } else {
            Write-Host "No se pudo localizar ffmpeg en el zip descargado." -ForegroundColor Yellow
        }
        Remove-Item $zipPath -Force
        # Optionally cleanup tmpExtract
        # Remove-Item -Recurse -Force $tmpExtract
    } else {
        Write-Host "ffmpeg directory already present, skipping download."
    }

    # Limpiar builds previos
    if (Test-Path .\build) { Remove-Item -Recurse -Force .\build }
    if (Test-Path .\dist)  { Remove-Item -Recurse -Force .\dist }
    $specFile = Join-Path (Get-Location) "LyricTranscriptor.spec"
    if (Test-Path $specFile) { Remove-Item -Force $specFile }

    # Ejecutar PyInstaller (Windows: separador de datos = ; )
    # Incluimos ffmpeg binarios y carpetas necesarias
    $addData = @(
        "templates;templates",
        "static;static",
        "uploads;uploads",
        "results;results",
        "ffmpeg;ffmpeg",
        "whisper_assets;whisper/assets"
    )

    # Add demucs models only if they exist locally
    $demucsLocalDir = Join-Path (Get-Location) "demucs_models"
    if (Test-Path $demucsLocalDir) {
        $addData += "demucs_models;.demucs"
        Write-Host "Demucs models will be included in bundle."
    } else {
        Write-Host "Demucs models not found locally; they will be downloaded on first use." -ForegroundColor Yellow
    }

    # Binaries to include (ffmpeg, ffprobe)
    $addBin = @()
    $ffmpegBinPath = Join-Path $ffmpegDir "bin"
    if (Test-Path (Join-Path $ffmpegBinPath "ffmpeg.exe")) {
        $addBin += "${ffmpegBinPath}\ffmpeg.exe;ffmpeg\\bin"
    }
    if (Test-Path (Join-Path $ffmpegBinPath "ffprobe.exe")) {
        $addBin += "${ffmpegBinPath}\ffprobe.exe;ffmpeg\\bin"
    }

    $pyArgs = @("--noconfirm","--clean","--onefile","--name","LyricTranscriptor")
    foreach ($d in $addData) { $pyArgs += "--add-data"; $pyArgs += $d }
    foreach ($b in $addBin)  { $pyArgs += "--add-binary"; $pyArgs += $b }
    $pyArgs += "app.py"

    Write-Host "Running: pyinstaller $($pyArgs -join ' ')"
    pyinstaller @pyArgs

    Write-Host "Build finished. Executable: .\dist\LyricTranscriptor.exe"
} catch {
    Write-Host "Error durante el build: $_" -ForegroundColor Red
    exit 1
}
