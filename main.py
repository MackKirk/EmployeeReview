from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import json

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "changeme"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = "data"
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")
PASSWORD = os.getenv("SUPERVISOR_PASSWORD", "supersecret")

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
    if role not in {"employee", "supervisor"}:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Invalid role."},
        )
    if role == "supervisor" and not request.session.get("supervisor_auth"):
        return templates.TemplateResponse(
            "password.html",
            {"request": request, "next": f"/select/{role}", "error": None},
        )
    employees = load_employees()
    if employees is None:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Unable to load employees."},
        )
    return templates.TemplateResponse(
        "select.html", {"request": request, "role": role, "names": employees}
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
            {"request": request, "next": f"/review/{role}/{name}", "error": None},
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
async def submit_review(request: Request, role: str, name: str):
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
    review_path = os.path.join(DATA_DIR, f"{name}_{role}.json")
    if os.path.exists(review_path):
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Review already submitted."},
        )
    form_data = await request.form()
    entry = {q: form_data.get(q, "") for q in QUESTIONS}
    try:
        with open(review_path, "w") as f:
            json.dump(entry, f, indent=2)
        os.chmod(review_path, 0o600)
    except Exception:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "message": "Could not save review."},
        )
    redirect = "/select/employee" if role == "employee" else "/select/supervisor"
    return RedirectResponse(url=redirect, status_code=303)


@app.post("/login")
async def login(request: Request, password: str = Form(...), next: str = Form(...)):
    if password == PASSWORD:
        request.session["supervisor_auth"] = True
        return RedirectResponse(url=next, status_code=303)
    return templates.TemplateResponse(
        "password.html",
        {"request": request, "next": next, "error": "Incorrect password"},
    )
