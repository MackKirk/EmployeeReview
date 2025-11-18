from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review
from app.utils.questions import get_questions_for_role
from app.utils.ui_overrides import get_rating_panel_html
from app.utils.auth_utils import get_current_user
import uuid
from datetime import datetime
from sqlalchemy.orm import load_only
import re

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def adapt_questions_for_supervisor(questions, employee_name):
    """
    Adapta as questões substituindo 'you'/'your' por 'employee' ou nome do funcionário
    para deixar claro que o supervisor está avaliando o funcionário, não a si mesmo.
    """
    # Capitalizar o nome corretamente (primeira letra de cada palavra em maiúscula)
    if employee_name:
        # Usar title() para capitalizar cada palavra do nome
        employee_ref = employee_name.title()
        employee_possessive = f"{employee_ref}'s"
    else:
        employee_ref = "the employee"
        employee_possessive = "the employee's"
    
    adapted = []
    for q in questions:
        # Criar uma cópia da questão para não modificar a original
        adapted_q = q.copy()
        
        # Substituir no texto da questão
        question_text = adapted_q.get("question", "")
        if question_text:
            # Substituir "your" (case-insensitive, mas preservando capitalização)
            question_text = re.sub(
                r'\bYour\b',
                employee_possessive if employee_name else "The employee's",
                question_text
            )
            question_text = re.sub(
                r'\byour\b',
                employee_possessive if employee_name else "the employee's",
                question_text,
                flags=re.IGNORECASE
            )
            
            # Substituir "you" (case-insensitive, mas preservando capitalização)
            # Evitar substituir em casos como "you're", "you've", etc. (já tratados acima com "your")
            question_text = re.sub(
                r'\bYou\b(?!\w)',
                employee_ref if employee_name else "The employee",
                question_text
            )
            question_text = re.sub(
                r'\byou\b(?!\w)',
                employee_ref if employee_name else "the employee",
                question_text,
                flags=re.IGNORECASE
            )
            
            adapted_q["question"] = question_text
        
        # Substituir na descrição da categoria se existir
        if "category_description" in adapted_q and adapted_q["category_description"]:
            desc_text = adapted_q["category_description"]
            desc_text = re.sub(
                r'\bYour\b',
                employee_possessive if employee_name else "The employee's",
                desc_text
            )
            desc_text = re.sub(
                r'\byour\b',
                employee_possessive if employee_name else "the employee's",
                desc_text,
                flags=re.IGNORECASE
            )
            desc_text = re.sub(
                r'\bYou\b(?!\w)',
                employee_ref if employee_name else "The employee",
                desc_text
            )
            desc_text = re.sub(
                r'\byou\b(?!\w)',
                employee_ref if employee_name else "the employee",
                desc_text,
                flags=re.IGNORECASE
            )
            adapted_q["category_description"] = desc_text
        
        adapted.append(adapted_q)
    
    return adapted


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
    readonly = bool(existing)
    db.close()
    rating_panel_html = get_rating_panel_html()
    # Use the employee's role so supervisor reviews the same questionnaire the employee answered
    selected_questions = get_questions_for_role(employee.role)
    
    # Create maps using question ID for matching (since we'll adapt the question text)
    existing_map = {}
    comment_map = {}
    if existing:
        # Create a mapping from original question text to answer
        question_text_to_answer = {a["question"]: a for a in existing}
        for q in selected_questions:
            original_text = q["question"]
            if original_text in question_text_to_answer:
                answer_data = question_text_to_answer[original_text]
                existing_map[original_text] = answer_data.get("value")
                comment_map[original_text] = answer_data.get("comment")
    
    # Adapt questions to replace "you"/"your" with employee name for supervisor clarity
    adapted_questions = adapt_questions_for_supervisor(selected_questions, employee.name)
    
    # Update maps to use adapted question text for display
    adapted_existing_map = {}
    adapted_comment_map = {}
    for i, q_original in enumerate(selected_questions):
        q_adapted = adapted_questions[i]
        original_text = q_original["question"]
        adapted_text = q_adapted["question"]
        if original_text in existing_map:
            adapted_existing_map[adapted_text] = existing_map[original_text]
        if original_text in comment_map:
            adapted_comment_map[adapted_text] = comment_map[original_text]
    
    return templates.TemplateResponse("supervisor_review.html", {
        "request": request,
        "employee": employee,
        "questions": adapted_questions,
        "existing_map": adapted_existing_map,
        "readonly": readonly,
        "comment_map": adapted_comment_map,
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

    # Use the employee's role so supervisor reviews the same questionnaire the employee answered
    selected_questions = get_questions_for_role(employee.role)
    for q in selected_questions:
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
