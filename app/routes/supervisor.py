from fastapi import APIRouter, Request, Form
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


@router.get("/supervisor/{supervisor_id}", response_class=HTMLResponse)
async def supervisor_dashboard(request: Request, supervisor_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    supervisor = db.query(Employee).filter_by(id=supervisor_id).first()
    if (
        not current_user
        or current_user.role != "supervisor"
        or str(current_user.id) != supervisor_id
    ):
        db.close()
        return HTMLResponse("Acesso negado", status_code=403)
    if not supervisor or not supervisor.is_supervisor:
        db.close()
        return HTMLResponse(
            "Supervisor não encontrado ou acesso negado", status_code=403
        )

    subordinates = db.query(Employee).filter_by(supervisor_email=supervisor.email).all()
    db.close()
    return templates.TemplateResponse("supervisor_dashboard.html", {
        "request": request,
        "supervisor": supervisor,
        "subordinates": subordinates
    })


@router.get("/supervisor/review/{employee_id}", response_class=HTMLResponse)
async def supervisor_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        db.close()
        return HTMLResponse("Funcionário não encontrado", status_code=404)
    if (
        not current_user
        or current_user.role != "supervisor"
        or current_user.email != employee.supervisor_email
    ):
        db.close()
        return HTMLResponse("Acesso negado", status_code=403)

    return templates.TemplateResponse("supervisor_review.html", {
        "request": request,
        "employee": employee,
        "questions": questions
    })


@router.post("/supervisor/review/{employee_id}/submit")
async def submit_supervisor_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        db.close()
        return HTMLResponse("Funcionário não encontrado", status_code=404)
    if (
        not current_user
        or current_user.role != "supervisor"
        or current_user.email != employee.supervisor_email
    ):
        db.close()
        return HTMLResponse("Acesso negado", status_code=403)

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

    # Cria ou atualiza review
    existing = db.query(Review).filter_by(employee_id=employee.id).first()
    if existing:
        existing.supervisor_answers = answers
        existing.updated_at = datetime.utcnow()
    else:
        review = Review(
            id=uuid.uuid4(),
            employee_id=employee.id,
            supervisor_id=employee.id,
            supervisor_answers=answers,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(review)

    db.commit()
    db.close()

    return HTMLResponse("✅ Avaliação salva com sucesso!", status_code=200)
