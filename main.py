
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = "data"

QUESTIONS = [
    "Qualidade do trabalho",
    "Pontualidade",
    "Assiduidade",
    "Conquistas no último ano",
    "O que poderia melhorar",
    "O que a empresa poderia fazer para ajudar",
    "Metas para o próximo período"
]

@app.get("/review/{role}/{name}", response_class=HTMLResponse)
async def get_form(request: Request, role: str, name: str):
    return templates.TemplateResponse("form.html", {"request": request, "role": role, "name": name, "questions": QUESTIONS})

@app.post("/submit/{role}/{name}")
async def submit_form(role: str, name: str, request: Request):
    form_data = await request.form()
    entry = {q: form_data.get(q) for q in QUESTIONS}

    filepath = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[role] = entry

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return RedirectResponse(url=f"/compare/{name}", status_code=303)

@app.get("/compare/{name}", response_class=HTMLResponse)
async def compare(request: Request, name: str):
    filepath = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return HTMLResponse(content="Review não encontrado.", status_code=404)

    with open(filepath, "r") as f:
        data = json.load(f)

    return templates.TemplateResponse("compare.html", {"request": request, "name": name, "data": data, "questions": QUESTIONS})
