#requires -version 5.1
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$host.UI.RawUI.WindowTitle = "DOMjudge 실행기"

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

Write-Step "Docker Desktop 확인"
$dockerReady = $false
try { docker info *> $null; $dockerReady = $true } catch { $dockerReady = $false }

if (-not $dockerReady) {
    Write-Host "Docker Desktop이 꺼져있어서 켭니다... (최대 2분 소요)"
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    $elapsed = 0
    while ($true) {
        Start-Sleep -Seconds 3
        $elapsed += 3
        try { docker info *> $null; $dockerReady = $true; break } catch {}
        if ($elapsed -ge 180) {
            Write-Host "Docker Desktop이 3분 안에 안 켜집니다. 수동으로 확인해주세요." -ForegroundColor Red
            Write-Host "흔한 원인: Docker Desktop 자체 오류 -> Docker Desktop을 직접 열어서 에러 메시지 확인"
            Read-Host "엔터를 누르면 창을 닫습니다"
            exit 1
        }
    }
    Write-Host "Docker Desktop 준비 완료"
} else {
    Write-Host "Docker Desktop 이미 실행중"
}

Write-Step "DOMjudge 컨테이너 기동"
docker compose up -d

Write-Step "domserver 준비 대기"
$elapsed = 0
while ($true) {
    try {
        $code = (Invoke-WebRequest -Uri "http://localhost:12345/api/v4" -UseBasicParsing -TimeoutSec 3).StatusCode
        if ($code -eq 200) { break }
    } catch {}
    Start-Sleep -Seconds 2
    $elapsed += 2
    if ($elapsed -ge 120) {
        Write-Host "domserver가 2분 안에 응답하지 않습니다. 'docker compose logs domserver' 로 확인하세요." -ForegroundColor Red
        Read-Host "엔터를 누르면 창을 닫습니다"
        exit 1
    }
}
Write-Host "domserver 응답 확인됨 (http://localhost:12345/)"

Write-Step "외부 접속용 Tailscale Funnel 확인"
$ts = "C:\Program Files\Tailscale\tailscale.exe"
$funnelUrl = $null
try {
    $tsStatus = & $ts status 2>&1 | Out-String
    if ($tsStatus -match "Logged out") {
        Write-Host "Tailscale에 로그인되어 있지 않습니다. 'tailscale up' 으로 직접 로그인해주세요." -ForegroundColor Yellow
    } else {
        & $ts funnel --bg 12345 2>&1 | Out-Null
        $funnelStatus = & $ts funnel status 2>&1 | Out-String
        if ($funnelStatus -match 'https://[a-z0-9.-]*\.ts\.net') {
            $funnelUrl = $Matches[0]
        }
    }
} catch {
    Write-Host "Tailscale이 설치되어 있지 않은 것 같습니다." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host " DOMjudge 준비 완료"
Write-Host "================================================" -ForegroundColor Green
Write-Host " 로컬:  http://localhost:12345/"
if ($funnelUrl) {
    Write-Host " 외부:  $funnelUrl  (고정 주소, 안 바뀜)"
} else {
    Write-Host " 외부:  Funnel 주소 확인 실패 -> 'tailscale funnel status' 직접 확인"
}
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Read-Host "엔터를 누르면 창을 닫습니다 (서버는 계속 실행됩니다)"
