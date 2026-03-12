"""认证模块测试"""
import pytest
from types import SimpleNamespace


def test_register_success(client):
    """测试用户注册成功"""
    response = client.post('/api/auth/register', json={
        'username': 'newuser',
        'password': 'password123'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert 'user_id' in data
    assert data['username'] == 'newuser'


def test_register_duplicate_username(client, db_session):
    """测试重复用户名"""
    # 先注册一个用户
    from src.timerservice.auth.service import register_user
    register_user(db_session, 'existing', 'pass123123')
    db_session.commit()

    # 尝试注册相同用户名
    response = client.post('/api/auth/register', json={
        'username': 'existing',
        'password': 'newpass123'
    })

    assert response.status_code == 409
    data = response.get_json()
    assert 'error' in data


def test_register_invalid_input(client):
    """测试无效输入"""
    # 密码太短
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': '123'  # 只有 3 位
    })
    assert response.status_code == 400

    # 缺少字段
    response = client.post('/api/auth/register', json={
        'username': 'testuser'
    })
    assert response.status_code == 400


def test_login_success(client, test_user):
    """测试登录成功"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data
    assert data['user_id'] == test_user.id
    assert data['username'] == test_user.username


def test_login_invalid_credentials(client, test_user):
    """测试登录失败"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })

    assert response.status_code == 401


def test_me_authenticated(client, test_user_token, monkeypatch):
    """测试获取当前用户信息（已认证）"""
    import src.timerservice.auth.routes as auth_routes

    class FakeSession:
        def close(self):
            pass

    monkeypatch.setattr(auth_routes, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(
        auth_routes,
        "get_user_by_id",
        lambda db, user_id: SimpleNamespace(id=user_id, username="testuser"),
    )

    response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['user_id'] > 0
    assert data['username'] == 'testuser'


def test_me_unauthenticated(client):
    """测试获取当前用户信息（未认证）"""
    response = client.get('/api/auth/me')

    assert response.status_code == 401
