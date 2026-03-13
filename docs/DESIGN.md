# 定时器服务 - 技术设计文档

## 概述

定时器服务是一个基于 Flask 的 Web 应用，提供定时器管理和实时事件推送功能。用户可以创建一次性定时器（once）或每日定时器（daily），当定时器触发时，系统会创建事件记录并通过 SSE 实时推送给在线用户。

## 架构设计

### 核心组件

| 组件 | 技术栈 | 说明 |
|--------|----------|------|
| 后端框架 | Flask 3.1 | Python Web 框架 |
| ORM | SQLAlchemy 2.0 | Python SQL 工具包和 ORM |
| 数据库 | MySQL 8.0+ | 关系型数据库 |
| 数据库迁移 | Alembic | 数据库版本控制 |
| 定时调度 | APScheduler 3.11 | Python 定时任务调度库 |
| 认证 | JWT + Bcrypt | Token 认证 + 密码哈希 |
| 实时推送 | SSE (Server-Sent Events) | 服务器推送事件 |
| 前端框架 | Vue 3 + Vite | 现代 JavaScript 框架 |
| 路由 | Vue Router 4 | 前端路由管理 |
| HTTP 客户端 | Axios | HTTP 请求库 |
| 构建工具 | Vite | 前端构建工具 |

## 数据库设计

### 用户表 (users)

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | INT | 主键 | PRIMARY KEY, AUTO_INCREMENT |
| username | VARCHAR(50) | 用户名 | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | 密码哈希 (bcrypt) | NOT NULL |
| created_at | | 创建时间 | NOT NULL, DEFAULT NOW() |

**索引**：
- `idx_username(username)`: 用户名唯一索引

### 定时器表 (timers)

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | INT | 主键 | PRIMARY KEY, AUTO_INCREMENT |
| user_id | INT | 所属用户 | FOREIGN KEY(users.id), NOT NULL, INDEX |
| name | VARCHAR(200) | 定时器名称 | NOT NULL |
| type | ENUM | 类型 | 'once' 或 'daily' |
| status | ENUM | 状态 | 'enabled', 'completed', 'deleted' |
| delay_seconds | INT | 延迟秒数 (once 类型) | NULL, 1~86400 |
| time_of_day | TIME | 每日触发时间 (daily 类型) | NULL |
| fire_at | DATETIME | 计划触发时间 (once) | NULL, INDEX |
| next_fire_at | DATETIME | 下次触发时间 (daily) | NULL, INDEX |
| last_fired_at | DATETIME | 上次触发时间 | NULL |
| created_at | DATETIME | 创建时间 | NOT NULL, DEFAULT NOW() |
| updated_at | DATETIME | 更新时间 | NOT NULL, DEFAULT NOW(), ON UPDATE NOW() |

**状态说明**：
- `enabled`: 启用中，定时器正常执行（创建后自动启用）
- `completed`: 已完成 (once 类型触发后)
- `deleted`: 已删除（软删除）

> 注意：定时器创建后自动启用，不支持暂停功能

**索引**：
- `idx_user_status(user_id, status)`: 按用户和状态查询
- `idx_status_next_fire(status, next_fire_at)`: 调度器查询

### 事件表 (timer_events)

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | INT | 主键 | PRIMARY KEY, AUTO_INCREMENT |
| user_id | INT | 所属用户 | FOREIGN KEY(users.id), NOT NULL, INDEX |
| timer_id | INT | 关联定时器 | FOREIGN KEY(timers.id), NOT NULL, INDEX |
| fired_at | DATETIME | 触发时间 | NOT NULL, DEFAULT NOW(), INDEX |
| read_at | DATETIME | 已读时间 | NULL, INDEX |

**计算字段**（非数据库字段，通过关联或属性计算）：
- `timer_name`: 通过 `timer.name` 关联查询获取
- `event_type`: 固定为 `'timer_fired'`
- `is_read`: 通过 `read_at is not None` 计算

**索引**：
- `idx_user_fired(user_id, fired_at)`: 按用户和时间查询
- `idx_user_read(user_id, read_at)`: 查询未读事件

## API 设计

### 认证 API

#### POST /api/auth/register

注册新用户

**请求**：
```json
{
  "username": "string (3-50字符)",
  "password": "string (至少6字符)"
}
```

**响应 201**：
```json
{
  "user_id": 1,
  "username": "alice"
}
```

**错误 409**：
```json
{
  "error": "Username already exists"
}
```

#### POST /api/auth/login

