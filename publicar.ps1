param(
    [string]$Mensaje = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".git")) {
    Write-Host "No se ha encontrado un repositorio Git en esta carpeta." -ForegroundColor Red
    exit 1
}

$cambios = git status --porcelain
if (-not $cambios) {
    Write-Host "No hay cambios pendientes para publicar." -ForegroundColor Green
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Mensaje)) {
    $fecha = Get-Date -Format "yyyy-MM-dd HH:mm"
    $Mensaje = "Update Afinia $fecha"
}

Write-Host "Preparando cambios..." -ForegroundColor Cyan
git add -A

Write-Host "Creando version: $Mensaje" -ForegroundColor Cyan
git commit -m $Mensaje

Write-Host "Subiendo a GitHub..." -ForegroundColor Cyan
git push

Write-Host "Publicado correctamente." -ForegroundColor Green
