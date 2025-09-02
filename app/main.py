from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from starlette.middleware.sessions import SessionMiddleware
import os
from app.routes import auth, employee, supervisor, director, home
from app.db import engine, SessionLocal
from app.models import Base, Employee
import csv
from datetime import date

app = FastAPI()
SESSION_SECRET = os.getenv("SESSION_SECRET", "changeme")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Garante que a pasta está montada corretamente
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(supervisor.router)
app.include_router(director.router)
app.include_router(home.router)


@app.on_event("startup")
def create_tables_on_startup():
    Base.metadata.create_all(bind=engine)

    # Seed from CSV if there are no employees yet
    db = SessionLocal()
    try:
        count = db.query(Employee).count()
        if count == 0:
            csv_paths = [
                os.path.join("app", "data", "Employees.csv"),
                os.path.join("app", "data", "general_bamboohr_org_chart.csv"),
            ]
            csv_path = next((p for p in csv_paths if os.path.exists(p)), None)
            if csv_path:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    created = 0
                    for raw in reader:
                        # Normalize keys
                        row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
                        name = row.get("name")
                        if not name:
                            continue
                        email = row.get("email") or None
                        supervisor_email = (
                            row.get("supervisor_email") or row.get("supervisor") or row.get("manager_email") or None
                        )
                        role = (row.get("role") or "employee").lower()
                        if role not in ("employee", "supervisor", "director"):
                            role = "employee"
                        birth_date_str = row.get("birth_date")
                        try:
                            bd = date.fromisoformat(birth_date_str) if birth_date_str else date(2000, 1, 1)
                        except Exception:
                            bd = date(2000, 1, 1)

                        exists = db.query(Employee).filter(Employee.name == name).first()
                        if exists:
                            continue

                        # Directors use a common simple password for now (plaintext expected by login)
                        password = "directorpass" if role == "director" else None

                        emp = Employee(
                            name=name,
                            email=email or None,
                            birth_date=bd,
                            supervisor_email=supervisor_email or None,
                            role=role,
                            password=password,
                        )
                        db.add(emp)
                        created += 1
                    if created:
                        db.commit()
    finally:
        db.close()
