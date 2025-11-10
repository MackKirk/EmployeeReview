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
from app.utils.ui_overrides import get_rating_panel_html
from datetime import datetime
import re
from sqlalchemy.orm import load_only
from sqlalchemy import text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/director/review/{employee_id}", response_class=HTMLResponse)
async def director_view_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    review = db.query(Review).options(
        load_only(
            Review.id,
            Review.employee_id,
            Review.supervisor_id,
            Review.employee_answers,
            Review.supervisor_answers,
            Review.director_comments,
            Review.status,
            Review.created_at,
            Review.updated_at,
        )
    ).filter_by(employee_id=employee_id).first()
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
    rating_panel_html = get_rating_panel_html()
    return templates.TemplateResponse(
        "director_review.html",
        {
            "request": request,
            "employee": employee,
            "review": review,
            "questions": questions,
            "comment_map": comment_map,
            "rating_panel_html": rating_panel_html,
            "allow_comments": allow_comments,
        },
    )

@router.post("/director/review/{employee_id}/submit")
async def save_director_comments(request: Request, employee_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    review = db.query(Review).options(
        load_only(
            Review.id,
            Review.employee_id,
            Review.supervisor_id,
            Review.employee_answers,
            Review.supervisor_answers,
            Review.director_comments,
            Review.status,
            Review.created_at,
            Review.updated_at,
        )
    ).filter_by(employee_id=employee_id).first()
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
    reviews = db.query(Review).options(
        load_only(
            Review.id,
            Review.employee_id,
            Review.supervisor_id,
            Review.employee_answers,
            Review.supervisor_answers,
            Review.director_comments,
            Review.status,
            Review.created_at,
            Review.updated_at,
        ),
        joinedload(Review.employee),
    ).all()
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
        # Check if schedule column exists to avoid 500 before migration runs
        col_exists = False
        try:
            exists_sql = text("SELECT 1 FROM information_schema.columns WHERE table_name='reviews' AND column_name='employee_scheduled_at'")
            col_exists = db.execute(exists_sql).first() is not None
        except Exception:
            col_exists = False
        rows = []
        for emp in employees:
            r = db.query(Review).options(
                load_only(
                    Review.id,
                    Review.employee_id,
                    Review.supervisor_id,
                    Review.employee_answers,
                    Review.supervisor_answers,
                    Review.director_comments,
                    Review.status,
                    Review.created_at,
                    Review.updated_at,
                ),
                joinedload(Review.employee),
            ).filter_by(employee_id=emp.id).first()
            employee_done = bool(r and r.employee_answers)
            supervisor_done = bool(r and r.supervisor_answers)
            director_done = bool(r and r.director_comments)
            # Email tracking
            has_sent = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="sent").first() is not None
            has_clicked = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="clicked").first() is not None
            sched_display = None
            sched_value = ""
            if col_exists and r:
                try:
                    # Load schedule lazily via direct SQL to avoid selecting missing column elsewhere
                    srow = db.execute(
                        text("SELECT employee_scheduled_at FROM reviews WHERE id=:id"),
                        {"id": str(r.id)},
                    ).first()
                    if srow and srow[0]:
                        sched_display = srow[0].strftime("%Y-%m-%d %H:%M")
                        sched_value = srow[0].strftime("%Y-%m-%dT%H:%M")
                except Exception:
                    pass
            rows.append({
                "employee": emp,
                "employee_done": employee_done,
                "supervisor_done": supervisor_done,
                "director_done": director_done,
                "has_sent": has_sent,
                "has_clicked": has_clicked,
                "self_scheduled_at_display": sched_display,
                "self_scheduled_at_value": sched_value,
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
async def admin_update_employee(request: Request, employee_id: str, role: str = Form(None), supervisor_name: str = Form(None), self_scheduled_at: str = Form(None)):
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

        # Handle scheduling the employee self review (only if column exists)
        schedule_val = (self_scheduled_at or "").strip()
        try:
            exists_sql = text("SELECT 1 FROM information_schema.columns WHERE table_name='reviews' AND column_name='employee_scheduled_at'")
            schedule_col_exists = db.execute(exists_sql).first() is not None
        except Exception:
            schedule_col_exists = False
        if schedule_col_exists:
            if schedule_val:
                try:
                    # Expecting 'YYYY-MM-DDTHH:MM' from input[type=datetime-local]
                    parsed = datetime.strptime(schedule_val, "%Y-%m-%dT%H:%M")
                except Exception:
                    from fastapi.responses import RedirectResponse
                    return RedirectResponse("/admin?error=Invalid%20date%20format", status_code=302)
                # Find or create review
                review = db.query(Review).options(
                    load_only(Review.id, Review.employee_id)
                ).filter_by(employee_id=emp.id).first()
                if not review:
                    review = Review(employee_id=emp.id)
                    db.add(review)
                    db.flush()
                # Duplicate check: another review with same datetime
                dup = db.execute(
                    text("SELECT 1 FROM reviews WHERE employee_scheduled_at = :dt AND employee_id <> :eid LIMIT 1"),
                    {"dt": parsed, "eid": str(emp.id)},
                ).first()
                if dup:
                    from fastapi.responses import RedirectResponse
                    return RedirectResponse("/admin?error=Já%20existe%20um%20agendamento%20com%20esta%20data%20e%20hora", status_code=302)
                # Update via direct SQL to avoid ORM selecting missing columns
                if review and getattr(review, "id", None):
                    db.execute(
                        text("UPDATE reviews SET employee_scheduled_at = :dt WHERE id = :id"),
                        {"dt": parsed, "id": str(review.id)},
                    )
                changed = True
            else:
                # Allow clearing the schedule
                review = db.query(Review).options(
                    load_only(Review.id, Review.employee_id)
                ).filter_by(employee_id=emp.id).first()
                if review and getattr(review, "id", None):
                    db.execute(
                        text("UPDATE reviews SET employee_scheduled_at = NULL WHERE id = :id"),
                        {"id": str(review.id)},
                    )
                    changed = True

        if changed:
            db.commit()

        from fastapi.responses import RedirectResponse
        return RedirectResponse("/admin?message=Employee%20updated", status_code=302)
    finally:
        db.close()


@router.post("/admin/bulk-update-supervisors", response_class=HTMLResponse)
async def admin_bulk_update_supervisors(request: Request):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    form = await request.form()
    # Collect mapping supervisor_name[employee_id] => value
    pattern = re.compile(r"^supervisor_name\[(.+)\]$")
    updates = {}
    for key, value in form.multi_items():
        m = pattern.match(key)
        if not m:
            continue
        emp_id = m.group(1)
        sup_name_val = (value or "").strip()
        # Allow blank (clears supervisor)
        updates[emp_id] = sup_name_val or None

    if not updates:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/admin?error=Nenhuma%20alteração%20informada", status_code=302)

    db: Session = SessionLocal()
    changed = 0
    try:
        for emp_id, sup_name in updates.items():
            emp = db.query(Employee).filter_by(id=emp_id).first()
            if not emp:
                continue
            if emp.supervisor_email != (sup_name or None):
                emp.supervisor_email = sup_name or None
                if sup_name:
                    sup_emp = db.query(Employee).filter(Employee.name == sup_name).first()
                    if sup_emp and not sup_emp.is_supervisor:
                        sup_emp.is_supervisor = True
                changed += 1
        if changed:
            db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"/admin?message=Atualizado:%20{changed}", status_code=302)
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
async def admin_questions_save(request: Request, role: str = Form("employee"), json_text: str = Form("", alias="json")):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    role = (role or "").strip().lower()
    if role not in {"employee", "supervisor", "administration"}:
        return HTMLResponse("Invalid role", status_code=400)

    try:
        payload = json.loads(json_text)
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

@router.get("/admin/ui", response_class=HTMLResponse)
async def admin_ui_editor(request: Request):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)
    path = os.path.join("app", "data", "ui_overrides.json")
    rating_html = ""
    instructions_html = ""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
                rating_html = data.get("rating_panel_html") or ""
                instructions_html = data.get("instructions_html") or ""
        except Exception:
            pass
    # Prefill defaults for convenience if nothing saved yet
    if not rating_html:
        rating_html = """
<div style="padding:12px 16px; border-bottom:1px solid #f1f5f9; display:flex; align-items:center; justify-content:space-between;">
  <div style="font-weight:700; color:#1f2937;">Rating Scale</div>
</div>
<div style="padding:12px 16px;">
  <table style="width:100%; border-collapse:collapse; font-size:13px; color:#374151;">
    <thead>
      <tr>
        <th style="text-align:left; padding:6px 4px; border-bottom:1px solid #e5e7eb; color:#6b7280;">Score</th>
        <th style="text-align:left; padding:6px 4px; border-bottom:1px solid #e5e7eb; color:#6b7280;">Meaning</th>
        <th style="text-align:left; padding:6px 4px; border-bottom:1px solid #e5e7eb; color:#6b7280;">Example</th>
      </tr>
    </thead>
    <tbody>
      <tr><td style="padding:6px 4px;">5</td><td style="padding:6px 4px;">Outstanding</td><td style="padding:6px 4px;">Goes above and beyond every day</td></tr>
      <tr><td style="padding:6px 4px;">4</td><td style="padding:6px 4px;">Above Average</td><td style="padding:6px 4px;">Often exceeds expectations</td></tr>
      <tr><td style="padding:6px 4px;">3</td><td style="padding:6px 4px;">Meets Expectations</td><td style="padding:6px 4px;">Reliable and consistent</td></tr>
      <tr><td style="padding:6px 4px;">2</td><td style="padding:6px 4px;">Needs Improvement</td><td style="padding:6px 4px;">Requires closer supervision</td></tr>
      <tr><td style="padding:6px 4px;">1</td><td style="padding:6px 4px;">Not Meeting Standards</td><td style="padding:6px 4px;">Unsafe or unprofessional conduct</td></tr>
    </tbody>
  </table>
</div>
""".strip()
    if not instructions_html:
        instructions_html = """
<h2 class="text-2xl font-bold text-gray-800">Before you begin</h2>
<p class="text-gray-700">Please read these instructions carefully before starting your self‑review:</p>
<ul class="list-disc pl-6 text-gray-700 space-y-1">
  <li>This review is about your performance and growth.</li>
  <li>Complete it in one sitting. Unsaved answers will be lost if you leave the page.</li>
  <li>Be honest and specific. Your input helps guide development and feedback.</li>
  <li>Use the rating scale on the right as a reference for each score.</li>
</ul>
""".strip()
    return templates.TemplateResponse("admin_ui.html", {
        "request": request,
        "rating_panel_html": rating_html,
        "instructions_html": instructions_html,
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
    })

