"""定时器路由模块"""
import datetime
from datetime import time as time_type
from typing import Optional
from flask import Blueprint, request, jsonify, g

from src.timerservice.db import SessionLocal
from src.timerservice.models import Timer, TimerType, TimerStatus
from src.timerservice.auth.jwt import require_auth
from src.timerservice.timers.timecalc import compute_once_fire_at, compute_daily_next_fire_at
from src.timerservice.scheduler.manager import add_scheduler_job, remove_scheduler_job, update_scheduler_job



timers_bp = Blueprint("timers", __name__)


def timer_to_dict(timer: Timer) -> dict:
    """将 Timer 对象转换为字典"""
    return {
        "id": timer.id,
        "user_id": timer.user_id,
        "name": timer.name,
        "type": timer.type,
        "status": timer.status,
        "delay_seconds": timer.delay_seconds,
        "time_of_day": timer.time_of_day.isoformat() if timer.time_of_day else None,
        "fire_at": timer.fire_at.isoformat() if timer.fire_at else None,
        "next_fire_at": timer.next_fire_at.isoformat() if timer.next_fire_at else None,
        "last_fired_at": timer.last_fired_at.isoformat() if timer.last_fired_at else None,
        "created_at": timer.created_at.isoformat() if timer.created_at else None,
        "updated_at": timer.updated_at.isoformat() if timer.updated_at else None,
    }


