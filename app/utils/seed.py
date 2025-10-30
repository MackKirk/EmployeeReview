import os
import csv
from datetime import date, datetime
from app.models import Employee


def make_email_from_name(name: str) -> str:
    base = ''.join(c.lower() if c.isalnum() else '.' for c in name).strip('.')
    while '..' in base:
        base = base.replace('..', '.')
    return f"{base}@example.com"


def _parse_birthdate(value: str) -> date:
    v = (value or "").strip()
    if not v:
        return date(2000, 1, 1)
    # Try ISO first (yyyy-mm-dd)
    try:
        return date.fromisoformat(v)
    except Exception:
        pass
    # Try mm/dd/yyyy
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except Exception:
            continue
    return date(2000, 1, 1)


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
        # 4th column is supervisor name (by the CSV header it is SupervisorName)
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
        # Last column (Role) indicates which form they respond to: employee/supervisor/administration/director
        role = (r.get("role") or "").lower().strip()
        if role == "manager":
            role = "administration"
        if not role:
            if 'director' in (job_title.lower() + ' ' + dept.lower()):
                role = 'director'
            elif name in supervisor_names:
                role = 'supervisor'
            else:
                role = 'employee'

        birth_date_str = r.get("birth_date") or r.get("birthdate")
        bd = _parse_birthdate(birth_date_str)

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
        # Ensure supervisors (including managers) are flagged
        if sup_name:
            sup_emp = db.query(Employee).filter(Employee.name == sup_name).first()
            if sup_emp and not sup_emp.is_supervisor:
                sup_emp.is_supervisor = True
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


