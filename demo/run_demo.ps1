# ==============================================================================
# UNMSM - Taller de Arquitectura de Software (TARQSW-06)
# Script de Demostración Rápida para Windows PowerShell
# ==============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  🎓 SISTEMA DE GESTIÓN DE EXPEDIENTES DE BOLSISTAS UNMSM        " -ForegroundColor Yellow
Write-Host "  Demostración de Arquitectura Distribuida (Rúbrica de 20 Pts)   " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Seleccione la acción a ejecutar:" -ForegroundColor White
Write-Host "  [1] Ejecutar prueba automatizada End-to-End (test_e2e.py)" -ForegroundColor Green
Write-Host "  [2] Iniciar todos los servicios con Docker Compose (RabbitMQ + API + Docs)" -ForegroundColor Green
Write-Host "  [3] Iniciar solo la API REST localmente (FastAPI en :8000)" -ForegroundColor Yellow
Write-Host "  [4] Iniciar solo el Microservicio DocsService (Consumidor RabbitMQ)" -ForegroundColor Yellow
Write-Host "  [5] Iniciar el emulador local de Serverless AWS Lambda (en :8001)" -ForegroundColor Yellow
Write-Host "  [6] Abrir Swagger UI de la API en el navegador (/docs)" -ForegroundColor Cyan
Write-Host "  [7] Abrir Panel de RabbitMQ en el navegador (:15672)" -ForegroundColor Cyan
Write-Host "  [8] Ejecutar la App de Escritorio original (CustomTkinter)" -ForegroundColor Magenta
Write-Host "  [Q] Salir" -ForegroundColor DarkGray
Write-Host ""

$opcion = Read-Host "Ingrese opción (1-8 o Q)"

switch ($opcion) {
    "1" {
        Write-Host "`n>> Ejecutando prueba automatizada E2E..." -ForegroundColor Cyan
        python demo/test_e2e.py
    }
    "2" {
        Write-Host "`n>> Levantando contenedores con docker-compose..." -ForegroundColor Cyan
        docker-compose up --build
    }
    "3" {
        Write-Host "`n>> Iniciando FastAPI en http://localhost:8000..." -ForegroundColor Cyan
        uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
    }
    "4" {
        Write-Host "`n>> Iniciando Worker DocsService..." -ForegroundColor Cyan
        python services/docs_service/worker.py
    }
    "5" {
        Write-Host "`n>> Iniciando Emulador Serverless en http://localhost:8001..." -ForegroundColor Cyan
        python functions/notificar_jefe/local_server.py
    }
    "6" {
        Write-Host "`n>> Abriendo Swagger UI..." -ForegroundColor Cyan
        Start-Process "http://localhost:8000/docs"
    }
    "7" {
        Write-Host "`n>> Abriendo RabbitMQ Management..." -ForegroundColor Cyan
        Start-Process "http://localhost:15672"
    }
    "8" {
        Write-Host "`n>> Iniciando App de Escritorio..." -ForegroundColor Magenta
        python src/main.py
    }
    default {
        Write-Host "`nSaliendo..." -ForegroundColor Gray
    }
}
