"""认证服务模块"""
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.timerservice.models import User

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对密码进行 hash"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, username: str, password: str) -> User:
    """
    注册用户

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        创建的用户对象

    Raises:
        ValueError: 用户名已存在
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise ValueError("Username already exists")

    # 创建新用户
    user = User(
        username=username,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    验证用户凭据

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        用户对象（验证成功）或 None（验证失败）
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    根据 ID 获取用户

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        用户对象或 None
    """
    return db.query(User).filter(User.id == user_id).first()
