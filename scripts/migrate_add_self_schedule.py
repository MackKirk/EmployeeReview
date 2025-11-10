from app.db import engine

# Postgres-safe add column if not exists
sql = """
ALTER TABLE reviews
ADD COLUMN IF NOT EXISTS employee_scheduled_at TIMESTAMP NULL;
"""

with engine.connect() as conn:
    conn.execute(sql)  # type: ignore
    conn.commit()

print("✅ Added employee_scheduled_at to reviews (if not already present).")


