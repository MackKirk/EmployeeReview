
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = "data"

QUESTIONS = ['Work quality', 'Punctuality', 'Attendance', 'Achievements in the last year', 'Areas for improvement', 'How the company or supervisor can support you', 'Professional goals for the next period']

def save_partial(name: str, role: str, entry: dict):
    filepath = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
    else:
        data = {}

    if role not in data:
        data[role] = {}

    data[role].update(entry)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

@app.get("/review/{role}/{name}", response_class=HTMLResponse)
async def get_form(request: Request, role: str, name: str):
    saved_data = {}
    filepath = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            saved_data = json.load(f)
            saved_data = saved_data.get(role, {})
    return templates.TemplateResponse("form.html", {"request": request, "role": role, "name": name, "questions": QUESTIONS, "saved_data": saved_data})

@app.post("/submit/{role}/{name}")
async def submit_form(role: str, name: str, request: Request):
    form_data = await request.form()
    entry = {q: form_data.get(q) for q in QUESTIONS}
    save_partial(name, role, entry)
    return RedirectResponse(url=f"/compare/{name}", status_code=303)

@app.get("/compare/{name}", response_class=HTMLResponse)
async def compare(request: Request, name: str):
    filepath = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return HTMLResponse(content="Review not found.", status_code=404)
    with open(filepath, "r") as f:
        data = json.load(f)
    return templates.TemplateResponse("compare.html", {"request": request, "name": name, "data": data, "questions": QUESTIONS})


@app.get("/select/{role}", response_class=HTMLResponse)
async def list_names(request: Request, role: str):
    all_files = os.listdir(DATA_DIR)
    names = [f.replace(".json", "") for f in all_files if f.endswith(".json")]
    return templates.TemplateResponse("select.html", {"request": request, "role": role, "names": names})
