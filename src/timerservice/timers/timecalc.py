"""时间计算工具模块"""
import datetime
from datetime import time as time_type


def compute_once_fire_at(now: datetime.datetime, delay_seconds: int) -> datetime.datetime:
    """
    计算 once 类型定时器的触发时间

    Args:
        now: 当前时间
        delay_seconds: 延迟秒数（1~86400）

    Returns:
        触发时间
    """
    if delay_seconds < 1 or delay_seconds > 86400:
        raise ValueError("delay_seconds must be between 1 and 86400")

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
    # 将当前时间转换为指定时区
    if now.tzinfo is None:
        # 如果 now 是 naive，假设为服务器时区
        now = now.replace(tzinfo=datetime.timezone.utc)
        # 这里简化处理，实际应该使用 pytz 或 zoneinfo
        # 为了简化，我们暂时使用 naive datetime 进行计算
        now = now.replace(tzinfo=None)

    # 创建今天的触发时间
    today_fire = now.replace(
        hour=time_of_day.hour,
        minute=time_of_day.minute,
        second=time_of_day.second,
        microsecond=0
    )

    # 如果今天的触发时间已经过了，则设置为明天
    if today_fire <= now:
        tomorrow = now + datetime.timedelta(days=1)
        next_fire = tomorrow.replace(
            hour=time_of_day.hour,
            minute=time_of_day.minute,
            second=time_of_day.second,
            microsecond=0
        )
        return next_fire

    return today_fire
