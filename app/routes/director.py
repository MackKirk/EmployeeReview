from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review, EmailEvent
from app.utils.auth_utils import get_current_user
from app.utils.questions import questions
from app.utils.auth_utils import generate_magic_login_token
import os
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/director/review/{employee_id}", response_class=HTMLResponse)
async def director_view_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    review = db.query(Review).filter_by(employee_id=employee_id).first()
    if not ((current_user and current_user.role == "director") or is_admin):
        db.close()
        return HTMLResponse("Access restricted", status_code=403)
    if not employee or not review:
        db.close()
        return HTMLResponse("Employee or review not found.", status_code=404)

    if not review.employee_answers or not review.supervisor_answers:
        db.close()
        return HTMLResponse("Incomplete review.", status_code=400)
    existing = review.director_comments or []
    comment_map = {c["question"]: c.get("comment") for c in existing}

    allow_comments = bool(current_user and current_user.role == "director")
    return templates.TemplateResponse(
        "director_review.html",
        {
            "request": request,
            "employee": employee,
            "review": review,
            "questions": questions,
            "comment_map": comment_map,
            "allow_comments": allow_comments,
        },
    )

@router.post("/director/review/{employee_id}/submit")
async def save_director_comments(request: Request, employee_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    review = db.query(Review).filter_by(employee_id=employee_id).first()
    if not current_user or current_user.role != "director":
        db.close()
        return HTMLResponse("Access restricted", status_code=403)
    if not review:
        db.close()
        return HTMLResponse("Review not found.", status_code=404)

    form = await request.form()
    comments = []
    for q in questions:
        comment = form.get(f"c{q['id']}")
        comments.append({"question": q["question"], "comment": comment})

    review.director_comments = comments
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


@router.get("/director/dashboard", response_class=HTMLResponse)
async def director_dashboard(request: Request):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    if not current_user or current_user.role != "director":
        db.close()
        return HTMLResponse("Access restricted", status_code=403)

    from sqlalchemy.orm import joinedload
    reviews = db.query(Review).options(joinedload(Review.employee)).all()
    db.close()

    return templates.TemplateResponse("director_dashboard.html", {
        "request": request,
        "reviews": reviews
    })


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    db: Session = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload
        employees = db.query(Employee).all()
        rows = []
        for emp in employees:
            r = db.query(Review).options(joinedload(Review.employee)).filter_by(employee_id=emp.id).first()
            employee_done = bool(r and r.employee_answers)
            supervisor_done = bool(r and r.supervisor_answers)
            director_done = bool(r and r.director_comments)
            # Email tracking
            has_sent = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="sent").first() is not None
            has_clicked = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="clicked").first() is not None
            rows.append({
                "employee": emp,
                "employee_done": employee_done,
                "supervisor_done": supervisor_done,
                "director_done": director_done,
                "has_sent": has_sent,
                "has_clicked": has_clicked,
            })
        all_names = [e.name for e in employees]
    finally:
        db.close()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "rows": rows,
        "names": all_names,
        "allowed_roles": ["employee", "supervisor", "administration", "director"],
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
    })


@router.post("/admin/update-employee/{employee_id}")
async def admin_update_employee(request: Request, employee_id: str, role: str = Form(None), supervisor_name: str = Form(None)):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    allowed = {"employee", "supervisor", "administration", "director"}
    role_val = (role or "").strip().lower()
    if role_val and role_val not in allowed:
        return HTMLResponse("Invalid role", status_code=400)

    db: Session = SessionLocal()
    try:
        emp = db.query(Employee).filter_by(id=employee_id).first()
        if not emp:
            return HTMLResponse("Employee not found", status_code=404)

        changed = False
        if role_val and emp.role != role_val:
            emp.role = role_val
            # If set to supervisor, ensure is_supervisor; otherwise clear it
            if role_val == "supervisor":
                if not emp.is_supervisor:
                    emp.is_supervisor = True
            else:
                if emp.is_supervisor:
                    emp.is_supervisor = False
            changed = True

        sup_name_val = (supervisor_name or "").strip()
        if emp.supervisor_email != sup_name_val:
            # Allow clearing supervisor by selecting None
            emp.supervisor_email = sup_name_val or None
            if sup_name_val:
                # Ensure the named supervisor is flagged as supervisor
                sup_emp = db.query(Employee).filter(Employee.name == sup_name_val).first()
                if sup_emp and not sup_emp.is_supervisor:
                    sup_emp.is_supervisor = True
            changed = True

        if changed:
            db.commit()

        from fastapi.responses import RedirectResponse
        return RedirectResponse("/admin?message=Employee%20updated", status_code=302)
    finally:
        db.close()


