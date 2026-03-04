from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username, User.is_active == True).first()  # noqa: E712
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
