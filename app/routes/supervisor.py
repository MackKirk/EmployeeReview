from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review
from app.utils.questions import questions
from app.utils.ui_overrides import get_rating_panel_html
from app.utils.auth_utils import get_current_user
import uuid
from datetime import datetime
from sqlalchemy.orm import load_only

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/supervisor/{supervisor_id}", response_class=HTMLResponse)
async def supervisor_dashboard(request: Request, supervisor_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    supervisor = db.query(Employee).filter_by(id=supervisor_id).first()
    is_admin = bool(request.session.get("is_admin"))
    if (
        not current_user
        or str(current_user.id) != supervisor_id
        or not (
            is_admin
            or current_user.role == "director"
            or current_user.role == "supervisor"
            or current_user.is_supervisor
        )
    ):
        db.close()
        return HTMLResponse("Access denied", status_code=403)
    # If the target user is missing entirely, block; otherwise allow directors/admins even if the flag isn't set.
    if not supervisor:
        db.close()
        return HTMLResponse(
            "Supervisor not found or access denied", status_code=403
        )

    subordinates = db.query(Employee).filter_by(supervisor_email=supervisor.name).all()
    data = []
    for emp in subordinates:
        r = db.query(Review).options(
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
        ).filter_by(employee_id=emp.id).first()
        employee_done = bool(r and r.employee_answers)
        supervisor_done = bool(r and r.supervisor_answers)
        data.append({
            "employee": emp,
            "employee_done": employee_done,
            "supervisor_done": supervisor_done,
        })
    db.close()
    return templates.TemplateResponse("supervisor_dashboard.html", {
        "request": request,
        "supervisor": supervisor,
        "subordinates": data,
    })


@router.get("/supervisor/review/{employee_id}", response_class=HTMLResponse)
async def supervisor_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        db.close()
        return HTMLResponse("Employee not found", status_code=404)
    is_admin = bool(request.session.get("is_admin"))
    allowed = False
    if current_user:
        if is_admin or current_user.role == "director":
            allowed = True
        elif current_user.role == "supervisor" or current_user.is_supervisor:
            allowed = (current_user.name == employee.supervisor_email)
    if not allowed:
        db.close()
        return HTMLResponse("Access denied", status_code=403)

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
    ).filter_by(employee_id=employee.id).first()
    existing = review.supervisor_answers if review else None
    existing_map = {a["question"]: a.get("value") for a in existing} if existing else {}
    comment_map = {a["question"]: a.get("comment") for a in existing} if existing else {}
    readonly = bool(existing)
    db.close()
    rating_panel_html = get_rating_panel_html()
    return templates.TemplateResponse("supervisor_review.html", {
        "request": request,
        "employee": employee,
        "questions": questions,
        "existing_map": existing_map,
        "readonly": readonly,
        "comment_map": comment_map,
        "rating_panel_html": rating_panel_html,
    })


@router.post("/supervisor/review/{employee_id}/submit")
async def submit_supervisor_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        db.close()
        return HTMLResponse("Employee not found", status_code=404)
    is_admin = bool(request.session.get("is_admin"))
    allowed = False
    if current_user:
        if is_admin or current_user.role == "director":
            allowed = True
        elif current_user.role == "supervisor" or current_user.is_supervisor:
            allowed = (current_user.name == employee.supervisor_email)
    if not allowed:
        db.close()
        return HTMLResponse("Access denied", status_code=403)

    form = await request.form()
    answers = []

    for q in questions:
        value = form.get(f"q{q['id']}")
        comment = None
        if q["type"] == "scale":
            comment = form.get(f"c{q['id']}")
        elif q["type"] == "yesno" and q.get("category") == "COMPANY VEHICLE AND MACHINERY":
            comment = form.get(f"c{q['id']}")
        if q["type"] == "scale":
            value = int(value) if value else None
        elif q["type"] == "yesno":
            value = value if value in ("Yes", "No") else None
        answers.append(
            {
                "question": q["question"],
                "type": q["type"],
                "value": value,
                "comment": comment,
            }
        )

    # Create or update review
    existing = db.query(Review).filter_by(employee_id=employee.id).first()
    if existing:
        existing.supervisor_answers = answers
        existing.updated_at = datetime.utcnow()
    else:
        review = Review(
            id=uuid.uuid4(),
            employee_id=employee.id,
            supervisor_id=current_user.id,
            supervisor_answers=answers,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(review)

    db.commit()
    db.close()

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "message": "✅ Review saved successfully!",
            "redirect_url": "/home",
            "seconds": 5,
        },
    )
