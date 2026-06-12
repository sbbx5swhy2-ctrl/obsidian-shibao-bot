<#
 .SYNOPSIS
     卸载 Windows 任务计划程序每日任务
 #>

$TaskName = "Obsidian Shibao Daily Update"

Write-Host "=== 卸载每日自动任务 ===" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName" -ForegroundColor Gray
Write-Host ""

# 检查任务是否存在
$existing = schtasks /query /tn $TaskName 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[信息] 任务不存在，无需卸载。" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按 Enter 键退出"
    exit 0
}

Write-Host "将删除任务: $TaskName" -ForegroundColor Yellow
Write-Host "不会删除任何 Obsidian 文件或已生成的日报。" -ForegroundColor Cyan
$confirm = Read-Host "确认卸载？(y/N)"

if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "已取消。" -ForegroundColor Gray
    exit 0
}

schtasks /delete /tn $TaskName /f
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== 卸载成功 ===" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[错误] 卸载失败" -ForegroundColor Red
}

Write-Host ""
Read-Host "按 Enter 键退出"
