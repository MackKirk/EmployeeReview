import os
import csv
from datetime import date
from app.models import Employee


def make_email_from_name(name: str) -> str:
    base = ''.join(c.lower() if c.isalnum() else '.' for c in name).strip('.')
    while '..' in base:
        base = base.replace('..', '.')
    return f"{base}@example.com"


def seed_employees_from_csv(db):
    csv_paths = [
        os.path.join("app", "data", "Employees.csv"),
        os.path.join("app", "data", "general_bamboohr_org_chart.csv"),
    ]
    csv_path = next((p for p in csv_paths if os.path.exists(p)), None)
    if not csv_path:
        return {"ok": False, "error": "CSV not found", "path": None}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    # Normalize rows
    norm_rows = []
    for raw in reader:
        row = {}
        for k, v in raw.items():
            key = (k or "").strip().lower().lstrip("\ufeff")
            row[key] = (v or "").strip()
        if row.get("name"):
            norm_rows.append(row)

    supervisor_names = set()
    for r in norm_rows:
        sup_name = r.get("supervisorname") or r.get("supervisor") or r.get("manager")
        if sup_name:
            supervisor_names.add(sup_name.strip())

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
        role = (r.get("role") or "").lower().strip()
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

    return {
        "ok": True,
        "path": csv_path,
        "rows": len(norm_rows),
        "created": created,
        "updated": updated,
    }


