r"""
Import extended employee info from CSV.
Matches rows by Employee Name; only updates employees that exist in the DB.
Fills/overwrites fields with values from the CSV for matched employees only.

Usage:
  python -m scripts.import_employee_info_csv "<path-to-csv>"
"""
import csv
import os
import re
import sys

# Add project root to path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
# Optional: load .env from project root so DATABASE_URL is set
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

from app.db import SessionLocal
from app.models import Employee
from sqlalchemy import text


def normalize_name(s):
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.split()).strip()


def is_section_header(name):
    """Rows that are department/section headers, not employee names."""
    if not name:
        return True
    n = name.strip().upper()
    return n in (
        "OFFICE", "STEEP", "C & W", "REPAIRS", "FLAT", "METAL", "CLADDING",
        "SHOP", "OPERATORS", "C & W", "REPAIRS ", "FLAT ", "METAL ", "CLADDING ",
        "SHOP ", "OPERATORS ",
    )


def normalize_lmia(val):
    if not val or not isinstance(val, str):
        return None
    v = val.strip().upper()
    if "SKILLED" in v or "SKILL" in v:
        return "SKILLED"
    if "UNSKILLED" in val.upper():
        return "UNSKILLED"
    return val.strip() or None


def ensure_columns(session):
    cols = [
        ("department", "VARCHAR"), ("position", "VARCHAR"), ("years_months_with_mk", "VARCHAR"),
        ("pay_hr_last_3_years", "TEXT"), ("loan_amount", "VARCHAR"), ("lmia", "VARCHAR"),
        ("company_phone", "VARCHAR"), ("company_laptop_ipad", "VARCHAR"),
        ("drive_company_vehicle", "VARCHAR"), ("company_gas_card", "VARCHAR"),
        ("skills_trade_completed", "VARCHAR"), ("safety_infraction_description", "TEXT"),
    ]
    for col, typ in cols:
        try:
            ex = session.execute(
                text("SELECT 1 FROM information_schema.columns WHERE table_name='employees' AND column_name=:c"),
                {"c": col},
            ).first()
            if not ex:
                session.execute(text(f"ALTER TABLE employees ADD COLUMN IF NOT EXISTS {col} {typ} NULL"))
                session.commit()
        except Exception:
            session.rollback()


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_employee_info_csv <path-to-csv>")
        sys.exit(1)
    csv_path = sys.argv[1]
    if not os.path.isfile(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)

    db = SessionLocal()
    try:
        ensure_columns(db)
        employees = db.query(Employee).all()
        name_to_employee = {normalize_name(e.name): e for e in employees}

        def find_employee(csv_name):
            n = normalize_name(csv_name)
            if not n:
                return None
            if n in name_to_employee:
                return name_to_employee[n]
            for db_name, emp in name_to_employee.items():
                if db_name.lower() == n.lower():
                    return emp
            return None

        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            # Normalize header: strip and collapse newlines
            header = [normalize_name(h).replace("\n", " ").strip() for h in header]
            col_count = len(header)
            name_idx = None
            for i, h in enumerate(header):
                if "employee name" in (h or "").lower():
                    name_idx = i
                    break
            if name_idx is None:
                name_idx = 1
            dept_idx = 0 if "department" in (header[0] or "").lower() else None
            pos_idx = next((i for i, h in enumerate(header) if h and "position" in h.lower() and "years" not in h.lower()), 2)
            years_idx = next((i for i, h in enumerate(header) if "years" in (h or "").lower() and "mk" in (h or "").lower()), 3)
            pay_idx = next((i for i, h in enumerate(header) if "pay" in (h or "").lower()), 5)
            loan_idx = next((i for i, h in enumerate(header) if "loan" in (h or "").lower()), 6)
            lmia_idx = next((i for i, h in enumerate(header) if "lmia" in (h or "").lower()), 7)
            phone_idx = next((i for i, h in enumerate(header) if "company phone" in (h or "").lower() or "allowance" in (h or "").lower()), 8)
            laptop_idx = next((i for i, h in enumerate(header) if "laptop" in (h or "").lower() or "ipad" in (h or "").lower()), 9)
            vehicle_idx = next((i for i, h in enumerate(header) if "drive" in (h or "").lower() and "vehicle" in (h or "").lower()), 10)
            gas_idx = next((i for i, h in enumerate(header) if "gas card" in (h or "").lower()), 11)
            skills_idx = next((i for i, h in enumerate(header) if "skills trade" in (h or "").lower()), 12)
            safety_yn_idx = next((i for i, h in enumerate(header) if "safety infraction" in (h or "").lower() and "link" not in (h or "").lower()), 13)
            safety_link_idx = next((i for i, h in enumerate(header) if "safety" in (h or "").lower() and "link" in (h or "").lower()), 14)

            current_department = None
            updated = 0
            not_found = []
            for row in reader:
                if len(row) <= name_idx:
                    continue
                name = normalize_name(row[name_idx])
                if not name:
                    continue
                if is_section_header(name):
                    if dept_idx is not None and len(row) > dept_idx and normalize_name(row[dept_idx]):
                        current_department = normalize_name(row[dept_idx])
                    continue
                if dept_idx is not None and len(row) > dept_idx and normalize_name(row[dept_idx]):
                    current_department = normalize_name(row[dept_idx])

                emp = find_employee(name)
                if not emp:
                    not_found.append(name)
                    continue

                def cell(i):
                    if i is None or i >= len(row):
                        return ""
                    return (row[i] or "").strip()

                changed = False
                if current_department:
                    emp.department = current_department
                    changed = True
                v = cell(pos_idx)
                if v:
                    emp.position = v
                    changed = True
                v = cell(years_idx)
                if v:
                    emp.years_months_with_mk = v
                    changed = True
                v = cell(pay_idx)
                if v:
                    emp.pay_hr_last_3_years = v
                    changed = True
                v = cell(loan_idx)
                if v:
                    emp.loan_amount = v
                    changed = True
                v = cell(lmia_idx)
                if v:
                    lm = normalize_lmia(v)
                    if lm:
                        emp.lmia = lm
                        changed = True
                v = cell(phone_idx)
                if v:
                    emp.company_phone = v
                    changed = True
                v = cell(laptop_idx)
                if v:
                    emp.company_laptop_ipad = v
                    changed = True
                v = cell(vehicle_idx)
                if v:
                    emp.drive_company_vehicle = v
                    changed = True
                v = cell(gas_idx)
                if v:
                    emp.company_gas_card = v
                    changed = True
                v = cell(skills_idx)
                if v:
                    emp.skills_trade_completed = v
                    changed = True
                v = cell(safety_link_idx)
                if v:
                    emp.safety_infraction_description = v
                    changed = True

                if changed:
                    updated += 1

            db.commit()
            print(f"Updated {updated} employee(s).")
            if not_found:
                print(f"Names in CSV not found in DB ({len(not_found)}):")
                for n in sorted(set(not_found))[:50]:
                    print(f"  - {n}")
                if len(set(not_found)) > 50:
                    print(f"  ... and {len(set(not_found)) - 50} more")
    finally:
        db.close()


if __name__ == "__main__":
    main()
