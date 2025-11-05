from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db import SessionLocal
from app.models import Employee  # ou Employee se for o modelo certo
import os
from app.utils.auth_utils import generate_magic_login_token, verify_magic_login_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/director-login", response_class=HTMLResponse)
async def show_director_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "director_only": True})


@router.post("/login")
async def login(
    request: Request,
    name: str = Form(...),
    birth_date: str = Form(None),
    password: str = Form(None),
    required_role: str = Form(None),
):
    db: Session = SessionLocal()
    try:
        user = db.query(Employee).filter(Employee.name == name).first()
        if not user:
            return templates.TemplateResponse("login.html", {"request": request, "error": "User not found."})

        if required_role and user.role != required_role:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Access restricted.", "director_only": required_role == "director"})

        if required_role == "director":
            if password != user.password:
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "error": "Invalid password.",
                        "director_only": True,
                    },
                )
        else:
            expected = user.birth_date.strftime("%Y-%m-%d")
            if birth_date != expected:
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "error": "Invalid birth date.",
                    },
                )

        request.session["user_id"] = str(user.id)
        request.session["role"] = user.role
        request.session["name"] = user.name

        return RedirectResponse("/home", status_code=302)


    finally:
        db.close()


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

@router.get("/usernames")
def get_usernames(role: str = None, exclude_directors: bool = False):
    db = SessionLocal()
    query = db.query(Employee.name)
    if role:
        query = query.filter(Employee.role == role)
    elif exclude_directors:
        query = query.filter(Employee.role != "director")
    names = query.all()
    db.close()
    return JSONResponse([name[0] for name in names])


@router.get("/magic-login")
async def magic_login(request: Request, token: str):
    data = verify_magic_login_token(token)
    if not data:
        return HTMLResponse("Invalid or expired link.", status_code=401)

    db: Session = SessionLocal()
    try:
        user = db.query(Employee).filter(Employee.id == data.get("user_id")).first()
        if not user:
            return HTMLResponse("User not found.", status_code=404)

        # Create session
        request.session["user_id"] = str(user.id)
        request.session["role"] = user.role
        request.session["name"] = user.name

        redirect_url = data.get("redirect") or "/home"
        return RedirectResponse(redirect_url, status_code=302)
    finally:
        db.close()


@router.get("/admin-login", response_class=HTMLResponse)
async def show_admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@router.post("/admin-login")
async def admin_login(request: Request, password: str = Form("")):
    expected = os.getenv("ADMIN_PASSWORD", "adminpass")
    if password != expected:
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "Invalid password."},
            status_code=401,
        )
    request.session["is_admin"] = True
    return RedirectResponse("/admin", status_code=302)
