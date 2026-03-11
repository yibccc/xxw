"""JWT 工具模块"""
import datetime
from functools import wraps
import jwt
from flask import g, request, jsonify, current_app

from src.timerservice.config import config


def generate_jwt(user_id: int) -> str:
    """
    生成 JWT token

    Args:
        user_id: 用户 ID

    Returns:
        JWT token 字符串
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) +
               datetime.timedelta(seconds=config.JWT_EXPIRES_SECONDS),
        "iat": datetime.datetime.now(datetime.timezone.utc)
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def verify_jwt(token: str) -> dict:
    """
    验证 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload

    Raises:
        jwt.InvalidTokenError: token 无效或过期
    """
    return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])


def require_auth(f):
    """
    JWT 认证装饰器

    从请求头中获取 Authorization: Bearer <token>，
    验证后将 user_id 注入到 g.user_id
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401

        # 检查 Bearer 格式
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"error": "Invalid authorization format"}), 401

        token = parts[1]

        try:
            payload = verify_jwt(token)
            g.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated_function
