"""Flask 应用工厂"""
from pathlib import Path

from flask import Flask, abort, send_from_directory

from .config import config
from .db import SessionLocal


def create_app() -> Flask:
    """
    创建并配置 Flask 应用

    Returns:
        Flask 应用实例
    """
    static_folder = Path(__file__).resolve().parent / "static"
    app = Flask(__name__, static_folder=None)

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

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        if path.startswith("api/") or path == "health":
            abort(404)

        requested = (static_folder / path).resolve() if path else None
        if requested and requested.is_file() and static_folder in requested.parents:
            return send_from_directory(static_folder, path)

        index_file = static_folder / "index.html"
        if index_file.exists():
            return send_from_directory(static_folder, "index.html")

        abort(404)

    return app
