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
                print(f"[startup] Seeding employees from: {csv_path}")
                with open(csv_path, newline="", encoding="utf-8") as f:
                    reader = list(csv.DictReader(f))

                # Normalize rows (strip BOM on first header if present)
                norm_rows = []
                for raw in reader:
                    row = {}
                    for k, v in raw.items():
                        key = (k or "").strip().lower().lstrip("\ufeff")
                        row[key] = (v or "").strip()
                    if row.get("name"):
                        norm_rows.append(row)
                print(f"[startup] CSV rows detected: {len(norm_rows)}")

                # Build set of supervisor names from SupervisorName column if present
                supervisor_names = set()
                for r in norm_rows:
                    sup_name = r.get("supervisorname") or r.get("supervisor") or r.get("manager")
                    if sup_name:
                        supervisor_names.add(sup_name.strip())

                def make_email_from_name(name: str) -> str:
                    base = ''.join(c.lower() if c.isalnum() else '.' for c in name).strip('.')
                    # collapse multiple dots
                    while '..' in base:
                        base = base.replace('..', '.')
                    return f"{base}@example.com"

                # First pass: create all employees with generated emails and roles
                name_to_email = {}
                created = 0
                for r in norm_rows:
                    name = r.get("name")
                    if not name:
                        continue
                    exists = db.query(Employee).filter(Employee.name == name).first()
                    if exists:
                        name_to_email[name] = exists.email
                        continue

                    email = r.get("email") or make_email_from_name(name)
                    job_title = r.get("job title") or r.get("job_title") or ""
                    dept = r.get("department") or ""
                    # Determine role
                    role = r.get("role") or ""
                    role = role.lower().strip()
                    if not role:
                        if 'director' in (job_title.lower() + ' ' + dept.lower()):
                            role = 'director'
                        elif name in supervisor_names:
                            role = 'supervisor'
                        else:
                            role = 'employee'

                    birth_date_str = r.get("birth_date") or r.get("birthdate")
                    try:
                        bd = date.fromisoformat(birth_date_str) if birth_date_str else date(2000, 1, 1)
                    except Exception:
                        bd = date(2000, 1, 1)

                    password = "directorpass" if role == "director" else None

                    emp = Employee(
                        name=name,
                        email=email,
                        birth_date=bd,
                        role=role,
                        password=password,
                    )
                    db.add(emp)
                    created += 1
                    name_to_email[name] = email

                if created:
                    db.commit()
                else:
                    print("[startup] No employees created (possibly already seeded).")
                print(f"[startup] Employees created in first pass: {created}")

                # Second pass: set supervisor_email by matching SupervisorName to generated emails
                updated = 0
                for r in norm_rows:
                    name = r.get("name")
                    sup_name = r.get("supervisorname") or r.get("supervisor") or r.get("manager")
                    if not name:
                        continue
                    emp = db.query(Employee).filter(Employee.name == name).first()
                    if not emp:
                        continue
                    sup_email = name_to_email.get(sup_name) if sup_name else None
                    if sup_email and emp.supervisor_email != sup_email:
                        emp.supervisor_email = sup_email
                        updated += 1

                if updated:
                    db.commit()
                else:
                    print("[startup] No supervisor links updated.")
                print(f"[startup] Employees updated with supervisors in second pass: {updated}")
            else:
                print("[startup] No CSV found at app/data/Employees.csv or app/data/general_bamboohr_org_chart.csv. Skipping seed.")
    finally:
        db.close()
