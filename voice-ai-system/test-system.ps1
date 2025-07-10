# Voice AI System Test Script
# Comprehensive testing of all system components

param(
    [switch]$FullTest,
    [switch]$QuickTest,
    [string]$TestUser = "test_user_123"
)

Write-Host "🧪 Voice AI System Test Script" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Test configuration
$baseUrl = "http://localhost"
$testData = @{
    user_id = $TestUser
    query = "What is the company refund policy?"
    phone_number = "+1234567890"
    call_id = "test_call_$(Get-Date -Format 'yyyyMMddHHmmss')"
}

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = 10
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "✅ $Name - PASSED" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ $Name - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to test API with response validation
function Test-API {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null,
        [scriptblock]$Validation = { $true }
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = 10
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        
        if (& $Validation $response) {
            Write-Host "✅ $Name - PASSED" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  $Name - PARTIAL: Response validation failed" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ $Name - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test Results
$testResults = @{
    Total = 0
    Passed = 0
    Failed = 0
    Partial = 0
}

function Add-TestResult {
    param([bool]$Success, [bool]$Partial = $false)
    
    $testResults.Total++
    if ($Success) {
        if ($Partial) {
            $testResults.Partial++
        } else {
            $testResults.Passed++
        }
    } else {
        $testResults.Failed++
    }
}

Write-Host "`n🔍 Testing System Health..." -ForegroundColor Yellow

# Test 1: VAPI Health
$result = Test-Endpoint "VAPI Health" "$baseUrl:3000/health"
Add-TestResult $result

# Test 2: n8n Health
$result = Test-Endpoint "n8n Health" "$baseUrl:5678/healthz"
Add-TestResult $result

# Test 3: RAG Health
$result = Test-Endpoint "RAG Health" "$baseUrl:8000/health"
Add-TestResult $result

# Test 4: Memory Health
$result = Test-Endpoint "Memory Health" "$baseUrl:8001/health"
Add-TestResult $result

Write-Host "`n🧠 Testing Memory System..." -ForegroundColor Yellow

# Test 5: Get User Memory (should create new user)
$memoryBody = @{
    user_id = $testData.user_id
    conversation_history = @(
        @{
            role = "user"
            content = "Hello, I need help with a refund"
            timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
        }
    )
    preferences = @{
        language = "en"
        voice_speed = 1.0
        voice_model = "alloy"
    }
}

$result = Test-API "Create User Memory" "$baseUrl:8001/memory/$($testData.user_id)" "POST" $memoryBody
Add-TestResult $result

# Test 6: Get User Memory
$result = Test-API "Get User Memory" "$baseUrl:8001/memory/$($testData.user_id)" "GET" $null { param($r) $r.user_id -eq $testData.user_id }
Add-TestResult $result

# Test 7: Update User Preferences
$preferencesBody = @{
    language = "en"
    voice_speed = 1.2
    voice_model = "echo"
    interruption_threshold = 0.3
}

$result = Test-API "Update User Preferences" "$baseUrl:8001/memory/$($testData.user_id)/preferences" "PUT" $preferencesBody
Add-TestResult $result

Write-Host "`n📚 Testing RAG System..." -ForegroundColor Yellow

# Test 8: RAG Query
$ragBody = @{
    query = $testData.query
    user_id = $testData.user_id
    max_results = 3
}

$result = Test-API "RAG Query" "$baseUrl:8000/rag/query" "POST" $ragBody { param($r) $r.answer -and $r.confidence -ge 0 }
Add-TestResult $result

# Test 9: RAG Search
$result = Test-API "RAG Search" "$baseUrl:8000/rag/search" "POST" "refund policy" { param($r) $r.results -ne $null }
Add-TestResult $result

# Test 10: List Documents
$result = Test-API "List Documents" "$baseUrl:8000/rag/documents" "GET" $null { param($r) $r.documents -ne $null }
Add-TestResult $result

Write-Host "`n🔗 Testing n8n Webhooks..." -ForegroundColor Yellow

# Test 11: n8n Voice Webhook
$webhookBody = @{
    event = "call_started"
    call_id = $testData.call_id
    user_id = $testData.user_id
    phone_number = $testData.phone_number
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
}

$result = Test-Endpoint "n8n Voice Webhook" "$baseUrl:5678/webhook/voice-trigger" "POST" $webhookBody
Add-TestResult $result

# Test 12: n8n Customer Service Webhook
$csWebhookBody = @{
    event = "transcript"
    call_id = $testData.call_id
    user_id = $testData.user_id
    transcript = "I need help with a refund"
    confidence = 0.95
    speaker = "user"
}

$result = Test-Endpoint "n8n Customer Service Webhook" "$baseUrl:5678/webhook/customer-service" "POST" $csWebhookBody
Add-TestResult $result

Write-Host "`n📊 Testing Monitoring..." -ForegroundColor Yellow

# Test 13: Grafana Dashboard
$result = Test-Endpoint "Grafana Dashboard" "$baseUrl:3001" "GET"
Add-TestResult $result

# Test 14: Kibana Dashboard
$result = Test-Endpoint "Kibana Dashboard" "$baseUrl:5601" "GET"
Add-TestResult $result

# Test 15: System Stats
$result = Test-API "Memory Stats" "$baseUrl:8001/memory/stats" "GET" $null { param($r) $r.total_users -ge 0 }
Add-TestResult $result

Write-Host "`n🎤 Testing Voice Integration..." -ForegroundColor Yellow

# Test 16: VAPI Assistant List (if API key is configured)
if ($env:VAPI_API_KEY -and $env:VAPI_API_KEY -ne "your_vapi_api_key_here") {
    try {
        $headers = @{
            "Authorization" = "Bearer $env:VAPI_API_KEY"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri "https://api.vapi.ai/assistants" -Headers $headers -Method Get
        Write-Host "✅ VAPI Assistants - PASSED" -ForegroundColor Green
        Add-TestResult $true
    } catch {
        Write-Host "❌ VAPI Assistants - FAILED: $($_.Exception.Message)" -ForegroundColor Red
        Add-TestResult $false
    }
} else {
    Write-Host "⚠️  VAPI Assistants - SKIPPED (API key not configured)" -ForegroundColor Yellow
    Add-TestResult $false
}

# Test 17: Memory Cleanup
$result = Test-API "Memory Cleanup" "$baseUrl:8001/memory/cleanup" "POST" $null
Add-TestResult $result

Write-Host "`n📋 Test Summary" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan
Write-Host "Total Tests:    $($testResults.Total)" -ForegroundColor White
Write-Host "Passed:         $($testResults.Passed)" -ForegroundColor Green
Write-Host "Partial:        $($testResults.Partial)" -ForegroundColor Yellow
Write-Host "Failed:         $($testResults.Failed)" -ForegroundColor Red

$successRate = if ($testResults.Total -gt 0) { [math]::Round(($testResults.Passed / $testResults.Total) * 100, 1) } else { 0 }
Write-Host "Success Rate:   $successRate%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })

if ($testResults.Failed -eq 0) {
    Write-Host "`n🎉 All tests passed! Voice AI system is ready for use." -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Please check the logs and configuration." -ForegroundColor Yellow
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Review failed tests and fix issues" -ForegroundColor White
Write-Host "2. Configure API keys in .env file" -ForegroundColor White
Write-Host "3. Test with actual voice calls" -ForegroundColor White
Write-Host "4. Monitor system performance" -ForegroundColor White
Write-Host "5. Set up alerts and notifications" -ForegroundColor White 