from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review
from app.utils.auth_utils import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return HTMLResponse("Acesso negado", status_code=403)

    db: Session = SessionLocal()

    # Review of the logged in user
    review = db.query(Review).filter_by(employee_id=user.id).first()
    filled = review and review.employee_answers
    employee_card_title = "Ver minhas respostas" if filled else "Preencher autoavaliação"

    # Pending reviews for supervisor
    supervisor_pending = 0
    if user.role == "supervisor":
        subordinates = db.query(Employee).filter_by(supervisor_email=user.email).all()
        for emp in subordinates:
            r = db.query(Review).filter_by(employee_id=emp.id).first()
            if not r or not r.supervisor_answers:
                supervisor_pending += 1

    # Pending reviews for director
    director_pending = 0
    if user.role == "director":
        all_reviews = db.query(Review).all()
        for r in all_reviews:
            if r.employee_answers and r.supervisor_answers and not r.director_comments:
                director_pending += 1

    db.close()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
        "employee_card_title": employee_card_title,
        "show_supervisor_card": user.role == "supervisor",
        "show_director_card": user.role == "director",
        "supervisor_pending": supervisor_pending,
        "director_pending": director_pending,
    })
