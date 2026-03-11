"""事件路由模块"""
import datetime
from flask import Blueprint, request, jsonify, g

from src.timerservice.db import SessionLocal
from src.timerservice.models import TimerEvent
from src.timerservice.auth.jwt import require_auth


events_bp = Blueprint("events", __name__)


def event_to_dict(event: TimerEvent) -> dict:
    """将 TimerEvent 对象转换为字典"""
    return {
        "id": event.id,
        "user_id": event.user_id,
        "timer_id": event.timer_id,
        "fired_at": event.fired_at.isoformat() if event.fired_at else None,
        "read_at": event.read_at.isoformat() if event.read_at else None,
    }


@events_bp.route("", methods=["GET"])
@require_auth
def list_events():
    """
    获取当前用户的事件列表

    查询参数:
        unread_only: 0|1，只返回未读事件
        limit: 返回数量限制（默认 100）
        cursor: 分页游标（event_id）
    """
    db = SessionLocal()
    try:
        query = db.query(TimerEvent).filter(TimerEvent.user_id == g.user_id)

        # 只返回未读
        unread_only = request.args.get("unread_only", "0") == "1"
        if unread_only:
            query = query.filter(TimerEvent.read_at.is_(None))

        # 游标分页
        cursor = request.args.get("cursor")
        if cursor:
            try:
                cursor_id = int(cursor)
                query = query.filter(TimerEvent.id < cursor_id)
            except ValueError:
                return jsonify({"error": "Invalid cursor format"}), 400

        # 排序
        query = query.order_by(TimerEvent.fired_at.desc())

        # 限制数量
        limit = int(request.args.get("limit", "100"))
        if limit > 1000:
            limit = 1000
        query = query.limit(limit)

        events = query.all()

        return jsonify([event_to_dict(e) for e in events]), 200

    finally:
        db.close()


@events_bp.route("/<int:event_id>/ack", methods=["POST"])
@require_auth
def ack_event(event_id: int):
    """
    标记单个事件为已读（幂等）
    """
    db = SessionLocal()
    try:
        event = db.query(TimerEvent).filter(
            TimerEvent.id == event_id,
            TimerEvent.user_id == g.user_id
        ).first()

        if not event:
            return jsonify({"error": "Event not found"}), 404

        # 幂等：如果已读，直接返回成功
        if event.read_at is not None:
            return jsonify({"message": "Event already acknowledged"}), 200

        # 标记为已读
        event.read_at = datetime.datetime.now()
        db.commit()

        return jsonify({"message": "Event acknowledged"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to acknowledge event"}), 500
    finally:
        db.close()


@events_bp.route("/ack_all", methods=["POST"])
@require_auth
def ack_all_events():
    """
    标记当前用户所有未读事件为已读
    """
    db = SessionLocal()
    try:
        # 查询所有未读事件
        unread_events = db.query(TimerEvent).filter(
            TimerEvent.user_id == g.user_id,
            TimerEvent.read_at.is_(None)
        ).all()

        if not unread_events:
            return jsonify({"message": "No unread events"}), 200

        # 批量更新
        now = datetime.datetime.now()
        for event in unread_events:
            event.read_at = now

        db.commit()

        return jsonify({
            "message": "All events acknowledged",
            "count": len(unread_events)
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to acknowledge events"}), 500
    finally:
        db.close()
