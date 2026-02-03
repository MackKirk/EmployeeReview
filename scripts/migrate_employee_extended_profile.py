"""Add extended profile columns to employees table."""
from app.db import engine
from sqlalchemy import text

COLUMNS = [
    ("department", "VARCHAR"),
    ("position", "VARCHAR"),
    ("years_months_with_mk", "VARCHAR"),
    ("pay_hr_last_3_years", "TEXT"),
    ("loan_amount", "VARCHAR"),
    ("lmia", "VARCHAR"),
    ("company_phone", "VARCHAR"),
    ("company_laptop_ipad", "VARCHAR"),
    ("drive_company_vehicle", "VARCHAR"),
    ("company_gas_card", "VARCHAR"),
    ("skills_trade_completed", "VARCHAR"),
    ("safety_infraction_description", "TEXT"),
]

with engine.connect() as conn:
    for col_name, col_type in COLUMNS:
        conn.execute(text(
            f"ALTER TABLE employees ADD COLUMN IF NOT EXISTS {col_name} {col_type} NULL"
        ))
    conn.commit()

print("✅ Added extended profile columns to employees (if not already present).")
