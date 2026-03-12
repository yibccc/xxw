# 定时器服务 (Timer Service)

一个基于 Flask + Vue 3 的定时器管理系统，支持一次性定时器和每日定时器，并提供实时事件推送功能。

## 功能特性

- ✅ 用户注册与登录（JWT 认证）
- ✅ 一次性定时器（once）：延迟 N 秒后触发
- ✅ 每日定时器（daily）：每天指定时间触发
- ✅ 定时器 CRUD（创建、查看、编辑、删除）
- ✅ 定时器创建后自动启用
- ✅ 事件历史记录与已读/未读状态管理
- ✅ SSE 实时推送定时器触发事件
- ✅ Vue 3 前端界面

## 技术栈

### 后端

- **Python** 3.11+
- **Flask** 3.1 - Web 框架
- **SQLAlchemy** 2.0 - ORM
- **Alembic** - 数据库迁移
- **APScheduler** 3.11 - 定时任务调度
- **PyJWT** - JWT 认证
- **Passlib** - 密码哈希（bcrypt）

### 前端

- **Vue** 3
- **Vite** - 构建工具
- **Vue Router** 4 - 路由管理
- **Axios** - HTTP 客户端

### 数据库

- **MySQL** 8.0+

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd xxw
```

### 2. 安装后端依赖

```bash
# 使用 uv（推荐）
uv sync
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 数据库配置（必须修改）
DATABASE_URL=mysql+pymysql://username:password@host:port/timerservice?charset=utf8mb4

# JWT 密钥（建议修改为随机字符串）
JWT_SECRET=your-random-secret-key

# 服务器配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 4. 初始化数据库

```bash
# 创建数据库（MySQL）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS timerservice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 生成迁移文件（会自动检测模型,已生成，下面的命令不可使用时重新使用这条命令生成）
uv run alembic revision --autogenerate -m "init tables"

# 执行迁移
uv run alembic upgrade head
```

### 5. 启动后端服务

```bash
uv run python main.py
```

后端将运行在 `http://localhost:5000`

### 6. 安装前端依赖

```bash
cd frontend
npm install
```

### 7. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

前端将运行在 `http://localhost:5173`

## 生产部署

### 构建前端

```bash
cd frontend
npm run build
```

构建产物将输出到 `src/timerservice/static/`，由 Flask 托管。

### 启动服务

```bash
# 设置环境变量
export FLASK_ENV=production

# 启动服务
uv run python main.py
```

访问 `http://localhost:5000` 即可使用完整应用。

### Docker 部署

#### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

#### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问 `http://localhost:5000` 即可使用应用。

#### 数据持久化

MySQL 数据存储在 Docker 卷中，重启后数据不丢失。

如需完全删除数据：

```bash
docker-compose down -v
```

#### 重新构建

```bash
docker-compose build --no-cache
```

## API 文档

详细的 API 设计文档请参考 [docs/DESIGN.md](docs/DESIGN.md)。

### 主要 API 端点

| 端点 | 方法 | 说明 |
|--------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户 |
| `/api/timers` | GET/POST | 定时器列表/创建 |
| `/api/timers/:id` | GET/PATCH/DELETE | 定时器详情/更新/删除 |
| `/api/events` | GET | 事件列表 |
| `/api/events/:id/ack` | POST | 标记事件已读 |
| `/api/events/ack_all` | POST | 标记所有事件已读 |
| `/api/stream` | GET | SSE 实时推送 |

## 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_auth.py

# 查看测试覆盖率
uv run pytest --cov=src/timerservice --cov-report=html
```

## 项目结构

```
.
├── src/timerservice/       # 后端代码
│   ├── app.py              # Flask 应用工厂
│   ├── config.py            # 配置
│   ├── db.py               # 数据库会话
│   ├── models.py            # ORM 模型
│   ├── auth/               # 认证模块
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── jwt.py
│   ├── timers/             # 定时器模块
│   │   ├── routes.py
│   │   └── timecalc.py
│   ├── events/             # 事件模块
│   │   └── routes.py
│   ├── sse/                # SSE 模块
│   │   ├── routes.py
│   │   └── hub.py
│   ├── scheduler/          # 调度器模块
│   │   └── manager.py
│   └── static/             # 前端构建输出（空目录）
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── components/  # 通用组件
│   │   ├── services/    # API 服务
│   │   └── router.js    # 路由配置
│   └── vite.config.js    # Vite 配置
├── tests/                 # 测试代码
│   ├── conftest.py      # pytest 配置
│   ├── test_auth.py     # 认证测试
│   ├── test_timers.py   # 定时器测试
│   └── test_events.py   # 事件测试
├── alembic/              # Alembic 迁移
├── docs/                 # 文档
│   ├── DESIGN.md       # 设计文档
│   └── plans/          # 实现计划
├── main.py               # 应用入口
├── pyproject.toml        # Python 项目配置
├── .env                 # 环境变量（需创建）
└── .env.example          # 环境变量示例
```

## 开发说明

### 添加新的 API 路由

1. 在对应的模块下创建 `routes.py`
2. 使用 `@require_auth` 装饰器保护需要认证的路由
3. 在 `app.py` 中注册蓝图

### 添加新的前端页面

1. 在 `frontend/src/views/` 创建 `.vue` 文件
2. 在 `frontend/src/router.js` 中添加路由配置

### 数据库迁移

```bash
# 生成迁移文件
uv run alembic revision --autogenerate -m "描述"

# 应用迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
