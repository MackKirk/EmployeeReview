
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = "data"
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")

os.makedirs(DATA_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/select/employee", response_class=HTMLResponse)
async def select_employee(request: Request):
    with open(EMPLOYEES_FILE) as f:
        employees = json.load(f)
    return templates.TemplateResponse("select_employee.html", {"request": request, "employees": employees})

@app.get("/select/supervisor", response_class=HTMLResponse)
async def select_supervisor(request: Request):
    with open(EMPLOYEES_FILE) as f:
        employees = json.load(f)
    return templates.TemplateResponse("select_supervisor.html", {"request": request, "employees": employees})

@app.get("/review/{name}/employee", response_class=HTMLResponse)
async def review_employee_form(request: Request, name: str):
    review_path = os.path.join(DATA_DIR, f"{name}_employee.json")
    existing_data = {}
    if os.path.exists(review_path):
        with open(review_path) as f:
            existing_data = json.load(f)
    return templates.TemplateResponse("review_employee.html", {"request": request, "name": name, "data": existing_data})

@app.post("/review/{name}/employee")
async def submit_employee_review(request: Request, name: str, responses: str = Form(...)):
    review_path = os.path.join(DATA_DIR, f"{name}_employee.json")
    with open(review_path, "w") as f:
        json.dump(json.loads(responses), f)
    return RedirectResponse(url="/select/employee", status_code=303)

@app.get("/review/{name}/supervisor", response_class=HTMLResponse)
async def review_supervisor_form(request: Request, name: str):
    review_path = os.path.join(DATA_DIR, f"{name}_supervisor.json")
    existing_data = {}
    if os.path.exists(review_path):
        with open(review_path) as f:
            existing_data = json.load(f)
    return templates.TemplateResponse("review_supervisor.html", {"request": request, "name": name, "data": existing_data})

@app.post("/review/{name}/supervisor")
async def submit_supervisor_review(request: Request, name: str, responses: str = Form(...)):
    review_path = os.path.join(DATA_DIR, f"{name}_supervisor.json")
    with open(review_path, "w") as f:
        json.dump(json.loads(responses), f)
    return RedirectResponse(url="/select/supervisor", status_code=303)
