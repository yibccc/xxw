"""定时器模块测试"""
import datetime


def test_create_once_timer_success(client, db_session, test_user, test_user_token):
    """测试创建一次性定时器成功"""
    response = client.post('/api/timers', json={
        'name': 'Test Once Timer',
        'type': 'once',
        'delay_seconds': 10
    }, headers={'Authorization': f'Bearer {test_user_token}'})

    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Test Once Timer'
    assert data['type'] == 'once'
    assert data['status'] == 'enabled'
    assert data['delay_seconds'] == 10
    assert data['next_fire_at'] is not None


def test_create_daily_timer_success(client, db_session, test_user, test_user_token):
    """测试创建每日定时器成功"""
    response = client.post('/api/timers', json={
        'name': 'Test Daily Timer',
        'type': 'daily',
        'time_of_day': '12:00:00'
    }, headers={'Authorization': f'Bearer {test_user_token}'})

    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Test Daily Timer'
    assert data['type'] == 'daily'
    assert data['status'] == 'enabled'
    assert data['time_of_day'] == '12:00:00'
    assert data['next_fire_at'] is not None


def test_create_timer_unauthenticated(client):
    """测试未认证创建定时器"""
    response = client.post('/api/timers', json={
        'name': 'Test Timer',
        'type': 'once',
        'delay_seconds': 10
    })

    assert response.status_code == 401


def test_create_timer_invalid_input(client, test_user_token):
    """测试无效输入"""
    # delay_seconds 超出范围
    response = client.post('/api/timers', json={
        'name': 'Test Timer',
        'type': 'once',
        'delay_seconds': 100000  # 超过 86400
    }, headers={'Authorization': f'Bearer {test_user_token}'})

    assert response.status_code == 400


def test_list_timers(client, db_session, test_user, test_user_token):
    """测试获取定时器列表"""
    # 创建一个定时器
    from src.timerservice.models import Timer, TimerType, TimerStatus
    timer = Timer(
        user_id=test_user.id,
        name='List Test Timer',
        type=TimerType.ONCE,
        status=TimerStatus.ENABLED,
        delay_seconds=5,
        fire_at=datetime.datetime.now(),
        next_fire_at=datetime.datetime.now()
    )
    db_session.add(timer)
    db_session.commit()

    # 获取列表
    response = client.get('/api/timers', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == timer.id


def test_get_timer_success(client, db_session, test_user, test_user_token):
    """测试获取单个定时器"""
    # 创建一个定时器
    from src.timerservice.models import Timer, TimerType, TimerStatus
    timer = Timer(
        user_id=test_user.id,
        name='Get Test Timer',
        type=TimerType.ONCE,
        status=TimerStatus.ENABLED,
        delay_seconds=5,
        fire_at=datetime.datetime.now(),
        next_fire_at=datetime.datetime.now()
    )
    db_session.add(timer)
    db_session.commit()

    # 获取定时器
    response = client.get(f'/api/timers/{timer.id}', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == timer.id


def test_get_timer_not_found(client, test_user_token):
    """测试获取不存在的定时器"""
    response = client.get('/api/timers/99999', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 404


def test_delete_timer(client, db_session, test_user, test_user_token):
    """测试软删除定时器"""
    # 创建一个定时器
    from src.timerservice.models import Timer, TimerType, TimerStatus
    timer = Timer(
        user_id=test_user.id,
        name='Delete Test Timer',
        type=TimerType.ONCE,
        status=TimerStatus.ENABLED,
        delay_seconds=5,
        fire_at=datetime.datetime.now(),
        next_fire_at=datetime.datetime.now()
    )
    db_session.add(timer)
    db_session.commit()

    # 删除定时器
    response = client.delete(f'/api/timers/{timer.id}', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200
    assert 'message' in response.get_json()

    # 验证状态为 deleted
    from src.timerservice.db import SessionLocal
    db = SessionLocal()
    updated = db.query(Timer).filter(Timer.id == timer.id).first()
    assert updated.status == TimerStatus.DELETED
    db.close()
