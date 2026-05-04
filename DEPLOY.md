# ContentForge Tech - 部署指南

本文档提供多种部署方式，从最简单的免费方案到生产级自托管方案。

---

## 部署方式速查

| 方式 | 难度 | 成本 | 适用场景 |
|:---|:---|:---|:---|
| [Streamlit Cloud](#方式一streamlit-cloud-免费推荐) | 极简 | 免费 | 个人使用、快速验证 |
| [Docker Compose](#方式二docker-compose-推荐) | 简单 | ~$5/月 | 自托管、长期使用 |
| [云服务器](#方式三云服务器部署) | 中等 | ~$5-10/月 | 公开访问、团队协作 |
| [GitHub Codespaces](#方式四github-codespaces) | 极简 | 免费 | 开发测试 |
| [本地Python](#方式五本地python运行) | 简单 | 免费 | 本地开发 |

---

## 前置条件

所有部署方式都需要：

1. **API密钥**（至少配置一个）
   - [Anthropic Claude API](https://console.anthropic.com/) — 推荐主模型
   - [OpenAI API](https://platform.openai.com/) — 备用模型

2. **复制环境变量文件**
   ```bash
   cp .env.example .env
   # 编辑 .env 填入你的 API 密钥
   ```

---

## 方式一：Streamlit Cloud（免费，推荐）

Streamlit官方提供的免费托管服务，无需服务器，一键部署。

### 步骤

1. **Fork本仓库**到自己的GitHub账号

2. **注册Streamlit Cloud**
   - 访问 [share.streamlit.io](https://share.streamlit.io)
   - 用GitHub账号登录

3. **创建新应用**
   - 点击 "New app"
   - 选择你的Fork仓库
   - 主文件路径填写 `app.py`

4. **配置Secrets**
   - 在应用设置中找到 "Secrets"
   - 添加以下配置（至少配置一个）：
   ```toml
   # 模型优先级链（可选，默认: kimi,gemini,openai）
   MODEL_PRIORITY = "kimi,gemini,openai"

   # 月之暗面 Kimi
   KIMI_API_KEY = "your_kimi_key_here"

   # Google Gemini
   GEMINI_API_KEY = "your_gemini_key_here"

   # OpenAI
   OPENAI_API_KEY = "your_openai_key_here"
   ```

   **注意**：配置多个模型时，系统会按 `MODEL_PRIORITY` 的顺序自动尝试，失败时自动降级到下一个。

5. **部署**
   - 点击 "Deploy"
   - 等待1-2分钟，获得 `https://your-app.streamlit.app` 地址

### 限制

- 免费版：1GB内存，1个CPU
- 应用睡眠：30分钟无访问后进入睡眠，下次访问需唤醒（约10秒）
- 存储：无持久化存储

---

## 方式二：Docker Compose（推荐）

使用Docker自托管，数据完全掌控，适合长期使用。

### 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0

### 一键部署

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/contentforge-tech.git
cd contentforge-tech

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 3. 使用部署脚本（推荐）
./scripts/deploy.sh setup

# 或手动执行：
# docker-compose up -d
```

### 部署脚本命令

```bash
./scripts/deploy.sh setup     # 首次部署（检查+构建+启动）
./scripts/deploy.sh start     # 启动服务
./scripts/deploy.sh stop      # 停止服务
./scripts/deploy.sh restart   # 重启服务
./scripts/deploy.sh logs      # 查看日志
./scripts/deploy.sh update    # 更新到最新版本
./scripts/deploy.sh status    # 查看状态
./scripts/deploy.sh clean     # 清理资源
```

### Windows 用户

```powershell
# 使用 PowerShell 脚本
.\scripts\deploy.ps1 setup
```

### 访问

部署完成后访问：http://localhost:8501

---

## 方式三：云服务器部署

在阿里云、腾讯云、AWS等云服务器上部署，支持公网访问。

### 3.1 服务器准备

推荐配置：
- CPU: 1核+
- 内存: 1GB+
- 带宽: 1Mbps+
- 系统: Ubuntu 22.04 LTS

### 3.2 安装Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3.3 部署应用

```bash
# 克隆仓库
git clone https://github.com/yourname/contentforge-tech.git
cd contentforge-tech

# 配置环境变量
cp .env.example .env
nano .env  # 填入API密钥

# 启动
docker-compose up -d
```

### 3.4 配置Nginx反向代理（可选，推荐）

如需HTTPS和域名访问，配置Nginx：

```bash
# 安装Nginx
sudo apt install nginx

# 创建配置文件
sudo tee /etc/nginx/sites-available/contentforge << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# 启用配置
sudo ln -s /etc/nginx/sites-available/contentforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3.5 配置HTTPS（推荐）

使用Let's Encrypt免费证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3.6 配置防火墙

```bash
# Ubuntu UFW
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

---

## 方式四：GitHub Codespaces

适合临时测试，无需本地环境。

### 步骤

1. 打开GitHub仓库页面
2. 点击 "Code" → "Codespaces" → "Create codespace on main"
3. 等待环境启动（约1-2分钟）
4. 在终端执行：
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # 编辑 .env 填入API密钥
   streamlit run app.py
   ```
5. 点击弹出的 "Open in Browser" 链接

---

## 方式五：本地Python运行

适合开发和调试。

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/contentforge-tech.git
cd contentforge-tech

# 2. 创建虚拟环境（推荐）
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 5. 启动
streamlit run app.py
```

访问 http://localhost:8501

---

## 镜像仓库（GitHub Container Registry）

如果你不想自己构建镜像，可以直接拉取预构建镜像：

```bash
# 登录GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 拉取镜像
docker pull ghcr.io/yourname/contentforge-tech:latest

# 运行
docker run -d \
  -p 8501:8501 \
  -e ANTHROPIC_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  --name contentforge-tech \
  ghcr.io/yourname/contentforge-tech:latest
```

---

## 环境变量说明

| 变量名 | 必填 | 说明 |
|:---|:---|:---|
| `ANTHROPIC_API_KEY` | 条件必填 | Claude API密钥（推荐主模型） |
| `OPENAI_API_KEY` | 条件必填 | OpenAI API密钥（备用模型） |
| `DEFAULT_AI_MODEL` | 否 | 默认模型：`claude` 或 `openai`（默认：claude） |
| `STREAMLIT_SERVER_PORT` | 否 | 服务端口（默认：8501） |

**注意**：`ANTHROPIC_API_KEY` 和 `OPENAI_API_KEY` 至少配置一个。

---

## 故障排查

### 问题：容器启动失败

```bash
# 查看日志
docker-compose logs -f

# 常见原因：
# 1. API密钥未配置 → 检查 .env 文件
# 2. 端口被占用 → 修改 docker-compose.yml 中的端口映射
```

### 问题：无法访问Web界面

```bash
# 检查容器状态
docker-compose ps

# 检查端口监听
netstat -tlnp | grep 8501

# 如果是云服务器，检查安全组/防火墙是否放行8501端口
```

### 问题：API调用失败

```bash
# 检查API密钥是否有效
curl https://api.anthropic.com/v1/models \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"

# 如果返回401，密钥无效或余额不足
```

### 问题：内存不足

```bash
# 修改docker-compose.yml中的内存限制
deploy:
  resources:
    limits:
      memory: 1G  # 增加内存限制
```

---

## 更新指南

### 使用部署脚本更新

```bash
./scripts/deploy.sh update
```

### 手动更新

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重建并重启
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 保留数据更新

```bash
# 仅更新镜像，保留容器状态
docker-compose pull
docker-compose up -d
```

---

## 安全建议

1. **API密钥保护**
   - 不要将 `.env` 文件提交到Git仓库（已在 `.gitignore` 中配置）
   - 定期轮换API密钥
   - 为API密钥设置使用限额

2. **访问控制**
   - 公网部署时建议配置Nginx Basic Auth
   - 使用HTTPS（Let's Encrypt免费证书）
   - 限制IP访问（如需）

3. **容器安全**
   - Dockerfile中使用非root用户运行应用
   - 定期更新基础镜像：`docker-compose pull && docker-compose up -d`

---

## 性能优化

| 优化项 | 方法 |
|:---|:---|
| 启动速度 | 使用预构建镜像，避免本地build |
| 内存使用 | 限制容器内存为512MB-1GB |
| API成本 | 启用缓存（后续版本支持） |
| 并发处理 | 使用多worker（Streamlit不支持，需配合Nginx） |

---

## 支持的部署平台

| 平台 | 部署方式 | 文档 |
|:---|:---|:---|
| **Streamlit Cloud** | GitHub集成 | [官方文档](https://docs.streamlit.io/deploy/streamlit-community-cloud) |
| **Docker** | 自托管 | 本文档 |
| **AWS EC2** | Docker Compose | [AWS文档](https://aws.amazon.com/ec2/) |
| **阿里云ECS** | Docker Compose | [阿里云文档](https://www.aliyun.com/product/ecs) |
| **腾讯云CVM** | Docker Compose | [腾讯云文档](https://cloud.tencent.com/product/cvm) |
| **Railway** | Dockerfile | [Railway文档](https://docs.railway.app/) |
| **Render** | Dockerfile | [Render文档](https://render.com/docs) |

---

## 需要帮助？

- 查看 [README.md](README.md) 了解项目功能
- 提交 [Issue](https://github.com/yourname/contentforge-tech/issues)
- 参考 [Streamlit部署文档](https://docs.streamlit.io/deploy)
