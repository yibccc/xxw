"""数据库模块，提供 SQLAlchemy engine 和 session"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from .config import config

# 创建数据库引擎
engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# 创建会话工厂
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# 创建 Base 类，所有 ORM 模型继承自它
Base = declarative_base()


def get_db():
    """
    依赖注入函数，获取数据库会话
    使用方法：
        with get_db() as db:
            # 使用 db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表（开发时使用，生产环境用 Alembic）"""
    Base.metadata.create_all(bind=engine)
