"""Remove outer try in admin_update_employee (lines between Invalid role and create-employee router)."""
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "app" / "routes" / "director.py"
lines = path.read_text(encoding="utf-8").splitlines(True)

start = None
end = None
for i, line in enumerate(lines):
    if (
        line == "    try:\n"
        and i > 0
        and "Invalid role" in lines[i - 1]
        and i + 1 < len(lines)
        and "emp = db.query(Employee).filter_by(id=employee_id)" in lines[i + 1]
    ):
        start = i
        continue
    if start is not None and line.startswith('@router.post("/admin/create-employee")'):
        end = i
        break

if start is None or end is None:
    raise SystemExit(f"markers not found start={start} end={end}")

new_lines = lines[:start]
for line in lines[start + 1 : end]:
    if line.startswith("        "):
        new_lines.append(line[4:])
    else:
        new_lines.append(line)
new_lines.extend(lines[end:])
path.write_text("".join(new_lines), encoding="utf-8")
print("dedented admin_update_employee", start, end)
