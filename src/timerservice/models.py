"""ORM 模型定义"""
import datetime
from datetime import time as time_type
from typing import Optional

from sqlalchemy import (
    String, Integer, DateTime, Time, Enum as SQLEnum, Index, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # 关系
    timers: Mapped[list["Timer"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    events: Mapped[list["TimerEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_username", "username"),
    )


class TimerType:
    """定时器类型常量"""
    ONCE = "once"
    DAILY = "daily"


class TimerStatus:
    """定时器状态常量"""
    ENABLED = "enabled"
    PAUSED = "paused"
    COMPLETED = "completed"
    DELETED = "deleted"


class Timer(Base):
    """定时器模型"""
    __tablename__ = "timers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(SQLEnum("once", "daily", name="timer_type"), nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum("enabled", "paused", "completed", "deleted", name="timer_status"),
        nullable=False,
        default=TimerStatus.ENABLED
    )

    # once 类型：延迟秒数
    delay_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # daily 类型：每天触发时间
    time_of_day: Mapped[Optional[time_type]] = mapped_column(Time, nullable=True)

    # 计算字段：once 类型的 fire_at，daily 类型的下次触发时间
    fire_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, index=True)
    next_fire_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_fired_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关系
    user: Mapped["User"] = relationship(back_populates="timers")
    events: Mapped[list["TimerEvent"]] = relationship(back_populates="timer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_status_next_fire", "status", "next_fire_at"),
    )


class TimerEvent(Base):
    """定时器事件模型"""
    __tablename__ = "timer_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    timer_id: Mapped[int] = mapped_column(ForeignKey("timers.id"), nullable=False, index=True)
    fired_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, index=True)
    read_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # 关系
    user: Mapped["User"] = relationship(back_populates="events")
    timer: Mapped["Timer"] = relationship(back_populates="events")

    __table_args__ = (
        Index("idx_user_fired", "user_id", "fired_at"),
        Index("idx_user_read", "user_id", "read_at"),
    )