用户登录

**请求**：
```json
{
  "username": "string",
  "password": "string"
}
```

**响应 200**：
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 1,
  "username": "alice"
}
```

**错误 401**：
```json
{
  "error": "Invalid credentials"
}
```

#### GET /api/auth/me

获取当前用户信息

**请求头**：
```
Authorization: Bearer <token>
```

**响应 200**：
```json
{
  "user_id": 1,
  "username": "alice"
}
```

### 定时器 API

#### POST /api/timers

创建定时器

**请求头**：
```
Authorization: Bearer <token>
```

**请求 (once 类型)**：
```json
{
  "name": "提醒我喝水",
  "type": "once",
  "delay_seconds": 3600
}
```

**请求 (daily 类型)**：
```json
{
  "name": "每日晨会",
  "type": "daily",
  "time_of_day": "08:00:00"
}
```

**响应 201**：
```json
{
  "id": 1,
  "user_id": 1,
  "name": "提醒我喝水",
  "type": "once",
  "status": "enabled",
  "delay_seconds": 3600,
  "time_of_day": null,
  "fire_at": "2026-03-11T14:37:00",
  "next_fire_at": "2026-03-11T14:37:00",
  "last_fired_at": null,
  "created_at": "2026-03-11T13:37:00",
  "updated_at": "2026-03-11T13:37:00"
}
```

#### GET /api/timers

获取定时器列表

**请求头**：
```
Authorization: Bearer <token>
```

**查询参数**：
- `status`: 过滤状态 (enabled/completed/deleted)
- `type`: 过滤类型 (once/daily)

**响应 200**：
```json
[
  {
    "id": 1,
    "name": "提醒我喝水",
    "type": "once",
    "status": "enabled",
    ...
  }
]
```

#### GET /api/timers/:id

获取单个定时器

**响应 200**：同创建响应

**错误 404**：
```json
{
  "error": "Timer not found"
}
```

#### PATCH /api/timers/:id

更新定时器

**请求**：
```json
{
  "delay_seconds": 7200,     // 仅 once 类型
  "time_of_day": "09:00:00"  // 仅 daily 类型
}
```

> 注意：定时器创建后自动启用，不支持暂停功能

**响应 200**：同创建响应

#### DELETE /api/timers/:id

删除定时器（软删除）

**响应 200**：
```json
{
  "message": "Timer deleted successfully"
}
```

### 事件 API

#### GET /api/events

获取事件列表

**请求头**：
```
Authorization: Bearer <token>
```

**查询参数**：
- `unread_only`: 0|1，只返回未读
- `limit`: 返回数量限制 (默认 100)
- `cursor`: 分页游标 (event_id)

**响应 200**：
```json
[
  {
    "id": 1,
    "user_id": 1,
    "timer_id": 1,
    "timer_name": "提醒我喝水",
    "event_type": "timer_fired",
    "is_read": false,
    "created_at": "2026-03-11T14:37:00",
    "fired_at": "2026-03-11T14:37:00",
    "read_at": null
  }
]
```

> 注意：`timer_name`、`event_type`、`is_read`、`created_at` 为计算字段，非数据库实际存储字段

#### POST /api/events/:id/ack

标记事件为已读

**响应 200**：
```json
{
  "message": "Event acknowledged"
}
```

#### POST /api/events/ack_all

标记所有未读事件为已读

**响应 200**：
```json
{
  "message": "All events acknowledged",
  "count": 5
}
```

### SSE API

#### GET /api/stream

建立 SSE 连接，接收实时事件推送

**请求头或查询参数**：
```
Authorization: Bearer <token>
或
?token=<token>
```

**响应**：`text/event-stream` 流

**事件格式**：
```
event: connected
data: {"user_id": 1, "timestamp": "2026-03-11T13:37:00"}

event: timer_fired
data: {"event_id": 1, "timer_id": 1, "timer_name": "提醒我喝水", "fired_at": "2026-03-11T14:37:00", "read_at": null}

