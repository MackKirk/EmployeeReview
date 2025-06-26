from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import json

from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import Base, Review

from fastapi import Depends

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "changeme"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = "data"
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")
PASSWORD = os.getenv("SUPERVISOR_PASSWORD", "supersecret")
DIRECTOR_PASSWORD = os.getenv("DIRECTOR_PASSWORD", "directorpass")

QUESTIONS = [
    "Work quality",
    "Punctuality",
    "Attendance",
    "Achievements in the last year",
    "Areas for improvement",
    "How the company or supervisor can support you",
    "Professional goals for the next period",
]

os.makedirs(DATA_DIR, exist_ok=True)


def load_employees():
    try:
        with open(EMPLOYEES_FILE) as f:
            return json.load(f)
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/select/{role}", response_class=HTMLResponse)
async def select_role(request: Request, role: str):
    if role not in {"employee", "supervisor", "director"}:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Invalid role."},
        )
    if role == "supervisor" and not request.session.get("supervisor_auth"):
        return templates.TemplateResponse(
            "password.html",
            {"request": request, "next": f"/select/{role}", "role": role, "error": None},
        )
    if role == "director" and not request.session.get("director_auth"):
        return templates.TemplateResponse(
            "password.html",
            {"request": request, "next": f"/select/{role}", "role": role, "error": None},
        )

    employees = load_employees()
    if employees is None:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Unable to load employees."},
        )

    statuses = {}
    for n in employees:
        statuses[n] = {
            "employee": os.path.exists(os.path.join(DATA_DIR, f"{n}_employee.json")),
            "supervisor": os.path.exists(os.path.join(DATA_DIR, f"{n}_supervisor.json")),
            "director": os.path.exists(os.path.join(DATA_DIR, f"{n}_director.json")),
        }
    return templates.TemplateResponse(
        "select.html", {"request": request, "role": role, "names": employees, "statuses": statuses}
    )


@app.get("/review/{role}/{name}", response_class=HTMLResponse)
async def get_review(request: Request, role: str, name: str):
    if role not in {"employee", "supervisor"}:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Invalid role."},
        )
    employees = load_employees()
    if employees is None or name not in employees:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Employee not found."},
        )
    if role == "supervisor" and not request.session.get("supervisor_auth"):
        return templates.TemplateResponse(
            "password.html",
            {"request": request, "next": f"/review/{role}/{name}", "role": role, "error": None},
        )
    review_path = os.path.join(DATA_DIR, f"{name}_{role}.json")
    if os.path.exists(review_path):
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Review already submitted."},
        )
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "role": role,
            "name": name,
            "questions": QUESTIONS,
            "saved_data": {},
        },
    )


@app.post("/review/{role}/{name}")
async def submit_review(request: Request, role: str, name: str, db: Session = Depends(get_db)):
    if role not in {"employee", "supervisor"}:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Invalid role."},
        )
    employees = load_employees()
    if employees is None or name not in employees:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Employee not found."},
        )

    # Verifica se o funcionário já tem review salvo
    existing = db.query(Review).filter_by(employee_name=name, role=role).first()
    if existing:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Review already submitted."},
        )

    # Lê as respostas do formulário
    form_data = await request.form()
    for q in QUESTIONS:
        answer = form_data.get(q, "")
        if answer:
            review = Review(employee_name=name, role=role, question=q, answer=answer)
            db.add(review)
    db.commit()

    redirect = "/select/employee" if role == "employee" else "/select/supervisor"
    return RedirectResponse(url=redirect, status_code=303)


@app.post("/login")
async def login(
    request: Request,
    password: str = Form(...),
    next: str = Form(...),
    role: str = Form(...),
):
    expected = PASSWORD if role == "supervisor" else DIRECTOR_PASSWORD
    if password == expected:
        key = "supervisor_auth" if role == "supervisor" else "director_auth"
        request.session[key] = True
        return RedirectResponse(url=next, status_code=303)
    return templates.TemplateResponse(
        "password.html",
        {"request": request, "next": next, "role": role, "error": "Incorrect password"},
    )


@app.get("/compare/{name}", response_class=HTMLResponse)
async def compare_reviews(request: Request, name: str):
    if not request.session.get("director_auth"):
        return templates.TemplateResponse(
            "password.html",
            {"request": request, "next": f"/compare/{name}", "role": "director", "error": None},
        )
    employees = load_employees()
    if employees is None or name not in employees:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Employee not found."},
        )
    data = {}
    employee_file = os.path.join(DATA_DIR, f"{name}_employee.json")
    supervisor_file = os.path.join(DATA_DIR, f"{name}_supervisor.json")
    if os.path.exists(employee_file):
        with open(employee_file) as f:
            data["funcionario"] = json.load(f)
    if os.path.exists(supervisor_file):
        with open(supervisor_file) as f:
            data["supervisor"] = json.load(f)
    director_file = os.path.join(DATA_DIR, f"{name}_director.json")
    if not os.path.exists(director_file):
        try:
            with open(director_file, "w") as f:
                json.dump({"viewed": True}, f)
            os.chmod(director_file, 0o600)
        except Exception:
            pass
    return templates.TemplateResponse(
        "compare.html",
        {
            "request": request,
            "name": name.replace("_", " ").title(),
            "questions": QUESTIONS,
            "data": data,
        },
    )
