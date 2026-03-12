# Docker Compose 部署方案

## 概述

使用 Docker Compose 部署 xxw-task 定时器服务，包含 MySQL 数据库、Flask 后端和 Vue 前端。

## 架构设计

```
┌─────────────────────────────────────┐
│         Docker Compose              │
├─────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐ │
│  │   MySQL     │   │  Backend    │ │
│  │  (持久化)   │◄──│  (Flask)    │ │
│  └─────────────┘   └─────────────┘ │
│                            │        │
│                     ┌──────▼──────┐ │
│                     │  Frontend   │ │
│                     │  (静态文件)  │ │
│                     └─────────────┘ │
└─────────────────────────────────────┘
         │
    ./data/mysql (持久化目录)
```

## 服务配置

### MySQL 服务

- 镜像: `mysql:8.0`
- 端口: 3306
- 数据持久化: `./data/mysql`
- 初始化: 创建 `timerservice` 数据库

### Backend 服务

- 镜像: 自定义 Dockerfile
- 基础镜像: Python 3.11-slim
- 依赖: 安装 pyproject.toml 中的依赖
- 启动命令: 运行 Alembic 迁移后启动 Flask
- 环境变量: 生产模式配置

### Frontend 服务

- 镜像: 自定义 Dockerfile
- 基础镜像: Node.js 20
- 构建: `npm run build`
- 输出: 构建产物到 `../src/timerservice/static/`

## 文件清单

| 文件 | 说明 |
|------|------|
| `Dockerfile.backend` | 后端容器配置 |
| `Dockerfile.frontend` | 前端容器配置 |
| `docker-compose.yml` | 编排配置 |
| `.dockerignore` | Docker 忽略文件 |
| `.env.production` | 生产环境配置 |

## 启动方式

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 数据持久化

- MySQL 数据存储在 `./data/mysql` 目录
- 重启容器后数据不丢失