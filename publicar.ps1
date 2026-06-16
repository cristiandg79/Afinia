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
git add -A

Write-Host "Creando version: $Mensaje" -ForegroundColor Cyan
git commit -m $Mensaje

Write-Host "Subiendo a GitHub en la rama $rama..." -ForegroundColor Cyan
git push origin $rama

Write-Host "Publicado correctamente." -ForegroundColor Green
