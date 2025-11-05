from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review, EmailEvent
from app.utils.auth_utils import get_current_user
from app.utils.auth_utils import generate_magic_login_token
from app.utils.email import send_email, build_review_invite_email
from app.utils.seed import seed_employees_from_csv
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return HTMLResponse("Access denied", status_code=403)

    db: Session = SessionLocal()

    # Review of the logged in user
    review = db.query(Review).filter_by(employee_id=user.id).first()
    filled = review and review.employee_answers
    employee_card_title = "View my answers" if filled else "Fill self review"

    # Pending reviews for supervisor
    supervisor_pending = 0
    if user.role == "supervisor" or user.is_supervisor:
        subordinates = db.query(Employee).filter_by(supervisor_email=user.name).all()
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
        "show_supervisor_card": user.role == "supervisor" or user.is_supervisor,
        "show_director_card": user.role == "director",
        "supervisor_pending": supervisor_pending,
        "director_pending": director_pending,
    })


@router.post("/admin/seed")
async def admin_seed(request: Request):
    user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((user and user.role == "director") or is_admin):
        return HTMLResponse("Access denied", status_code=403)
    db: Session = SessionLocal()
    try:
        result = seed_employees_from_csv(db)
        if not result.get("ok"):
            return HTMLResponse(f"Seed failed: {result.get('error')}", status_code=500)
        return HTMLResponse(
            f"Seeded from {result['path']}. Rows: {result['rows']}, created: {result['created']}, supervisor links: {result['updated']}",
            status_code=200,
        )
    finally:
        db.close()


@router.get("/setup/seed", response_class=HTMLResponse)
async def seed_setup_form(request: Request):
    return templates.TemplateResponse("seed_setup.html", {"request": request})


@router.post("/setup/seed", response_class=HTMLResponse)
async def seed_setup_submit(request: Request, password: str = Form("")):
    expected = os.getenv("SEED_PASSWORD", "seedme")
    if password != expected:
        return templates.TemplateResponse(
            "seed_setup.html",
            {"request": request, "error": "Invalid password."},
            status_code=401,
        )
    db: Session = SessionLocal()
    try:
        result = seed_employees_from_csv(db)
        if not result.get("ok"):
            return templates.TemplateResponse(
                "seed_setup.html",
                {"request": request, "error": f"Seed failed: {result.get('error')}"},
                status_code=500,
            )
        return templates.TemplateResponse(
            "seed_setup.html",
            {
                "request": request,
                "success": f"Seeded from {result['path']}. Rows: {result['rows']}, created: {result['created']}, supervisor links: {result['updated']}"
            },
            status_code=200,
        )
    finally:
        db.close()


@router.post("/admin/send-review-link/{employee_id}")
async def admin_send_review_link(request: Request, employee_id: str):
    user = get_current_user(request)
    is_admin = bool(request.session.get("is_admin"))
    if not ((user and user.role == "director") or is_admin):
        return HTMLResponse("Access denied", status_code=403)

    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    db: Session = SessionLocal()
    try:
        emp = db.query(Employee).filter_by(id=employee_id).first()
        if not emp:
            return HTMLResponse("Employee not found", status_code=404)
        if not emp.email:
            return HTMLResponse("Employee has no email", status_code=400)

        token = generate_magic_login_token(str(emp.id), redirect_url=f"/employee/{emp.id}", role=emp.role)
        link = f"{base_url}/magic-login?token={token}"
        subject = "Employee Review Notice"
        html = build_review_invite_email(emp.name, link, base_url)
        ok = send_email(emp.email, subject, html)
        if not ok:
            return HTMLResponse("Failed to send email (SMTP not configured?)", status_code=500)
        try:
            evt = EmailEvent(employee_id=emp.id, event_type="sent")
            db.add(evt)
            db.commit()
        except Exception:
            db.rollback()
        # Redirect back to admin page with a flash-like message via querystring
        return RedirectResponse("/admin", status_code=302)
    finally:
        db.close()


@router.post("/admin/send-review-links")
async def admin_send_review_links(request: Request, role: str = Form(None)):
    user = get_current_user(request)
    if not user or user.role != "director":
        return HTMLResponse("Access denied", status_code=403)

    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    db: Session = SessionLocal()
    try:
        q = db.query(Employee)
        if role:
            q = q.filter(Employee.role == role)
        employees = q.all()
        sent = 0
        skipped = 0
        for emp in employees:
            if not emp.email:
                skipped += 1
                continue
            token = generate_magic_login_token(str(emp.id), redirect_url=f"/employee/{emp.id}", role=emp.role)
            link = f"{base_url}/magic-login?token={token}"
            subject = "Employee Review Notice"
            html = build_review_invite_email(emp.name, link, base_url)
            ok = send_email(emp.email, subject, html)
            if ok:
                sent += 1
                try:
                    evt = EmailEvent(employee_id=emp.id, event_type="sent")
                    db.add(evt)
                    db.commit()
                except Exception:
                    db.rollback()
            else:
                skipped += 1
        return HTMLResponse(f"Emails sent: {sent}. Skipped: {skipped}. Role filter: {role or 'all'}.", status_code=200)
    finally:
        db.close()
