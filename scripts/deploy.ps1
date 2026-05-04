# ContentForge Tech - Windows PowerShell 部署脚本
# 支持：本地Docker / 云服务器 / 一键安装

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          ContentForge Tech - 部署脚本                       ║" -ForegroundColor Cyan
    Write-Host "║          技术博客多平台内容生成器                            ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Yellow }

# 检查依赖
function Check-Dependencies {
    Write-Info "检查依赖..."

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker 未安装"
        Write-Host "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    }

    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose 未安装"
        Write-Host "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    }

    Write-Success "依赖检查通过"
}

# 检查环境变量
function Check-Env {
    Write-Info "检查环境变量..."

    if (-not (Test-Path "$ProjectDir\.env")) {
        Write-Error ".env 文件不存在"
        Write-Host ""
        Write-Host "请执行以下步骤："
        Write-Host "  1. Copy-Item .env.example .env"
        Write-Host "  2. 编辑 .env 文件，填入你的 API 密钥"
        Write-Host ""
        exit 1
    }

    $envContent = Get-Content "$ProjectDir\.env" -Raw
    if (-not ($envContent -match "ANTHROPIC_API_KEY=sk-") -and -not ($envContent -match "OPENAI_API_KEY=sk-")) {
        Write-Error ".env 文件中未配置有效的 API 密钥"
        Write-Host "请确保至少配置了 ANTHROPIC_API_KEY 或 OPENAI_API_KEY"
        exit 1
    }

    Write-Success "环境变量检查通过"
}

# 构建镜像
function Build-Image {
    Write-Info "构建 Docker 镜像..."
    Set-Location $ProjectDir
    docker-compose build --no-cache
    Write-Success "镜像构建完成"
}

# 启动服务
function Start-Service {
    Write-Info "启动 ContentForge Tech..."
    Set-Location $ProjectDir
    docker-compose up -d
    Write-Success "服务已启动"
    Write-Host ""
    Write-Host "访问地址: http://localhost:8501" -ForegroundColor Green
    Write-Host ""
}

# 停止服务
function Stop-Service {
    Write-Info "停止 ContentForge Tech..."
    Set-Location $ProjectDir
    docker-compose down
    Write-Success "服务已停止"
}

# 查看日志
function Show-Logs {
    Set-Location $ProjectDir
    docker-compose logs -f --tail=100
}

# 重启服务
function Restart-Service {
    Stop-Service
    Start-Service
}

# 状态检查
function Show-Status {
    Set-Location $ProjectDir
    docker-compose ps
}

# 清理
function Clean-Resources {
    Write-Info "清理 Docker 资源..."
    Set-Location $ProjectDir
    docker-compose down -v --remove-orphans
    docker system prune -f
    Write-Success "清理完成"
}

# 显示帮助
function Show-Help {
    Write-Host "ContentForge Tech 部署脚本 (PowerShell)"
    Write-Host ""
    Write-Host "用法: .\scripts\deploy.ps1 [命令]"
    Write-Host ""
    Write-Host "命令:"
    Write-Host "  setup     首次部署（检查环境 + 构建 + 启动）"
    Write-Host "  build     构建 Docker 镜像"
    Write-Host "  start     启动服务"
    Write-Host "  stop      停止服务"
    Write-Host "  restart   重启服务"
    Write-Host "  logs      查看日志"
    Write-Host "  status    查看服务状态"
    Write-Host "  clean     清理 Docker 资源"
    Write-Host "  help      显示帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\scripts\deploy.ps1 setup    # 首次部署"
}

# 主逻辑
Write-Banner

$Command = if ($args.Length -gt 0) { $args[0] } else { "setup" }

switch ($Command) {
    "setup" {
        Check-Dependencies
        Check-Env
        Build-Image
        Start-Service
    }
    "build" {
        Check-Dependencies
        Build-Image
    }
    "start" {
        Check-Dependencies
        Check-Env
        Start-Service
    }
    "stop" {
        Stop-Service
    }
    "restart" {
        Check-Dependencies
        Restart-Service
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Show-Status
    }
    "clean" {
        Clean-Resources
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "未知命令: $Command"
        Show-Help
        exit 1
    }
}
