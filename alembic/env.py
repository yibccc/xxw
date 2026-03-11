from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 添加 src 目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入我们的配置和模型
from src.timerservice.config import config as app_config
from src.timerservice.db import Base
from src.timerservice.models import User, Timer, TimerEvent

# 这是 Alembic Config 对象，用于访问 .ini 配置文件中的值
config = context.config

# 设置数据库 URL
config.set_main_option("sqlalchemy.url", app_config.DATABASE_URL)

# 读取配置文件中的 Python 日志配置
# 这一行主要用于设置日志记录器
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型元数据用于自动生成迁移
target_metadata = Base.metadata

# 其他配置值，可以根据 env.py 的需要获取：
# my_important_option = config.get_main_option("my_important_option")
# ... 等等


def run_migrations_offline() -> None:
    """离线模式运行迁移

    此模式仅使用 URL 配置上下文，不需要 Engine（虽然也可以使用）。
    由于跳过 Engine 创建，我们甚至不需要 DBAPI。

    在此调用 context.execute() 会将给定字符串输出到脚本。

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移

    在此场景下，我们需要创建 Engine
    并将连接与上下文关联。

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