@router.post("/admin/ui", response_class=HTMLResponse)
async def admin_ui_save(request: Request, rating_panel_html: str = Form(""), instructions_html: str = Form("")):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)
    path = os.path.join("app", "data", "ui_overrides.json")
    try:
        existing = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f) or {}
        existing["rating_panel_html"] = rating_panel_html
        existing["instructions_html"] = instructions_html
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"/admin/ui?error=Save%20failed:%20{str(e).replace(' ', '%20')}", status_code=302)
    # Clear cached overrides
    try:
        from app.utils import ui_overrides as ui_mod
        ui_mod._cache = None  # type: ignore
    except Exception:
        pass
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/admin/ui?message=Saved", status_code=302)

@router.post("/admin/ui/preview", response_class=HTMLResponse)
async def admin_ui_preview(request: Request, rating_panel_html: str = Form(""), instructions_html: str = Form("")):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)
    return templates.TemplateResponse("admin_ui_preview.html", {
        "request": request,
        "rating_panel_html": rating_panel_html,
        "instructions_html": instructions_html,
    })

@router.post("/admin/questions/preview", response_class=HTMLResponse)
async def admin_questions_preview(request: Request, role: str = Form("employee"), json_text: str = Form("", alias="json")):
    current_user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    try:
        payload = json.loads(json_text)
        if not isinstance(payload, list):
            raise ValueError("JSON must be a list of questions")
    except Exception as e:
        return HTMLResponse(f"Invalid JSON: {e}", status_code=400)

    return templates.TemplateResponse("admin_questions_preview.html", {
        "request": request,
        "role": role,
        "questions": payload,
    })