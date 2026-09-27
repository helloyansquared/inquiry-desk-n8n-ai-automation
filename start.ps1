$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
try {
    $status = Invoke-RestMethod 'http://127.0.0.1:8769/health' -TimeoutSec 2
    if ($status.ok) { Write-Output 'Already running: http://127.0.0.1:8769'; exit 0 }
} catch {}
Start-Process -FilePath (Get-Command python).Source -ArgumentList @((Join-Path $projectDir 'app.py')) -WorkingDirectory $projectDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectDir 'server.log') -RedirectStandardError (Join-Path $projectDir 'server-error.log')
Write-Output 'Started: http://127.0.0.1:8769'
