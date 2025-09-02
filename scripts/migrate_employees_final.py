import csv
import uuid
from datetime import datetime, date
from app.db import SessionLocal
from app.models import Employee
import hashlib

csv_file = "C:/_WorkDev/EmployeeReview/app/data/general_bamboohr_org_chart.csv"

# Etapa 1 – Carregar dados do CSV e gerar UUIDs
employees = []
id_map = {}  # PersonID → UUID
raw_data = []

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not row['Name']:
            continue
        person_id = row['PersonID']
        emp_uuid = str(uuid.uuid4())
        id_map[person_id] = emp_uuid
        raw_data.append(row)
        employees.append({
            "id": emp_uuid,
            "person_id": person_id,
            "name": row['Name'].strip(),
            "email": row['Email'].strip() if row['Email'] else None,
            "supervisor_id": row['SupervisorID'],
        })

# Etapa 2 – Atribuir supervisor_email
personid_to_email = {
    e['person_id']: e['email']
    for e in employees if e['email']
}

for emp in employees:
    supervisor_person_id = emp['supervisor_id']
    emp['supervisor_email'] = personid_to_email.get(supervisor_person_id)

# Etapa 3 – Determinar quem é supervisor
supervised_ids = set(row['SupervisorID'] for row in raw_data if row['SupervisorID'])
supervised_ids = set(str(int(float(i))) for i in supervised_ids if i)  # normaliza

for emp in employees:
    if emp['person_id'] in supervised_ids:
        emp['role'] = 'supervisor'
    else:
        emp['role'] = 'employee'

# Etapa 4 – Inserir no banco
db = SessionLocal()
created = 0

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

for emp in employees:
    exists = db.query(Employee).filter(Employee.name == emp['name']).first()
    if exists:
        continue

    new_emp = Employee(
        id=emp['id'],
        name=emp['name'],
        email=emp['email'] or f"fake_{uuid.uuid4()}@example.com",
        birth_date=date(2000, 1, 1),
        supervisor_email=emp['supervisor_email'],
        role=emp['role'],
        password=hash_password("directorpass") if emp['role'] == 'director' else None
    )
    db.add(new_emp)
    created += 1

db.commit()
db.close()

print(f"✅ Importação finalizada. Funcionários criados: {created}")
