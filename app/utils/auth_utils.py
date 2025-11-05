from app.db import SessionLocal
from app.models import Employee
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os

def get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    user = db.query(Employee).filter_by(id=user_id).first()
    db.close()
    return user


def _get_serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SESSION_SECRET", "changeme")
    # Salt isolates magic-link tokens from other potential signatures
    return URLSafeTimedSerializer(secret_key=secret, salt="magic-login")


def generate_magic_login_token(user_id: str, redirect_url: str = "/home", role: str = None) -> str:
    s = _get_serializer()
    payload = {"user_id": str(user_id), "redirect": redirect_url}
    if role:
        payload["role"] = role
    return s.dumps(payload)


def verify_magic_login_token(token: str, max_age_seconds: int = None):
    s = _get_serializer()
    if max_age_seconds is None:
        # Default: 7 days
        max_age_seconds = int(os.getenv("MAGIC_LINK_MAX_AGE_SECONDS", "604800"))
    try:
        data = s.loads(token, max_age=max_age_seconds)
        return data
    except (SignatureExpired, BadSignature):
        return None
