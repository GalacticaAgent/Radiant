# Radiant（元光体）阿里云上线 Runbook（Ubuntu 24.04｜2C2G｜无 Docker）

适用场景：
- ECS：Ubuntu 24.04（2 vCPU / 2 GiB / 40 GiB）
- 域名：ai4research.com.cn + www.ai4research.com.cn（已备案）
- 部署方式：Nginx + HTTPS（Let’s Encrypt），前端静态文件，后端 FastAPI（systemd），PostgreSQL/Redis/Neo4j 同机，Neo4j 通过 SSH 隧道远程管理

## 0. 必要前提
- DNS：`ai4research.com.cn` 的 A 记录指向 ECS 公网 IP（`www` 可先不配，后续补齐再签包含 www 的证书）
- 安全组：仅放行 22/80/443；不放行 5432/6379/7474/7687/8000
- DeepSeek 连通性：`curl -I https://api.deepseek.com` 能返回（401/200 均可，代表链路通）

## 1. 机器初始化（强烈推荐）

### 1.1 系统更新 + 基础工具
```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install nginx git curl ca-certificates ufw
sudo systemctl enable --now nginx
```

### 1.2 启用 UFW（可选但推荐）
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
sudo ufw status
```

### 1.3 2C2G 必备：加 Swap（避免 Neo4j/Postgres OOM）
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 2. 安装并配置 PostgreSQL（同机）

### 2.1 安装
```bash
sudo apt -y install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
psql --version
```

### 2.2 安装 pgvector 扩展（满足后端启动时 CREATE EXTENSION vector）
说明：Ubuntu 24.04 默认常见为 PostgreSQL 16，对应包通常是 `postgresql-16-pgvector`。
```bash
sudo apt -y install postgresql-16-pgvector || true
```

### 2.3 创建数据库与用户
```bash
sudo -u postgres psql -c "CREATE DATABASE radiant;"
sudo -u postgres psql -c "CREATE USER radiant_user WITH ENCRYPTED PASSWORD 'CHANGE_ME_STRONG';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE radiant TO radiant_user;"
```

### 2.4 只监听本机（避免暴露到公网）
编辑 `/etc/postgresql/*/main/postgresql.conf`：
- `listen_addresses = '127.0.0.1'`

编辑 `/etc/postgresql/*/main/pg_hba.conf`：确保只允许本机连接（按实际文件为准）。

重启：
```bash
sudo systemctl restart postgresql
```

## 3. 安装并配置 Redis（同机）
```bash
sudo apt -y install redis-server
sudo systemctl enable --now redis-server
sudo systemctl status redis-server --no-pager
```

## 4. 安装并配置 Neo4j（必须上线｜SSH 隧道远程管理）

### 4.1 安装 Neo4j 5.x（示例锁定到 5.14）
```bash
curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/neo4j.gpg
echo "deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable 5" | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt -y install neo4j=1:5.14.0
sudo systemctl enable --now neo4j
```

### 4.2 设置初始密码（只需一次）
```bash
sudo neo4j-admin dbms set-initial-password 'CHANGE_ME_STRONG'
```

### 4.3 2G 内存降配 + 仅本机监听（关键）
编辑 `/etc/neo4j/neo4j.conf`：
```ini
server.default_listen_address=127.0.0.1
server.default_advertised_address=127.0.0.1

server.memory.heap.initial_size=256m
server.memory.heap.max_size=512m
server.memory.pagecache.size=256m
```

重启并检查：
```bash
sudo systemctl restart neo4j
sudo systemctl status neo4j --no-pager
curl -I http://127.0.0.1:7474 || true
```

### 4.4 远程管理 Neo4j（本地电脑执行）
Windows PowerShell 示例：
```powershell
ssh -L 7474:127.0.0.1:7474 -L 7687:127.0.0.1:7687 root@<你的ECS公网IP>
```
浏览器打开：`http://localhost:7474`，连接：`bolt://localhost:7687`

## 5. 部署后端（FastAPI + systemd）

### 5.1 安装运行依赖（含 LibreOffice 用于 .doc 转换）
```bash
sudo apt -y install python3-venv python3-pip build-essential libreoffice-writer fonts-dejavu fonts-liberation
```

### 5.2 创建运行用户（推荐）
```bash
sudo useradd -r -m -d /opt/radiant -s /usr/sbin/nologin radiant || true
sudo mkdir -p /opt/radiant /var/lib/radiant/uploads
sudo chown -R radiant:radiant /opt/radiant /var/lib/radiant
```

### 5.3 拉代码（放到 /opt/radiant）
```bash
sudo -u radiant -H bash -lc "cd /opt/radiant && git clone <你的仓库地址> ."
```

