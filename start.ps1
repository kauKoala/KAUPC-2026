#requires -version 5.1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[1/4] mariadb + domserver 기동..."
docker compose up -d mariadb domserver

Write-Host "[2/4] domserver 초기화 대기 (초기 비밀번호 파일 생성까지, 최대 3분)..."
$adminSecretPath = ""
for ($i = 0; $i -lt 60; $i++) {
    $exists = docker compose exec -T domserver test -f /opt/domjudge/domserver/etc/initial_admin_password.secret 2>$null
    if ($LASTEXITCODE -eq 0) { $adminSecretPath = "ok"; break }
    Start-Sleep -Seconds 3
}
if ($adminSecretPath -ne "ok") {
    Write-Error "domserver 초기화 시간 초과. 'docker compose logs domserver' 로 확인하세요."
}

$adminPw = (docker compose exec -T domserver cat /opt/domjudge/domserver/etc/initial_admin_password.secret).Trim()
$restapiSecret = (docker compose exec -T domserver cat /opt/domjudge/domserver/etc/restapi.secret).Trim()
# restapi.secret 형식: <endpoint-id> <url> <username> <password>
$judgePw = ($restapiSecret -split '\s+')[-1]

Write-Host "[3/4] .env 파일 작성..."
$envContent = @"
DOMJUDGE_PORT=12345
MYSQL_ROOT_PASSWORD=domjudge_root
MYSQL_PASSWORD=domjudge_pw
JUDGEDAEMON_PASSWORD=$judgePw
"@
Set-Content -Path "$PSScriptRoot\.env" -Value $envContent -Encoding utf8NoBOM

Write-Host "[4/4] judgehost 기동..."
docker compose up -d judgehost

Write-Host ""
Write-Host "=== 완료 ==="
Write-Host "웹: http://localhost:12345/  (외부: README.md의 공인 IP 참고)"
Write-Host "admin 계정 비밀번호: $adminPw"
Write-Host "judgehost 비밀번호(.env에 저장됨): $judgePw"
