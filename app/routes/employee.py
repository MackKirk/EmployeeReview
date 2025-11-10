from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review
from app.utils.questions import get_questions_for_role
from app.utils.ui_overrides import get_rating_panel_html, get_instructions_html
from app.utils.auth_utils import get_current_user
import uuid
from datetime import datetime
from sqlalchemy.orm import load_only


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/employee/{employee_id}", response_class=HTMLResponse)
async def employee_review(request: Request, employee_id: str):

    current_user = get_current_user(request)
    if not current_user or str(current_user.id) != employee_id:
        return HTMLResponse("Access denied", status_code=403)

    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    review = db.query(Review).options(
        load_only(
            Review.id,
            Review.employee_id,
            Review.employee_answers,
            Review.supervisor_answers,
            Review.director_comments,
            Review.status,
            Review.created_at,
            Review.updated_at,
        )
    ).filter_by(employee_id=employee_id).first()
    existing = review.employee_answers if review else None
    existing_map = {a["question"]: a.get("value") for a in existing} if existing else {}
    readonly = bool(existing)
    db.close()
    if not employee:
        return HTMLResponse("Employee not found", status_code=404)
    selected_questions = get_questions_for_role(employee.role)
    rating_panel_html = get_rating_panel_html()
    instructions_html = get_instructions_html()
    return templates.TemplateResponse("employee_review.html", {
        "request": request,
        "employee": employee,
        "questions": selected_questions,
        "existing_map": existing_map,
        "readonly": readonly,
        "rating_panel_html": rating_panel_html,
        "instructions_html": instructions_html,
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

    from app.utils.questions import get_questions_for_role

    form = await request.form()
    answers = []

    selected_questions = get_questions_for_role(employee.role)
    for q in selected_questions:
        value = form.get(f"q{q['id']}")
        if q["type"] == "scale":
            value = int(value) if value else None
        elif q["type"] == "yesno":
            value = value if value in ("Yes", "No") else None
        answers.append({
            "question": q["question"],
            "type": q["type"],
            "value": value
        })

    # Create or update review
    existing = db.query(Review).options(
        load_only(Review.id, Review.employee_id, Review.employee_answers, Review.created_at, Review.updated_at)
    ).filter_by(employee_id=employee.id).first()
    if existing and existing.employee_answers:
        db.close()
        return HTMLResponse("Review already submitted", status_code=400)
    elif existing:
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