### 5.4 安装 Python 依赖
```bash
sudo -u radiant -H bash -lc "cd /opt/radiant/backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"
```

### 5.5 配置后端环境变量（/opt/radiant/backend/.env）
```env
SECRET_KEY=CHANGE_ME_LONG_RANDOM
DEEPSEEK_API_KEY=你的key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

POSTGRES_SERVER=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=radiant_user
POSTGRES_PASSWORD=CHANGE_ME_STRONG
POSTGRES_DB=radiant

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
CELERY_RUN_INLINE=True

NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=CHANGE_ME_STRONG

UPLOAD_DIR=/var/lib/radiant/uploads
FORMAT_AUTOFIX_ENABLED=True
VIRUS_SCAN_ENABLED=False
```

注意：`SECRET_KEY` 必须改为随机长字符串（生产环境不可用默认值）。

### 5.6 创建 systemd 服务
创建 `/etc/systemd/system/radiant-backend.service`：
```ini
[Unit]
Description=Radiant Backend (FastAPI)
After=network.target postgresql.service redis-server.service neo4j.service

[Service]
Type=simple
User=radiant
Group=radiant
WorkingDirectory=/opt/radiant/backend
EnvironmentFile=/opt/radiant/backend/.env
ExecStart=/opt/radiant/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now radiant-backend
sudo systemctl status radiant-backend --no-pager
curl -s http://127.0.0.1:8000/health
```

## 6. 部署前端（静态文件 + Nginx）

### 6.1 本地构建
在你的本机：
```bash
cd frontend
npm ci
npm run build
```
生成 `frontend/dist/`

### 6.2 上传到服务器（/var/www/radiant）
```bash
sudo mkdir -p /var/www/radiant
sudo chown -R www-data:www-data /var/www/radiant
```
用 scp/rsync 把 dist 内容上传到 `/var/www/radiant/`。

## 7. Nginx（先 HTTP 跑通 → 再签证书 → 再开启 HTTPS 与跳转）

重要：在证书还没签发之前，不要先写 `listen 443 ssl` 且引用 `/etc/letsencrypt/live/...` 的证书路径，否则 Nginx 可能无法通过 `nginx -t`，导致 Certbot 验证失败。

### 7.1 阶段一：HTTP 站点（用于签发证书）
创建 `/etc/nginx/sites-available/ai4research.com.cn`：
```nginx
server {
    listen 80;
    server_name ai4research.com.cn www.ai4research.com.cn;

    client_max_body_size 60m;

    root /var/www/radiant;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /api/v1/chat/stream {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300;
    }
}
```

启用：
```bash
sudo ln -sf /etc/nginx/sites-available/ai4research.com.cn /etc/nginx/sites-enabled/ai4research.com.cn
sudo nginx -t
sudo systemctl reload nginx
```

## 8. HTTPS（Let’s Encrypt）
```bash
sudo apt -y install certbot python3-certbot-nginx
sudo certbot --nginx -d ai4research.com.cn -d www.ai4research.com.cn
sudo certbot renew --dry-run
```

### 8.1 阶段二：开启 HTTPS 与跳转（签证书后）
证书签发成功后，将 Nginx 配置替换为“HTTP→HTTPS + www→主域名”的版本（示例）：
```nginx
server {
    listen 80;
    server_name ai4research.com.cn www.ai4research.com.cn;
    return 301 https://ai4research.com.cn$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.ai4research.com.cn;

    ssl_certificate     /etc/letsencrypt/live/ai4research.com.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai4research.com.cn/privkey.pem;

    return 301 https://ai4research.com.cn$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ai4research.com.cn;

    ssl_certificate     /etc/letsencrypt/live/ai4research.com.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai4research.com.cn/privkey.pem;

    client_max_body_size 60m;

    root /var/www/radiant;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /api/v1/chat/stream {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300;
    }
}
```

应用：
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 9. 上线验收清单
- 服务状态：
  - `systemctl status postgresql redis-server neo4j radiant-backend --no-pager`
  - `curl -s http://127.0.0.1:8000/health`
- Nginx：
  - `curl -I http://ai4research.com.cn` 应 301 到 https
  - `curl -I https://ai4research.com.cn` 应 200/304
- Neo4j 管理：
  - 本地 SSH 隧道后打开 `http://localhost:7474`
- 功能冒烟：
  - 登录
  - 上传论文
  - 触发模拟审稿/格式审查任一任务

## 10. 常用排错命令
- 后端日志：`sudo journalctl -u radiant-backend -n 200 --no-pager`
- Nginx 日志：`sudo tail -n 200 /var/log/nginx/error.log`
- Postgres：`sudo journalctl -u postgresql -n 200 --no-pager`
- Neo4j：`sudo journalctl -u neo4j -n 200 --no-pager`
