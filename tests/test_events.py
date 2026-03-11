"""事件模块测试"""
import datetime


def test_list_events(client, db_session, test_user, test_user_token):
    """测试获取事件列表"""
    # 创建一个事件
    from src.timerservice.models import Timer, TimerEvent, TimerType, TimerStatus
    timer = Timer(
        user_id=test_user.id,
        name='Test Timer',
        type=TimerType.ONCE,
        status=TimerStatus.COMPLETED,
        delay_seconds=5,
        fire_at=datetime.datetime.now(),
        next_fire_at=None,
        last_fired_at=datetime.datetime.now()
    )
    db_session.add(timer)
    db_session.flush()

    event = TimerEvent(
        user_id=test_user.id,
        timer_id=timer.id,
        fired_at=datetime.datetime.now()
    )
    db_session.add(event)
    db_session.commit()

    # 获取事件列表
    response = client.get('/api/events', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == event.id


def test_list_unread_events(client, db_session, test_user, test_user_token):
    """测试获取未读事件"""
    # 创建一个事件（未读）
    from src.timerservice.models import Timer, TimerEvent, TimerType, TimerStatus
    timer = Timer(
        user_id=test_user.id,
        name='Test Timer',
        type=TimerType.ONCE,
        status=TimerStatus.COMPLETED,
        delay_seconds=5,
        fire_at=datetime.datetime.now(),
        next_fire_at=None,
        last_fired_at=datetime.datetime.now()
    )
    db_session.add(timer)
    db_session.flush()

    event = TimerEvent(
        user_id=test_user.id,
        timer_id=timer.id,
        fired_at=datetime.datetime.now(),
        read_at=None  # 未读
    )
    db_session.add(event)
    db_session.commit()

    # 获取未读事件
    response = client.get('/api/events?unread_only=1', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['read_at'] is None


def test_ack_event(client, db_session, test_user, test_user_token):
    """测试标记事件为已读"""
    # 创建一个事件
    from src.timerservice.models import Timer, TimerEvent, TimerType, TimerStatus
    timer = Timer(
        user_id=test_user.id,
        name='Test Timer',
        type=TimerType.ONCE,
        status=TimerStatus.COMPLETED,
        delay_seconds=5,
        fire_at=datetime.datetime.now(),
        next_fire_at=None,
        last_fired_at=datetime.datetime.now()
    )
    db_session.add(timer)
    db_session.flush()

    event = TimerEvent(
        user_id=test_user.id,
        timer_id=timer.id,
        fired_at=datetime.datetime.now()
    )
    db_session.add(event)
    db_session.commit()

    # 标记为已读
    response = client.post(f'/api/events/{event.id}/ack', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200

    # 验证 read_at 被设置
    from src.timerservice.db import SessionLocal
    db = SessionLocal()
    updated = db.query(TimerEvent).filter(TimerEvent.id == event.id).first()
    assert updated.read_at is not None
    db.close()


def test_ack_all_events(client, db_session, test_user, test_user_token):
    """测试标记所有未读事件为已读"""
    # 创建多个未读事件
    from src.timerservice.models import Timer, TimerEvent, TimerType, TimerStatus
    for i in range(3):
        timer = Timer(
            user_id=test_user.id,
            name=f'Test Timer {i}',
            type=TimerType.ONCE,
            status=TimerStatus.COMPLETED,
            delay_seconds=5,
            fire_at=datetime.datetime.now(),
            next_fire_at=None,
            last_fired_at=datetime.datetime.now()
        )
        db_session.add(timer)
        db_session.flush()

        event = TimerEvent(
            user_id=test_user.id,
            timer_id=timer.id,
            fired_at=datetime.datetime.now()
        )
        db_session.add(event)

    db_session.commit()

    # 标记所有为已读
    response = client.post('/api/events/ack_all', headers={
        'Authorization': f'Bearer {test_user_token}'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'count' in data
    assert data['count'] == 3
