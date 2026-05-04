#!/bin/bash
set -e

# ContentForge Tech - 部署脚本
# 支持：本地Docker / 云服务器 / 一键安装

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          ContentForge Tech - 部署脚本                       ║${NC}"
    echo -e "${BLUE}║          技术博客多平台内容生成器                            ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi

    print_success "依赖检查通过"
}

# 检查环境变量
check_env() {
    print_info "检查环境变量..."

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        print_error ".env 文件不存在"
        echo ""
        echo "请执行以下步骤："
        echo "  1. cp .env.example .env"
        echo "  2. 编辑 .env 文件，填入你的 API 密钥"
        echo ""
        exit 1
    fi

    # 检查是否有API密钥
    if ! grep -q "ANTHROPIC_API_KEY=sk-" "$PROJECT_DIR/.env" 2>/dev/null && ! grep -q "OPENAI_API_KEY=sk-" "$PROJECT_DIR/.env" 2>/dev/null; then
        print_error ".env 文件中未配置有效的 API 密钥"
        echo "请确保至少配置了 ANTHROPIC_API_KEY 或 OPENAI_API_KEY"
        exit 1
    fi

    print_success "环境变量检查通过"
}

# 构建镜像
build() {
    print_info "构建 Docker 镜像..."
    cd "$PROJECT_DIR"
    docker-compose build --no-cache
    print_success "镜像构建完成"
}

# 启动服务
start() {
    print_info "启动 ContentForge Tech..."
    cd "$PROJECT_DIR"
    docker-compose up -d
    print_success "服务已启动"
    echo ""
    echo -e "${GREEN}访问地址: http://localhost:8501${NC}"
    echo ""
}

# 停止服务
stop() {
    print_info "停止 ContentForge Tech..."
    cd "$PROJECT_DIR"
    docker-compose down
    print_success "服务已停止"
}

# 查看日志
logs() {
    cd "$PROJECT_DIR"
    docker-compose logs -f --tail=100
}

# 重启服务
restart() {
    stop
    start
}

# 更新（拉取最新代码并重建）
update() {
    print_info "更新 ContentForge Tech..."
    cd "$PROJECT_DIR"

    # 备份 .env
    if [ -f ".env" ]; then
        cp .env .env.backup
        print_info "已备份 .env 到 .env.backup"
    fi

    # 拉取最新代码（如果是git仓库）
    if [ -d ".git" ]; then
        git pull origin main || git pull origin master
    fi

    # 重建并启动
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d

    print_success "更新完成"
}

# 状态检查
status() {
    cd "$PROJECT_DIR"
    docker-compose ps
}

# 清理
clean() {
    print_info "清理 Docker 资源..."
    cd "$PROJECT_DIR"
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_success "清理完成"
}

# 显示帮助
help() {
    echo "ContentForge Tech 部署脚本"
    echo ""
    echo "用法: ./scripts/deploy.sh [命令]"
    echo ""
    echo "命令:"
    echo "  setup     首次部署（检查环境 + 构建 + 启动）"
    echo "  build     构建 Docker 镜像"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  logs      查看日志"
    echo "  update    更新到最新版本"
    echo "  status    查看服务状态"
    echo "  clean     清理 Docker 资源"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/deploy.sh setup    # 首次部署"
    echo "  ./scripts/deploy.sh update   # 更新版本"
}

# 主逻辑
main() {
    print_banner

    case "${1:-setup}" in
        setup)
            check_dependencies
            check_env
            build
            start
            ;;
        build)
            check_dependencies
            build
            ;;
        start)
            check_dependencies
            check_env
            start
            ;;
        stop)
            stop
            ;;
        restart)
            check_dependencies
            restart
            ;;
        logs)
            logs
            ;;
        update)
            check_dependencies
            update
            ;;
        status)
            status
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            help
            ;;
        *)
            print_error "未知命令: $1"
            help
            exit 1
            ;;
    esac
}

main "$@"
