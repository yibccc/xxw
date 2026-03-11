"""测试配置和 fixtures"""
import os
import pytest
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.timerservice.app import create_app
from src.timerservice.db import Base
from src.timerservice.models import User, Timer, TimerEvent
from src.timerservice.auth.service import register_user, authenticate_user, hash_password


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """创建测试数据库会话"""
    # 使用内存 SQLite 进行测试
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = register_user(db_session, "testuser", "testpass123")
    db_session.commit()
    return user


@pytest.fixture
def test_user_token(test_user):
    """返回测试用户的 JWT token"""
    from src.timerservice.auth.jwt import generate_jwt
    return generate_jwt(test_user.id)
