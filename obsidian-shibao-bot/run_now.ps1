<#
 .SYNOPSIS
     手动立即运行一次时报机器人
 #>

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatchFile = Join-Path $ProjectDir "run_daily.bat"

Write-Host "=== 时报机器人 - 手动运行 ===" -ForegroundColor Cyan
Write-Host "项目目录: $ProjectDir" -ForegroundColor Gray
Write-Host ""

# 检查依赖
$requirementsFile = Join-Path $ProjectDir "requirements.txt"
$needInstall = $false
if (Test-Path $requirementsFile) {
    try {
        pip show requests >$null 2>&1
        if ($LASTEXITCODE -ne 0) { $needInstall = $true }
    } catch { $needInstall = $true }
    if ($needInstall) {
        Write-Host "[信息] 安装依赖..." -ForegroundColor Cyan
        pip install -r $requirementsFile -q
    }
}

# 运行
if (Test-Path $BatchFile) {
    & $BatchFile
    $exitCode = $LASTEXITCODE
} else {
    cd $ProjectDir
    python -m src.main
    $exitCode = $LASTEXITCODE
}

Write-Host ""

if ($exitCode -eq 0) {
    Write-Host "=== 运行成功 ===" -ForegroundColor Green
} else {
    Write-Host "=== 运行完成 (退出码: $exitCode) ===" -ForegroundColor Yellow
    Write-Host "查看日志: $ProjectDir\logs\$(Get-Date -Format 'yyyy-MM-dd').log" -ForegroundColor Gray
}

Write-Host ""
Read-Host "按 Enter 键退出"
