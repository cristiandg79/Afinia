param(
    [string]$Mensaje = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".git")) {
    Write-Host "No se ha encontrado un repositorio Git en esta carpeta." -ForegroundColor Red
    exit 1
}

$rama = git branch --show-current
if ([string]::IsNullOrWhiteSpace($rama)) {
    Write-Host "No se ha podido detectar la rama actual." -ForegroundColor Red
    exit 1
}

$cambios = git status --porcelain
if (-not $cambios) {
    Write-Host "No hay cambios pendientes para publicar." -ForegroundColor Green
    exit 0
}

$patronesSecretos = @(
    ("github" + "_pat" + "_"),
    ("gh" + "p" + "_"),
    ("gh" + "o" + "_"),
    ("gh" + "u" + "_"),
    ("gh" + "s" + "_"),
    ("gh" + "r" + "_")
)

$archivos = git ls-files --modified --others --exclude-standard
foreach ($archivo in $archivos) {
    if (-not (Test-Path $archivo -PathType Leaf)) {
        continue
    }

    $extension = [System.IO.Path]::GetExtension($archivo).ToLowerInvariant()
    if ($extension -in @(".zip", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf")) {
        continue
    }

    foreach ($patron in $patronesSecretos) {
        $coincidencia = Select-String -Path $archivo -Pattern $patron -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($coincidencia) {
            Write-Host "No se publica porque parece haber un token o secreto en:" -ForegroundColor Red
            Write-Host "  $archivo, linea $($coincidencia.LineNumber)" -ForegroundColor Yellow
            Write-Host "Quita ese dato antes de volver a ejecutar el script." -ForegroundColor Yellow
            exit 1
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Mensaje)) {
    $fecha = Get-Date -Format "yyyy-MM-dd HH:mm"
    $Mensaje = "Update Afinia $fecha"
}

Write-Host "Preparando cambios..." -ForegroundColor Cyan
$archivosParaAgregar = @(
    git ls-files --modified --deleted --others --exclude-standard |
    Where-Object {
        $_ -notmatch '^(media/|media\\)' -and
        $_ -notlike 'media*.zip' -and
        $_ -ne 'media_entrega_actual.zip'
    }
)
if ($archivosParaAgregar.Count -gt 0) {
    git add -- $archivosParaAgregar
    if ($LASTEXITCODE -ne 0) {
        Write-Host "No se han podido preparar los cambios." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

$archivosPreparados = git diff --cached --name-only
if (-not $archivosPreparados) {
    Write-Host "No hay cambios publicables despues de excluir media." -ForegroundColor Yellow
    exit 0
}

Write-Host "Creando version: $Mensaje" -ForegroundColor Cyan
git commit -m $Mensaje
if ($LASTEXITCODE -ne 0) {
    Write-Host "No se ha podido crear la version." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Subiendo a GitHub en la rama $rama..." -ForegroundColor Cyan
git push origin $rama
if ($LASTEXITCODE -ne 0) {
    Write-Host "GitHub ha rechazado la subida. Revisa el error anterior." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Publicado correctamente." -ForegroundColor Green
