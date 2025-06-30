from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db import SessionLocal
from app.models import Employee  # ou Employee se for o modelo certo

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, name: str = Form(...), birth_date: str = Form(...)):
    db: Session = SessionLocal()
    try:
        user = db.query(Employee).filter(Employee.name == name).first()
        if not user:
            return templates.TemplateResponse("login.html", {"request": request, "error": "User not found."})

        expected = user.birth_date.strftime("%Y-%m-%d")
        if birth_date != expected:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid birth date."})

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
def get_usernames():
    db = SessionLocal()
    names = db.query(Employee.name).all()
    db.close()
    return JSONResponse([name[0] for name in names])