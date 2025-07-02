from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review
from app.utils.questions import questions
from app.utils.auth_utils import get_current_user
import uuid
from datetime import datetime


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/employee/{employee_id}", response_class=HTMLResponse)
async def employee_review(request: Request, employee_id: str):

    current_user = get_current_user(request)
    if not current_user or str(current_user.id) != employee_id:
        return HTMLResponse("Access denied", status_code=403)

    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    db.close()
    if not employee:
        return HTMLResponse("Employee not found", status_code=404)
    return templates.TemplateResponse("employee_review.html", {
        "request": request,
        "employee": employee,
        "questions": questions
    })



@router.post("/employee/{employee_id}/submit")
async def submit_employee_review(request: Request, employee_id: str):
    db: Session = SessionLocal()

    current_user = get_current_user(request)
    if not current_user or str(current_user.id) != employee_id:
        return HTMLResponse("Access denied", status_code=403)

    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        db.close()
        return HTMLResponse("Employee not found", status_code=404)

    from app.utils.questions import questions

    form = await request.form()
    answers = []

    for q in questions:
        value = form.get(f"q{q['id']}")
        if q["type"] == "scale":
            value = int(value) if value else None
        answers.append({
            "question": q["question"],
            "type": q["type"],
            "value": value
        })

    # Create or update review
    existing = db.query(Review).filter_by(employee_id=employee.id).first()
    if existing:
        existing.employee_answers = answers
        existing.updated_at = datetime.utcnow()
    else:
        review = Review(
            id=uuid.uuid4(),
            employee_id=employee.id,
            employee_answers=answers,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(review)

    db.commit()
    db.close()

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "message": "✅ Answers submitted successfully!",
            "redirect_url": "/home",
            "seconds": 5,
        },
    )
