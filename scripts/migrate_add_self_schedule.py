from app.db import engine
from sqlalchemy import text

# Postgres-safe add column if not exists
sql = text("""
ALTER TABLE reviews
ADD COLUMN IF NOT EXISTS employee_scheduled_at TIMESTAMP NULL;
""")

with engine.connect() as conn:
    conn.execute(sql)
    conn.commit()

print("✅ Added employee_scheduled_at to reviews (if not already present).")


