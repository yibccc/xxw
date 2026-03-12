"""SSE 路由模块"""
import json
import time
import queue
from datetime import datetime
from flask import Blueprint, request, Response, stream_with_context

from src.timerservice.auth.jwt import verify_jwt
from src.timerservice.sse.hub import sse_hub, SSEConnection

sse_bp = Blueprint("sse", __name__)


def format_sse_message(event: str, data: dict) -> str:
    """
    格式化 SSE 消息

    Args:
        event: 事件名称
        data: 事件数据

    Returns:
        格式化后的 SSE 消息字符串
    """
    data_str = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {data_str}\n\n"


def generate_sse_stream(conn: SSEConnection):
    """
    生成 SSE 流

    Args:
        conn: SSE 连接对象

    Yields:
        SSE 消息字符串
    """
    ping_interval = 30  # 30 秒发送一次 ping
    last_ping = time.time()

    try:
        while not conn.closed:
            try:
                # 尝试从队列获取消息，超时 1 秒
                message = conn.message_queue.get(timeout=1)

                if message["event"] == "ping":
                    # ping 消息使用注释格式
                    yield ": ping\n\n"
                else:
                    yield format_sse_message(message["event"], message["data"])

                last_ping = time.time()

            except queue.Empty:
                # 队列为空，检查是否需要发送 ping
                now = time.time()
                if now - (last_ping + ping_interval) > 0:
                    yield ": ping\n\n"
                    last_ping = now

    except GeneratorExit:
        # 客户端断开连接
        pass
    finally:
        # 清理连接
        sse_hub.unregister(conn.user_id, conn)


@sse_bp.route("/stream", methods=["GET"])
def stream():
    """
    SSE 端点

    从请求头或查询参数中获取 token，
    建立持久连接并推送事件。
    """
    # 尝试从请求头获取 token
    token = None
    auth_header = request.headers.get("Authorization")

    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0] == "Bearer":
            token = parts[1]

    if not token:
        return {"error": "Missing authorization token"}, 401

    try:
        payload = verify_jwt(token)
        user_id = payload["user_id"]
    except Exception:
        return {"error": "Invalid token"}, 401

    # 注册连接
    conn = sse_hub.register(user_id)

    # 发送连接成功消息
    conn.message_queue.put({
        "event": "connected",
        "data": {"user_id": user_id, "timestamp": datetime.now().isoformat()}
    })

    # 返回流式响应
    return Response(
        stream_with_context(generate_sse_stream(conn)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 配置
            "Connection": "keep-alive",
        }
    )
