# Voice AI System Startup Script
# PowerShell script to start and validate the complete Voice AI system

param(
    [switch]$Production,
    [switch]$Debug,
    [string]$Environment = "development"
)

Write-Host "🎤 Voice AI System Startup Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "✅ Created .env file from template" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env file with your actual API keys" -ForegroundColor Yellow
    } else {
        Write-Host "❌ env.example not found. Please create .env file manually." -ForegroundColor Red
        exit 1
    }
}

# Validate environment variables
Write-Host "Validating environment variables..." -ForegroundColor Yellow
$requiredVars = @(
    "VAPI_API_KEY",
    "OPENAI_API_KEY",
    "PINECONE_API_KEY",
    "N8N_PASSWORD",
    "POSTGRES_PASSWORD"
)

$missingVars = @()
foreach ($var in $requiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if (-not $value -or $value -eq "your_${var}_here") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing or invalid environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host "Please update your .env file with valid values." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Environment variables validated" -ForegroundColor Green

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
$directories = @(
    "vapi/data",
    "n8n/workflows",
    "rag/documents",
    "memory/data",
    "screenshots",
    "logs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Created directory: $dir" -ForegroundColor Green
    }
}

# Start the system
Write-Host "Starting Voice AI system..." -ForegroundColor Yellow

if ($Production) {
    Write-Host "🚀 Starting in PRODUCTION mode" -ForegroundColor Red
    docker-compose -f docker-compose.prod.yml up -d
} else {
    Write-Host "🔧 Starting in DEVELOPMENT mode" -ForegroundColor Green
    docker-compose up -d
}

# Wait for services to start
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "Checking service status..." -ForegroundColor Yellow
$services = @(
    @{Name="VAPI"; Port=3000; Path="/health"},
    @{Name="n8n"; Port=5678; Path="/healthz"},
    @{Name="RAG"; Port=8000; Path="/health"},
    @{Name="Memory"; Port=8001; Path="/health"},
    @{Name="Redis"; Port=6379; Path=""},
    @{Name="PostgreSQL"; Port=5432; Path=""},
    @{Name="Elasticsearch"; Port=9200; Path="/"},
    @{Name="Grafana"; Port=3001; Path="/"},
    @{Name="Kibana"; Port=5601; Path="/"}
)

$healthyServices = 0
$totalServices = $services.Count

foreach ($service in $services) {
    try {
        $url = "http://localhost:$($service.Port)$($service.Path)"
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Name) is healthy" -ForegroundColor Green
            $healthyServices++
        } else {
            Write-Host "⚠️  $($service.Name) returned status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.Name) is not responding" -ForegroundColor Red
    }
}

Write-Host "`n📊 Service Health Summary:" -ForegroundColor Cyan
Write-Host "   Healthy: $healthyServices/$totalServices" -ForegroundColor Green

if ($healthyServices -eq $totalServices) {
    Write-Host "🎉 All services are running successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some services may need more time to start" -ForegroundColor Yellow
}

# Display access URLs
Write-Host "`n🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "   VAPI Dashboard:     http://localhost:3000" -ForegroundColor White
Write-Host "   n8n Dashboard:      http://localhost:5678" -ForegroundColor White
Write-Host "   RAG API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Memory API Docs:    http://localhost:8001/docs" -ForegroundColor White
Write-Host "   Grafana Dashboard:  http://localhost:3001" -ForegroundColor White
Write-Host "   Kibana Dashboard:   http://localhost:5601" -ForegroundColor White

# Show logs command
Write-Host "`n📋 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View all logs:      docker-compose logs -f" -ForegroundColor White
Write-Host "   View specific logs: docker-compose logs -f vapi" -ForegroundColor White
Write-Host "   Stop system:        docker-compose down" -ForegroundColor White
Write-Host "   Restart system:     docker-compose restart" -ForegroundColor White

# Test endpoints
Write-Host "`n🧪 Testing endpoints..." -ForegroundColor Yellow

# Test VAPI health
try {
    $vapiHealth = Invoke-RestMethod -Uri "http://localhost:3000/health" -Method Get
    Write-Host "✅ VAPI health check passed" -ForegroundColor Green
} catch {
    Write-Host "❌ VAPI health check failed" -ForegroundColor Red
}

# Test RAG API
try {
    $ragHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ RAG API health check passed" -ForegroundColor Green
} catch {
    Write-Host "❌ RAG API health check failed" -ForegroundColor Red
}

# Test Memory API
try {
    $memoryHealth = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get
    Write-Host "✅ Memory API health check passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Memory API health check failed" -ForegroundColor Red
}

Write-Host "`n🎤 Voice AI System is ready!" -ForegroundColor Green
Write-Host "You can now start making voice calls and testing the system." -ForegroundColor White 