@router.get("/admin/open-review/{employee_id}")
async def admin_open_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        base_url = "https://" + base_url
    base_url = base_url.rstrip("/")
    db: Session = SessionLocal()
    try:
        emp = db.query(Employee).filter_by(id=employee_id).first()
        if not emp:
            return HTMLResponse("Employee not found", status_code=404)
        # Redirect to home after logging in as the selected user (for testing session as that user)
        token = generate_magic_login_token(str(emp.id), redirect_url="/home", role=emp.role)
        link = f"{base_url}/magic-login?token={token}"
        from fastapi.responses import RedirectResponse
        return RedirectResponse(link, status_code=302)
    finally:
        db.close()


@router.get("/admin/questions", response_class=HTMLResponse)
async def admin_questions_editor(request: Request, role: str = "employee"):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    # Load current questions: prefer overrides file, fallback to defaults
    from app.utils.questions import get_questions_for_role
    qs = get_questions_for_role(role)
    json_text = json.dumps(qs, ensure_ascii=False, indent=2)
    return templates.TemplateResponse("admin_questions.html", {
        "request": request,
        "role": role,
        "json_text": json_text,
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
    })


@router.post("/admin/questions", response_class=HTMLResponse)
async def admin_questions_save(request: Request, role: str = Form("employee"), json: str = Form("")):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    role = (role or "").strip().lower()
    if role not in {"employee", "supervisor", "administration"}:
        return HTMLResponse("Invalid role", status_code=400)

    try:
        data = json_module.loads(json) if False else None  # placeholder to keep name unique
    except Exception:
        data = None
    # Proper parse
    try:
        payload = json.loads(json)
        if not isinstance(payload, list):
            raise ValueError("JSON must be a list of questions")
        # Basic validation
        allowed_types = {"scale", "yesno", "text"}
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Each question must be an object")
            if not isinstance(item.get("id"), int):
                raise ValueError("id must be integer")
            if item.get("type") not in allowed_types:
                raise ValueError("type must be one of scale|yesno|text")
            if not item.get("question") or not item.get("category"):
                raise ValueError("question and category are required")
    except Exception as e:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"/admin/questions?role={role}&error={str(e).replace(' ', '%20')}", status_code=302)

    # Write overrides file (merge with existing)
    path = os.path.join("app", "data", "questions_overrides.json")
    try:
        existing = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f) or {}
    except Exception:
        existing = {}
    existing[role] = payload
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"/admin/questions?role={role}&error=Save%20failed:%20{str(e).replace(' ', '%20')}", status_code=302)

    from fastapi.responses import RedirectResponse
    return RedirectResponse(f"/admin/questions?role={role}&message=Saved", status_code=302)


@router.post("/admin/questions/preview", response_class=HTMLResponse)
async def admin_questions_preview(request: Request, role: str = Form("employee"), json: str = Form("")):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    try:
        payload = json.loads(json)
        if not isinstance(payload, list):
            raise ValueError("JSON must be a list of questions")
    except Exception as e:
        return HTMLResponse(f"Invalid JSON: {e}", status_code=400)

    return templates.TemplateResponse("admin_questions_preview.html", {
        "request": request,
        "role": role,
        "questions": payload,
    })