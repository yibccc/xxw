"""应用入口点"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.timerservice.app import create_app
from src.timerservice.runtime import start_runtime_services


def main():
    """启动 Flask 应用"""
    app = create_app()
    start_runtime_services()

    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))

    print(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False))


if __name__ == "__main__":
    main()
