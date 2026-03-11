"""APScheduler 管理模块"""
import datetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from src.timerservice.db import SessionLocal
from src.timerservice.models import Timer, TimerEvent, TimerType, TimerStatus
from src.timerservice.timers.timecalc import compute_daily_next_fire_at
from src.timerservice.sse.hub import sse_hub

logger = logging.getLogger(__name__)


# 全局调度器实例
scheduler = None


def init_scheduler():
    """
    初始化调度器

    Returns:
        BackgroundScheduler 实例
    """
    global scheduler

    if scheduler is not None:
        return scheduler

    # 创建调度器
    scheduler = BackgroundScheduler(
        executors={
            "default": ThreadPoolExecutor(max_workers=10)
        },
        jobstores={
            "default": MemoryJobStore()
        },
        timezone="Asia/Shanghai"
    )

    return scheduler


def get_scheduler():
    """
    获取调度器实例

    Returns:
        BackgroundScheduler 实例
    """
    global scheduler
    return scheduler


def handle_timer_fire(timer_id: int):
    """
    处理定时器触发

    Args:
        timer_id: 定时器 ID
    """
    db = SessionLocal()
    try:
        # 重新从数据库读取定时器（确保状态是最新的）
        timer = db.query(Timer).filter(Timer.id == timer_id).first()

        if not timer:
            logger.warning(f"Timer {timer_id} not found, skipping")
            return

        # 检查状态是否为 enabled
        if timer.status != TimerStatus.ENABLED:
            logger.info(f"Timer {timer_id} is not enabled (status: {timer.status}), skipping")
            return

        # 创建事件记录
        event = TimerEvent(
            user_id=timer.user_id,
            timer_id=timer.id
        )
        db.add(event)
        db.flush()  # 获取 event.id

        # 更新定时器状态
        now = datetime.datetime.now()

        if timer.type == TimerType.ONCE:
            # once 类型：触发后变为 completed
            timer.status = TimerStatus.COMPLETED
            timer.last_fired_at = now
            timer.next_fire_at = None

        elif timer.type == TimerType.DAILY:
            # daily 类型：更新 last_fired_at 和 next_fire_at
            timer.last_fired_at = now
            timer.next_fire_at = compute_daily_next_fire_at(now, timer.time_of_day)

            # 更新调度器中的 job
            update_scheduler_job(timer)

        db.commit()

        # 推送 SSE 消息
        sse_hub.publish(
            user_id=timer.user_id,
            event_name="timer_fired",
            data={
                "event_id": event.id,
                "timer_id": timer.id,
                "timer_name": timer.name,
                "timer_type": timer.type,
                "fired_at": now.isoformat(),
                "read_at": None
            }
        )

        logger.info(f"Timer {timer_id} fired successfully, event {event.id} created")

    except Exception as e:
        db.rollback()
        logger.error(f"Error handling timer fire for timer {timer_id}: {e}")
    finally:
        db.close()


def add_scheduler_job(timer: Timer):
    """
    添加定时器到调度器

    Args:
        timer: Timer 对象
    """
    sched = get_scheduler()
    if not sched:
        raise RuntimeError("Scheduler not initialized")

    job_id = f"timer:{timer.id}"

    # 如果已存在，先移除
    if sched.get_job(job_id):
        sched.remove_job(job_id)

    # 根据类型创建 trigger
    if timer.type == TimerType.ONCE:
        trigger = DateTrigger(run_date=timer.fire_at)
    elif timer.type == TimerType.DAILY:
        hour = timer.time_of_day.hour
        minute = timer.time_of_day.minute
        second = timer.time_of_day.second
        trigger = CronTrigger(hour=hour, minute=minute, second=second)
    else:
        raise ValueError(f"Unknown timer type: {timer.type}")

    # 添加 job
    sched.add_job(
        handle_timer_fire,
        trigger=trigger,
        args=[timer.id],
        id=job_id,
        replace_existing=True
    )

    logger.info(f"Added scheduler job {job_id} for timer {timer.id}")


def remove_scheduler_job(timer_id: int):
    """
    从调度器中移除定时器

    Args:
        timer_id: 定时器 ID
    """
    sched = get_scheduler()
    if not sched:
        return

    job_id = f"timer:{timer_id}"

    if sched.get_job(job_id):
        sched.remove_job(job_id)
        logger.info(f"Removed scheduler job {job_id}")


def update_scheduler_job(timer: Timer):
    """
    更新调度器中的定时器

    Args:
        timer: Timer 对象
    """
    # 简单实现：先移除再添加
    remove_scheduler_job(timer.id)
    if timer.status == TimerStatus.ENABLED:
        add_scheduler_job(timer)


def rebuild_jobs_from_db():
    """
    从数据库重建所有调度任务

    加载所有 status=enabled 的定时器并注册到调度器
    """
    db = SessionLocal()
    try:
        enabled_timers = db.query(Timer).filter(
            Timer.status == TimerStatus.ENABLED
        ).all()

        count = 0
        for timer in enabled_timers:
            try:
                add_scheduler_job(timer)
                count += 1
            except Exception as e:
                logger.error(f"Failed to add job for timer {timer.id}: {e}")

        logger.info(f"Rebuilt {count} scheduler jobs from database")
        return count

    finally:
        db.close()


def start_scheduler():
    """
    启动调度器

    初始化调度器并从数据库加载任务
    """
    sched = init_scheduler()

    # 从数据库加载任务
    rebuild_jobs_from_db()

    # 启动调度器
    sched.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """
    停止调度器
    """
    sched = get_scheduler()
    if sched and sched.running:
        sched.shutdown()
        logger.info("Scheduler stopped")
