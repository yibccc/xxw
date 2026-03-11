"""配置模块，从环境变量读取配置"""
import os
from dotenv import load_dotenv

# 加载 .env 文件（如果有）
load_dotenv()


class Config:
    """应用配置类"""

    # 数据库配置
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@127.0.0.1:3306/timerservice?charset=utf8mb4"
    )

    # JWT 配置
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_EXPIRES_SECONDS = int(os.getenv("JWT_EXPIRES_SECONDS", "86400"))  # 默认 24 小时

    # 服务器时区
    SERVER_TZ = os.getenv("SERVER_TZ", "Asia/Shanghai")

    # Flask 配置
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", JWT_SECRET)

    # 应用环境
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"


# 导出默认配置实例
config = Config()
