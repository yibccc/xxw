里程碑 0：仓库准备与依赖（后端骨架）



 0.1 目录结构落地



 在仓库根目录创建（先空文件/空目录即可）：



 - src/timerservice/

   - \_\_init\_\_.py

   - app.py（Flask app factory）

   - config.py

   - db.py（engine/session）

   - models.py（User/Timer/TimerEvent ORM）

   - auth/（register/login/jwt）

   - timers/（timers CRUD）

   - events/（events list/ack）

   - sse/（stream endpoint + hub）

   - scheduler/（APScheduler init/rebuild/handlers）

   - static/（Vue build 输出目录，先空）

 - tests/

 - docs/plans/2026-03-11-timerservice-design.md（按已确认内容落盘）

 - alembic/（后续由 alembic init 生成）



 入口：保留 main.py 作为启动点（调用 create\_app()）。



 0.2 Python 依赖（uv）



 在 pyproject.toml 中加入依赖（方向如下）：

 - Flask

 - SQLAlchemy

 - Alembic

 - PyMySQL（MySQL 驱动；或 mysqlclient，Windows 下编译成本更高，建议 PyMySQL）

 - APScheduler

 - PyJWT（或 python-jose；二选一）

 - passlib\[bcrypt]（或 bcrypt + werkzeug.security；二选一）

 - pytest、pytest-flask（或 Flask 提供的 test client 自己配）

 - python-dotenv（可选：本地环境变量）



 建议命令（示例）：

 uv add flask sqlalchemy alembic pymysql apscheduler pyjwt passlib\[bcrypt]

 uv add --dev pytest



 0.3 配置约定（环境变量）



 在 src/timerservice/config.py 约定读取：

 - DATABASE\_URL：例如 mysql+pymysql://user:pass@127.0.0.1:3306/timerservice?charset=utf8mb4

 - JWT\_SECRET：签名密钥

 - JWT\_EXPIRES\_SECONDS：默认 86400

 - SERVER\_TZ：默认系统时区（第一版按服务器时区，不做用户时区）



 验收标准：

 - uv run python main.py 能启动 Flask（即使暂时无路由），无 ImportError。



 ---

 里程碑 1：数据库模型 + Alembic 迁移



 1.1 ORM Models（models.py）



 实现 3 个模型（字段按设计）：

 - User

 - Timer

 - TimerEvent



 关键点：

 - Timer.status：enabled/paused/completed/deleted

 - Timer.type：once/daily

 - Timer.time\_of\_day：SQLAlchemy 映射 MySQL TIME

 - TimerEvent.read\_at：NULL=未读

 - 常用索引：在模型或迁移里加（user\_id,status / status,next\_fire\_at / user\_id,fired\_at / user\_id,read\_at）



 1.2 Alembic 初始化与首个迁移



 命令（示例）：

 uv run alembic init alembic

 配置 alembic.ini 与 env.py：

 - 读取 DATABASE\_URL

 - target\_metadata 指向 SQLAlchemy Base metadata



 生成首个迁移：

 uv run alembic revision --autogenerate -m "init schema"

 uv run alembic upgrade head



 验收标准：

 - MySQL 中创建了三张表及索引；

 - 可用一个简单脚本连接 DB 并查询无报错。



 ---

 里程碑 2：认证（注册/登录/JWT 校验）



 2.1 Auth 路由与服务



 模块建议：

 - auth/routes.py：Flask Blueprint

 - auth/service.py：注册、登录逻辑

 - auth/jwt.py：签发与验证、装饰器/依赖注入



 实现接口：

 - POST /api/auth/register：username 唯一；密码 hash（bcrypt）

 - POST /api/auth/login：校验后签发 JWT（exp=24h）

 - 统一鉴权：提供 @require\_auth（或 before\_request）把 g.user\_id 注入



 关键实现细节：

 - sessionStorage 存 token，后端无需 cookie

 - 任何越权资源访问按“查不到”返回 404



 验收标准（手工/测试）：

 - 能注册、登录拿到 token

 - token 过期/错误返回 401



 ---

 里程碑 3：Timers REST（CRUD + 状态机 + 校验）



 3.1 Timers Blueprint



 实现接口：

 - POST /api/timers

   - once：入参 delay\_seconds（1~86400）→ 计算 fire\_at = now + delay

   - daily：入参 time\_of\_day（HH:MM:SS）→ 计算 next\_fire\_at

 - GET /api/timers：仅当前用户；默认不返回 deleted

 - GET /api/timers/<id>：按 (id,user\_id) 查

 - PATCH /api/timers/<id>

   - status：enabled/paused

   - once 改 delay\_seconds：仅允许 status!=completed/deleted 时；重算 fire\_at/next\_fire\_at

   - daily 改 time\_of\_day：重算 next\_fire\_at

 - DELETE /api/timers/<id>：软删 deleted



 3.2 时间计算函数（可单测）



 放在 timers/timecalc.py：

 - compute\_once\_fire\_at(now, delay\_seconds)

 - compute\_daily\_next\_fire\_at(now, time\_of\_day, tz=server\_tz)（按服务器时区语义；实现时直接用本地 aware datetime 或 naive + 统一约定）



 3.3 状态约束（建议）



 - once：

   - enabled/paused 允许改 delay

   - completed/deleted 不允许改

 - daily：

   - enabled/paused 允许改 time\_of\_day

   - deleted 不允许改

 - delete 后不可恢复（第一版）



 验收标准：

 - Postman/pytest 调用 CRUD 正常

 - 访问别人的 timer 永远 404



 ---

 里程碑 4：Events（历史/未读/已读）



 实现接口：

 - GET /api/events

   - query：unread\_only=0|1，limit，cursor（cursor 可先用 id<f 或 fired\_at< 简化）

 - POST /api/events/<id>/ack

   - 只允许 ack 自己的事件

   - 幂等：read\_at 已有则直接返回成功

 - POST /api/events/ack\_all

   - 将当前用户所有 read\_at IS NULL 的置为 now



 验收标准：

 - 触发事件写入后，GET /api/events?unread\_only=1 能看到

 - ack 后不再出现在 unread\_only 列表



 ---

 里程碑 5：SSE（/api/stream）+ SSE Hub（内存连接管理）



 5.1 SSE Hub 设计



 在 sse/hub.py：

 - 维护：user\_id -> set/ list of connection objects

 - 每个连接一个线程安全队列（如 queue.Queue）用于推送消息

 - 提供：

   - register(user\_id) -> conn

   - unregister(user\_id, conn)

   - publish(user\_id, event\_name, data\_dict)



 5.2 SSE Endpoint



 在 sse/routes.py：

 - GET /api/stream

   - 鉴权：读取 Authorization Bearer

   - 返回 streaming response（text/event-stream）

   - 每隔 N 秒发送 ping（或在生成器里超时 yield ping）

   - 当客户端断开：捕获异常并 unregister



 事件格式：

 event: timer\_fired

 data: {...json...}





 验收标准：

 - 前端/脚本可以保持连接并收到 ping

 - publish 后能立刻收到事件



 ---

 里程碑 6：APScheduler 集成（单实例）+ 触发写库 + 推送



 6.1 Scheduler 初始化



 在 scheduler/manager.py：

 - init\_scheduler(app)：创建 BackgroundScheduler

 - rebuild\_jobs\_from\_db()：加载所有 status=enabled timers，注册 job



 job id 建议：

 - timer:{timer\_id}（便于更新/删除）



 6.2 触发处理函数（可测试）



 抽成纯函数/可注入依赖：

 - handle\_timer\_fire(timer\_id)：

   - 重新读 DB，检查 status==enabled

   - 插入 TimerEvent（read\_at NULL）

   - 更新 Timer：

       - once：status=completed，last\_fired\_at=now，next\_fire\_at=NULL

     - daily：last\_fired\_at=now，next\_fire\_at=下一次

   - 提交事务

   - publish SSE：timer\_fired（包含 event\_id、timer 信息、read\_at=null）



 6.3 与 Timers PATCH/DELETE 联动



 在 timers 修改后调用 scheduler manager：

 - create timer：立即注册 job（enabled 才注册）

 - pause：移除 job

 - enable：注册 job

 - update time：重建 job

 - delete：移除 job + status=deleted



 验收标准：

 - 创建 once delay=2 秒：2 秒后 events 表新增记录；SSE 收到 timer\_fired；timer 状态变 completed

 - daily 在当日/次日正确触发（至少验证 next\_fire\_at 计算与 job 安排）



 ---

 里程碑 7：Vue 前端（同域托管）+ SSE 客户端（fetch stream）



 7.1 前端工程



 在仓库根目录：

 cd frontend

 npm create vite@latest . -- --template vue

 npm install



 构建输出配置（vite.config）：

 - build.outDir 指向 ../src/timerservice/static/

 - build.emptyOutDir = true



 7.2 页面与功能



 - 登录页（login）

 - 注册页（register）

 - 定时器列表（list）

   - 展示：name/type/status/next\_fire\_at

   - 操作：暂停/恢复、删除

 - 新建定时器（create）

 - 编辑定时器（edit）

   - once：改 delay\_seconds

   - daily：改 time\_of\_day

 - 通知/事件中心（events）

   - 未读计数

   - 列表 + 单条 ack

   - “全部已读” ack\_all



 7.3 SSE 客户端实现要点



 - 用 fetch 建连：

   - fetch('/api/stream', { headers: { Authorization: 'Bearer ' + token } })

   - response.body.getReader() 循环读 chunk，拼接 buffer，按 \\n\\n 分割事件块

 - 收到 timer\_fired：

   - toast/弹窗（可选）

   - 刷新 events 未读计数或直接把 event push 到 store



 7.4 Flask 静态托管



 - Flask app 配置 static\_folder 指向 src/timerservice/static

 - 路由：/、/timers、/events 等前端路由需要回退到 index.html（history 模式需处理；或前端用 hash 模式简化）



 验收标准：

 - npm run build 后，uv run python main.py 打开根路径能看到 Vue 页面

 - 登录后能 CRUD timers、查看 events、SSE 实时弹出触发通知



 ---

 里程碑 8：测试与CI（最小闭环）



 8.1 pytest 结构



 - tests/test\_auth.py

 - tests/test\_timers.py

 - tests/test\_events.py

 - tests/test\_timecalc.py

 - （可选）tests/test\_scheduler\_handler.py：直接调用 handle\_timer\_fire



 8.2 测试数据库策略（建议）



 - 用独立 MySQL schema（例如 timerservice\_test）

 - 测试启动前 alembic upgrade head

 - 每个测试用事务回滚或 truncate



 验收标准：

 - uv run pytest 全绿

 - 覆盖最关键权限隔离与状态机



 ---

 运行/开发命令清单（建议最终写入 README）



 后端：

 set DATABASE\_URL=...

 set JWT\_SECRET=...

 uv run python main.py



 迁移：

 uv run alembic revision --autogenerate -m "..."

 uv run alembic upgrade head



 前端：

 cd frontend

 npm run dev

 npm run build



 ---

 最终验收清单（你可作为交付标准）



 1. 用户 A/B 注册登录后，A 无法看到/修改/删除 B 的 timers 与 events（均 404）。

 2. once 定时器 delay=1~86400 校验正确；触发后：

   - DB 写入一条 event（未读）

   - timer 变为 completed

   - 在线 SSE 立即收到 timer\_fired



 3. daily 定时器按服务器时区每天 HH:MM:SS 触发；可修改 time\_of\_day 并生效。

 4. events：

   - 未读列表可查

   - 单条 ack 后 read\_at 被写入且不再未读

   - ack\_all 生效



 5. Vue 页面同域可访问，能完成：注册/登录、定时器 CRUD、事件查看、SSE 实时通知。

