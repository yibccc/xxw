"""认证路由模块"""
from flask import Blueprint, request, jsonify, g, session

from src.timerservice.db import SessionLocal
from src.timerservice.auth.jwt import generate_jwt
from src.timerservice.auth.service import register_user, authenticate_user

# 创建认证蓝图
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    用户注册

    请求体:
        {
            "username": "string",
            "password": "string"
        }

    返回:
        {
            "user_id": int,
            "username": "string"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if len(username) < 3 or len(username) > 50:
        return jsonify({"error": "Username must be between 3 and 50 characters"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = SessionLocal()
    try:
        user = register_user(db, username, password)
        return jsonify({
            "user_id": user.id,
            "username": user.username
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Registration failed"}), 500
    finally:
        db.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    用户登录

    请求体:
        {
            "username": "string",
            "password": "string"
        }

    返回:
        {
            "token": "string",
            "user_id": int,
            "username": "string"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db = SessionLocal()
    try:
        user = authenticate_user(db, username, password)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        token = generate_jwt(user.id)

        return jsonify({
            "token": token,
            "user_id": user.id,
            "username": user.username
        }), 200
    finally:
        db.close()


@auth_bp.route("/me", methods=["GET"])
def me():
    """
    获取当前用户信息（需要认证）

    返回:
        {
            "user_id": int,
            "username": "string"
        }
    """
    from src.timerservice.auth.jwt import require_auth
    from src.timerservice.auth.service import get_user_by_id

    # 这里需要装饰器，但 Flask 装饰器不能在函数内部使用
    # 所以我们手动验证
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Missing authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0] != "Bearer":
        return jsonify({"error": "Invalid authorization format"}), 401

    try:
        from src.timerservice.auth.jwt import verify_jwt
        payload = verify_jwt(parts[1])
        user_id = payload["user_id"]
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    db = SessionLocal()
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "user_id": user.id,
            "username": user.username
        }), 200
    finally:
        db.close()
