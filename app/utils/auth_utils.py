from app.db import SessionLocal
from app.models import Employee

def get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    user = db.query(Employee).filter_by(id=user_id).first()
    db.close()
    return user
