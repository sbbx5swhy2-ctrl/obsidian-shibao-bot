 <#
 .SYNOPSIS
     打开今天生成的日报文件
 #>
 
 $ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
 $ConfigPath = Join-Path $ProjectDir "config.yaml"
 
 Write-Host "=== 打开今日日报 ===" -ForegroundColor Cyan
 
 # 读取配置
 if (-not (Test-Path $ConfigPath)) {
     Write-Host "[错误] 找不到 config.yaml" -ForegroundColor Red
     exit 1
 }
 
 if (-not (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue)) {
     Write-Host "[错误] 需要 PowerShell 7+ 或安装 powershell-yaml 模块。" -ForegroundColor Red
     Write-Host "请手动打开 Obsidian 时报文件夹。" -ForegroundColor Yellow
     exit 1
 }
 
 try {
     $config = Get-Content $ConfigPath -Raw | ConvertFrom-Yaml
 } catch {
     Write-Host "[错误] 读取 config.yaml 失败: $_" -ForegroundColor Red
     exit 1
 }
 
 $vaultPath = $config.vault_path
 $rootFolder = $config.root_folder
 
 if (-not $vaultPath -or $vaultPath -eq "OBSIDIAN_VAULT_PATH") {
     Write-Host "[错误] vault_path 未设置。请先在 config.yaml 中配置。" -ForegroundColor Red
     exit 1
 }
 
 if (-not (Test-Path $vaultPath)) {
     Write-Host "[错误] vault_path 不存在: $vaultPath" -ForegroundColor Red
     Write-Host "请检查 iCloud Drive 是否已同步到本机。" -ForegroundColor Yellow
     exit 1
 }
 
 $today = Get-Date -Format "yyyy-MM-dd"
 $year = $today.Split("-")[0]
 $month = $today.Split("-")[1]
 $mdFile = Join-Path $vaultPath "$rootFolder\$year\$month\$today.md"
 $indexFile = Join-Path $vaultPath "$rootFolder\$($rootFolder)首页.md"
 
 # 检查日报文件是否存在
 if (Test-Path $mdFile) {
     Write-Host "打开文件: $mdFile" -ForegroundColor Green
     Invoke-Item $mdFile
 } else {
     Write-Host "[提示] 今日日报文件不存在: $mdFile" -ForegroundColor Yellow
     Write-Host "请先运行 run_now.ps1 生成日报。" -ForegroundColor Cyan
     
     # 如果首页存在，打开首页所在目录
     $rootPath = Join-Path $vaultPath $rootFolder
     if (Test-Path $rootPath) {
         Write-Host "打开时报文件夹: $rootPath" -ForegroundColor Gray
         Invoke-Item $rootPath
     } elseif (Test-Path $indexFile) {
         Write-Host "打开首页: $indexFile" -ForegroundColor Gray
         Invoke-Item $indexFile
     } else {
         Write-Host "打开仓库: $vaultPath" -ForegroundColor Gray
         Invoke-Item $vaultPath
     }
 }
 
 Write-Host ""
 Read-Host "按 Enter 键退出"
