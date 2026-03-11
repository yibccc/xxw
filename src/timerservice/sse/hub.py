"""SSE Hub - 管理客户端连接和消息推送"""
import json
import queue
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SSEConnection:
    """SSE 连接对象"""
    user_id: int
    message_queue: queue.Queue
    closed: bool = False


class SSEHub:
    """SSE 消息中心，管理所有客户端连接"""

    def __init__(self):
        # user_id -> List[SSEConnection]
        self._connections: Dict[int, List[SSEConnection]] = {}
        self._lock = threading.Lock()

    def register(self, user_id: int) -> SSEConnection:
        """
        注册新连接

        Args:
            user_id: 用户 ID

        Returns:
            SSEConnection 对象
        """
        conn = SSEConnection(
            user_id=user_id,
            message_queue=queue.Queue(),
            closed=False
        )

        with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = []
            self._connections[user_id].append(conn)

        return conn

    def unregister(self, user_id: int, conn: SSEConnection):
        """
        注销连接

        Args:
            user_id: 用户 ID
            conn: 连接对象
        """
        with self._lock:
            if user_id in self._connections:
                if conn in self._connections[user_id]:
                    self._connections[user_id].remove(conn)
                    conn.closed = True

                # 如果该用户没有连接了，删除键
                if not self._connections[user_id]:
                    del self._connections[user_id]

    def publish(self, user_id: int, event_name: str, data: dict):
        """
        向指定用户推送消息

        Args:
            user_id: 用户 ID
            event_name: 事件名称
            data: 事件数据
        """
        # 构建 SSE 消息
        message = {
            "event": event_name,
            "data": data
        }

        with self._lock:
            if user_id not in self._connections:
                return  # 用户没有连接

            # 向该用户的所有连接推送消息
            for conn in self._connections[user_id]:
                if not conn.closed:
                    try:
                        conn.message_queue.put_nowait(message)
                    except queue.Full:
                        # 队列满了，跳过这条消息
                        pass

    def publish_ping(self):
        """
        向所有连接发送 ping 消息（保活）
        """
        with self._lock:
            for user_id, connections in self._connections.items():
                for conn in connections:
                    if not conn.closed:
                        try:
                            conn.message_queue.put_nowait({"event": "ping"})
                        except queue.Full:
                            pass

    def get_connection_count(self, user_id: int) -> int:
        """
        获取指定用户的连接数

        Args:
            user_id: 用户 ID

        Returns:
            连接数量
        """
        with self._lock:
            if user_id not in self._connections:
                return 0
            return len(self._connections[user_id])


# 全局 SSE Hub 实例
sse_hub = SSEHub()
