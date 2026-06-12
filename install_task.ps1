<#
 .SYNOPSIS
     安装 Windows 任务计划程序每日任务（无需管理员权限）
 #>

$TaskName = "Obsidian Shibao Daily Update"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatchFile = Join-Path $ProjectDir "run_daily.bat"

Write-Host "=== 安装每日自动任务 ===" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName" -ForegroundColor Gray
Write-Host "项目目录: $ProjectDir" -ForegroundColor Gray
Write-Host ""

# 确保 batch 文件存在
if (-not (Test-Path $BatchFile)) {
    Write-Host "[错误] 找不到 run_daily.bat" -ForegroundColor Red
    exit 1
}

# 检查 config.yaml
if (-not (Test-Path (Join-Path $ProjectDir "config.yaml"))) {
    Write-Host "[错误] 找不到 config.yaml" -ForegroundColor Red
    exit 1
}

# 读取配置获取运行时间
$RunTime = "08:30"
$configFile = Join-Path $ProjectDir "config.yaml"
if (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue) {
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Yaml
        if ($config.daily_run_time) {
            $RunTime = $config.daily_run_time
        }
    } catch { }
}

# 删除旧任务（如果存在）
schtasks /delete /tn $TaskName /f 2>$null

# 创建新任务
schtasks /create /tn $TaskName /tr "`"$BatchFile`"" /sc daily /st $RunTime /f

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== 安装成功 ===" -ForegroundColor Green
    Write-Host "任务名称: $TaskName" -ForegroundColor Gray
    Write-Host "运行时间: 每天 $RunTime" -ForegroundColor Gray
    Write-Host ""
    Write-Host "你可以在「任务计划程序」中查看和管理此任务。" -ForegroundColor Gray
    Write-Host "如需修改运行时间，编辑 config.yaml 的 daily_run_time 后重新运行此脚本。" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "[错误] 安装失败" -ForegroundColor Red
}

Write-Host ""
Read-Host "按 Enter 键退出"
