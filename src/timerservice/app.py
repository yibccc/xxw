"""Flask 应用工厂"""
import threading
from flask import Flask

from .config import config
from .db import engine, SessionLocal


# 启动 SSE ping 后台线程
def start_ping_thread(hub):
    """启动 ping 线程，每 30 秒向所有连接发送 ping"""
    import time

    def ping_loop():
        while True:
            time.sleep(30)
            hub.publish_ping()

    thread = threading.Thread(target=ping_loop, daemon=True)
    thread.start()
    return thread


def create_app() -> Flask:
    """
    创建并配置 Flask 应用

    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config)

    # 注册蓝图
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from .timers.routes import timers_bp
    app.register_blueprint(timers_bp, url_prefix="/api/timers")

    from .events.routes import events_bp
    app.register_blueprint(events_bp, url_prefix="/api/events")

    from .sse.routes import sse_bp
    app.register_blueprint(sse_bp, url_prefix="/api")

    # 启动 SSE ping 线程
    from .sse.hub import sse_hub
    start_ping_thread(sse_hub)

    # 启动调度器
    from .scheduler.manager import start_scheduler
    start_scheduler()

    # 请求后处理：关闭数据库会话
    @app.teardown_appcontext
    def shutdown_db_session(exception=None):
        SessionLocal.remove()

    # 健康检查路由
    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