: ping
```

## 安全设计

### 认证与授权

1. **JWT Token 认证**
   - 所有 API 路由（除注册/登录）需要有效的 JWT token
   - Token 默认有效期 24 小时
   - 使用 HS256 算法签名

2. **密码安全**
   - 密码使用 bcrypt 哈希存储
   - 密码长度至少 6 字符
   - 明文密码不存储或记录

3. **权限隔离**
   - 用户只能访问自己的定时器和事件
   - 访问其他用户资源返回 404（而非 403，避免信息泄露）

### 数据安全

1. **SQL 注入防护**
   - 使用 SQLAlchemy ORM，所有查询参数化
   - 不使用原生 SQL 拼接

2. **XSS 防护**
   - 前端使用 Vue 的模板自动转义
   - SSE 事件数据使用 JSON 格式

3. **CSRF 防护**
   - 使用 Token 认证，天然防 CSRF
   - 不使用 Cookie 存储敏感信息

## 定时器调度设计

### APScheduler 配置

- **调度器类型**: BackgroundScheduler
- **执行器**: ThreadPoolExecutor (max_workers=10)
- **时区**: Asia/Shanghai
- **Job Store**: MemoryJobStore (单实例部署)

### Job 管理

每个定时器对应一个 APScheduler Job：

- **Job ID**: `timer:{timer_id}`
- **Once 类型**: 使用 `DateTrigger`，触发一次后自动删除
- **Daily 类型**: 使用 `CronTrigger`，每日同一时间触发

### 触发处理流程

```
1. APScheduler 触发 Job
   ↓
2. 重新从 DB 读取 Timer（确保状态最新）
   ↓
3. 检查 status == enabled
   ↓
4. 创建 TimerEvent 记录
   ↓
5. 更新 Timer 状态
   - once: status=completed, next_fire_at=NULL
   - daily: 更新 last_fired_at, 重新计算 next_fire_at
   ↓
6. 推送 SSE 消息
   ↓
7. daily 类型：更新调度器中的 Job
```

### 数据库同步

- **创建定时器**: 立即添加 Job (如果 status=enabled)
- **更新时间**: 重建 Job
- **删除定时器**: 移除 Job

## 前端设计

### 页面结构

| 路由 | 组件 | 说明 |
|------|------|------|
| `/login` | Login.vue | 登录页面 |
| `/register` | Register.vue | 注册页面 |
| `/timers` | Timers.vue | 定时器列表，支持 CRUD |
| `/events` | Events.vue | 事件中心，查看和 ack 事件 |

### 状态管理

使用 Vue 3 Composition API + Ref 进行状态管理：

- `localStorage`: 存储 token 和用户信息
- `SSEClient`: 单例管理 SSE 连接
- `axios`: 全局拦截器处理认证和错误

### SSE 客户端

使用 `fetch` API 实现 SSE 连接（因为 EventSource 不支持自定义头部）：

```javascript
class SSEClient {
  async connect() {
    const response = await fetch('/api/stream', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const reader = response.body.getReader()
    // 逐块读取并解析事件
  }
}
```

### 构建配置

- **开发**: 使用 Vite 开发服务器，代理 API 到后端
- **生产**: 构建到 `src/timerservice/static/`，由 Flask 托管

### 功能特性

#### 定时器创建
- 支持时分秒输入：更直观地设置延迟时间
- 创建后自动启用：无需手动点击启用

#### 用户交互
- 退出登录按钮：导航栏提供登出功能
- 定时器触发后自动标记已读：用户确认提示后自动处理
- 未读事件数量实时显示

#### 深色模式支持
- 支持系统级深色模式（`prefers-color-scheme: dark`）
- 覆盖登录、注册、定时器列表、事件中心等页面

#### SSE 客户端优化
- 修复多行事件解析：event 和 data 行可在同一块中独立处理
- 统一的日志前缀 `[SSE]` 便于调试

## 部署建议

### 单实例部署

适用于小型团队或个人使用：

```
1. 配置 MySQL 数据库
2. 运行数据库迁移
3. 构建前端: npm run build
4. 启动服务: uv run python main.py
```

### 多实例扩展（未来）

如需支持高并发：

1. **数据库 Job Store**: 使用 SQLAlchemyJobStore 替代 MemoryJobStore
2. **分布式锁**: 使用 Redis 实现 Job 锁
3. **负载均衡**: 多个 Flask 实例 + Nginx
4. **Session 存储**: 使用 Redis 替代内存 Session

## 性能优化

### 数据库

- 索引优化：已为查询路径添加复合索引
- 连接池：SQLAlchemy 默认连接池
- 事务：每次请求独立事务

### SSE

- 连接保活：30 秒发送 ping
- 消息队列：使用 `queue.Queue` 避免阻塞
- 连接清理：客户端断开时及时清理资源

### 前端

- 虚拟滚动：事件列表实现虚拟滚动（未来）
- 请求优化：列表查询限制返回数量
- 缓存策略：可添加前端缓存（未来）
