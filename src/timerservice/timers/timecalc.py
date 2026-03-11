"""时间计算工具模块"""
import datetime
from datetime import time as time_type
from zoneinfo import ZoneInfo

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def ensure_shanghai_tz(dt: datetime.datetime) -> datetime.datetime:
    """
    确保 datetime 带有上海时区信息

    Args:
        dt: 输入的 datetime

    Returns:
        带上海时区的 datetime
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # naive datetime，假设为上海时区
        return dt.replace(tzinfo=SHANGHAI_TZ)
    return dt


def compute_once_fire_at(now: datetime.datetime, delay_seconds: int) -> datetime.datetime:
    """
    计算 once 类型定时器的触发时间

    Args:
        now: 当前时间
        delay_seconds: 延迟秒数（1~86400）

    Returns:
        触发时间（带上海时区）
    """
    if delay_seconds < 1 or delay_seconds > 86400:
        raise ValueError("delay_seconds must be between 1 and 86400")

    # 确保 now 带有时区信息
    now = ensure_shanghai_tz(now)

    return now + datetime.timedelta(seconds=delay_seconds)


def compute_daily_next_fire_at(
    now: datetime.datetime,
    time_of_day: time_type,
    tz: str = "Asia/Shanghai"
) -> datetime.datetime:
    """
    计算 daily 类型定时器的下次触发时间

    Args:
        now: 当前时间
        time_of_day: 触发时间（HH:MM:SS）
        tz: 时区（默认 Asia/Shanghai）

    Returns:
        下次触发时间（含时区信息）
    """
    # 确保 now 带有时区信息
    now = ensure_shanghai_tz(now)

    # 创建今天的触发时间
    today_fire = now.replace(
        hour=time_of_day.hour,
        minute=time_of_day.minute,
        second=time_of_day.second,
        microsecond=0,
        tzinfo=SHANGHAI_TZ
    )

    # 如果今天的触发时间已经过了，则设置为明天
    if today_fire <= now:
        tomorrow = now + datetime.timedelta(days=1)
        next_fire = tomorrow.replace(
            hour=time_of_day.hour,
            minute=time_of_day.minute,
            second=time_of_day.second,
            microsecond=0,
            tzinfo=SHANGHAI_TZ
        )
        return next_fire

    return today_fire