@timers_bp.route("", methods=["POST"])
@require_auth
def create_timer():
    """
    创建定时器

    请求体（once 类型）:
        {
            "name": "string",
            "type": "once",
            "delay_seconds": int
        }

    请求体（daily 类型）:
        {
            "name": "string",
            "type": "daily",
            "time_of_day": "HH:MM:SS"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    name = data.get("name")
    timer_type = data.get("type")

    if not name:
        return jsonify({"error": "name is required"}), 400
    if timer_type not in [TimerType.ONCE, TimerType.DAILY]:
        return jsonify({"error": f"type must be '{TimerType.ONCE}' or '{TimerType.DAILY}'"}), 400

    db = SessionLocal()
    try:
        now = db.execute("SELECT NOW()").scalar()
        if isinstance(now, str):
            now = datetime.datetime.fromisoformat(now.replace("T", " "))

        if timer_type == TimerType.ONCE:
            delay_seconds = data.get("delay_seconds")
            if not delay_seconds:
                return jsonify({"error": "delay_seconds is required for once timers"}), 400
            if delay_seconds < 1 or delay_seconds > 86400:
                return jsonify({"error": "delay_seconds must be between 1 and 86400"}), 400

            fire_at = compute_once_fire_at(now, delay_seconds)

            timer = Timer(
                user_id=g.user_id,
                name=name,
                type=TimerType.ONCE,
                status=TimerStatus.ENABLED,
                delay_seconds=delay_seconds,
                fire_at=fire_at,
                next_fire_at=fire_at
            )

        elif timer_type == TimerType.DAILY:
            time_of_day_str = data.get("time_of_day")
            if not time_of_day_str:
                return jsonify({"error": "time_of_day is required for daily timers"}), 400

            try:
                time_of_day = time_type.fromisoformat(time_of_day_str)
            except ValueError:
                return jsonify({"error": "time_of_day must be in HH:MM:SS format"}), 400

            next_fire_at = compute_daily_next_fire_at(now, time_of_day)

            timer = Timer(
                user_id=g.user_id,
                name=name,
                type=TimerType.DAILY,
                status=TimerStatus.ENABLED,
                time_of_day=time_of_day,
                next_fire_at=next_fire_at
            )

        db.add(timer)
        db.commit()
        db.refresh(timer)

        # 注册到调度器
        add_scheduler_job(timer)

        return jsonify(timer_to_dict(timer)), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to create timer"}), 500
    finally:
        db.close()


@timers_bp.route("", methods=["GET"])
@require_auth
def list_timers():
    """
    获取当前用户的定时器列表

    查询参数:
        status: 过滤状态（可选）
        type: 过滤类型（可选）
    """
    db = SessionLocal()
    try:
        query = db.query(Timer).filter(Timer.user_id == g.user_id)

        # 排除已删除的定时器
        query = query.filter(Timer.status != TimerStatus.DELETED)

        # 可选过滤
        status_filter = request.args.get("status")
        if status_filter:
            query = query.filter(Timer.status == status_filter)

        type_filter = request.args.get("type")
        if type_filter:
            query = query.filter(Timer.type == type_filter)

        timers = query.order_by(Timer.created_at.desc()).all()

        return jsonify([timer_to_dict(t) for t in timers]), 200

    finally:
        db.close()


@timers_bp.route("/<int:timer_id>", methods=["GET"])
@require_auth
def get_timer(timer_id: int):
    """
    获取单个定时器
    """
    db = SessionLocal()
    try:
        timer = db.query(Timer).filter(
            Timer.id == timer_id,
            Timer.user_id == g.user_id
        ).first()

        if not timer:
            return jsonify({"error": "Timer not found"}), 404

        return jsonify(timer_to_dict(timer)), 200

    finally:
        db.close()


@timers_bp.route("/<int:timer_id>", methods=["PATCH"])
@require_auth
def update_timer(timer_id: int):
    """
    更新定时器

    请求体:
        {
            "status": "enabled" | "paused",
            "delay_seconds": int,  # only for once type
            "time_of_day": "HH:MM:SS"  # only for daily type
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    db = SessionLocal()
    try:
        timer = db.query(Timer).filter(
            Timer.id == timer_id,
            Timer.user_id == g.user_id
        ).first()

        if not timer:
            return jsonify({"error": "Timer not found"}), 404

        # 检查状态约束
        if timer.status in [TimerStatus.COMPLETED, TimerStatus.DELETED]:
            return jsonify({"error": f"Cannot update timer with status '{timer.status}'"}), 400

        # 更新状态
        new_status = data.get("status")
        if new_status in [TimerStatus.ENABLED, TimerStatus.PAUSED]:
            timer.status = new_status

        # 更新时间参数
        if timer.type == TimerType.ONCE:
            new_delay = data.get("delay_seconds")
            if new_delay is not None:
                if new_delay < 1 or new_delay > 86400:
                    return jsonify({"error": "delay_seconds must be between 1 and 86400"}), 400
                timer.delay_seconds = new_delay

                # 重新计算 fire_at
                now = db.execute("SELECT NOW()").scalar()
                if isinstance(now, str):
                    now = datetime.datetime.fromisoformat(now.replace("T", " "))
                timer.fire_at = compute_once_fire_at(now, new_delay)
                timer.next_fire_at = timer.fire_at

        elif timer.type == TimerType.DAILY:
            new_time_of_day_str = data.get("time_of_day")
            if new_time_of_day_str is not None:
                try:
                    new_time_of_day = time_type.fromisoformat(new_time_of_day_str)
                except ValueError:
                    return jsonify({"error": "time_of_day must be in HH:MM:SS format"}), 400

                timer.time_of_day = new_time_of_day

                # 重新计算 next_fire_at
                now = db.execute("SELECT NOW()").scalar()
                if isinstance(now, str):
                    now = datetime.datetime.fromisoformat(now.replace("T", " "))
                timer.next_fire_at = compute_daily_next_fire_at(now, new_time_of_day)

        db.commit()
        db.refresh(timer)

        # 同步到调度器
        update_scheduler_job(timer)

        return jsonify(timer_to_dict(timer)), 200

    except ValueError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to update timer"}), 500
    finally:
        db.close()


@timers_bp.route("/<int:timer_id>", methods=["DELETE"])
@require_auth
def delete_timer(timer_id: int):
    """
    删除定时器（软删除）
    """
    db = SessionLocal()
    try:
        timer = db.query(Timer).filter(
            Timer.id == timer_id,
            Timer.user_id == g.user_id
        ).first()

        if not timer:
            return jsonify({"error": "Timer not found"}), 404

        # 软删除
        timer.status = TimerStatus.DELETED
        db.commit()

        # 从调度器移除
        remove_scheduler_job(timer.id)

        return jsonify({"message": "Timer deleted successfully"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to delete timer"}), 500
    finally:
        db.close()
