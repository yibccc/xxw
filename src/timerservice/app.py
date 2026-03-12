"""Flask 应用工厂"""
from flask import Flask

from .config import config
from .db import SessionLocal


def create_app() -> Flask:
    """
    创建并配置 Flask 应用

    Returns:
        Flask 应用实例
    """
    import os
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='')

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

    # 请求后处理：关闭数据库会话
    @app.teardown_appcontext
    def shutdown_db_session(exception=None):
        SessionLocal.remove()

    # 健康检查路由
    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
