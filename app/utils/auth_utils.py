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


def generate_magic_login_token(user_id: str, redirect_url: str = "/home", role: str = None, never_expires: bool = False) -> str:
    s = _get_serializer()
    payload = {"user_id": str(user_id), "redirect": redirect_url}
    if role:
        payload["role"] = role
    if never_expires:
        payload["never_expires"] = True
    return s.dumps(payload)


def verify_magic_login_token(token: str, max_age_seconds: int = None):
    s = _get_serializer()
    if max_age_seconds is None:
        # Default: 7 days
        max_age_seconds = int(os.getenv("MAGIC_LINK_MAX_AGE_SECONDS", "604800"))
    
    # First, try with the normal max_age
    try:
        data = s.loads(token, max_age=max_age_seconds)
        return data
    except SignatureExpired:
        # Token expired according to normal max_age
        # Check if it has never_expires flag by trying with a very large max_age
        # Use 10 years as "never expires" (practical never)
        very_large_max_age = 315360000  # ~10 years
        try:
            data = s.loads(token, max_age=very_large_max_age)
            # If it has never_expires flag, return it even though it expired with normal max_age
            if data.get("never_expires"):
                return data
            # Otherwise, it's expired
            return None
        except (SignatureExpired, BadSignature):
            # Token is invalid or expired even with very large max_age
            return None
    except BadSignature:
        # Invalid token signature
        return None
