"""Remove orphan outer try (formerly wrapping finally db.close) in director routes."""
from pathlib import Path
import re

path = Path(__file__).resolve().parent.parent / "app" / "routes" / "director.py"
text = path.read_text(encoding="utf-8")

# admin_update_employee: unwrap inner try block (lines with 8-space base -> 4-space)
pat = r'''(    if role_val and role_val not in allowed:
        return HTMLResponse\("Invalid role", status_code=400\)
)    try:
((?:        .*\n)+?)(    @router\.post\("/admin/create-employee"\))'''

def repl(m):
    body = m.group(2)
    # Dedented: remove 4 spaces from each line of body
    lines = body.splitlines(True)
    dedented = []
    for line in lines:
        if line.startswith("        "):
            dedented.append(line[4:])
        else:
            dedented.append(line)
    return m.group(1) + "".join(dedented) + m.group(3)

text2, n = re.subn(pat, repl, text, count=1, flags=re.MULTILINE)
if n != 1:
    raise SystemExit(f"admin_update_employee pattern n={n}")

# admin_create_employee: unwrap try/finally
pat2 = r'''(    bd = _parse_birthdate\(birth_date or ""\)
)    try:
((?:        .*\n)+?)(    @router\.post\("/admin/employee/\{employee_id\}/deactivate"\))'''

def repl2(m):
    body = m.group(2)
    lines = body.splitlines(True)
    dedented = []
    for line in lines:
        if line.startswith("        "):
            dedented.append(line[4:])
        else:
            dedented.append(line)
    return m.group(1) + "".join(dedented) + m.group(3)

text3, n2 = re.subn(pat2, repl2, text2, count=1, flags=re.MULTILINE)
if n2 != 1:
    raise SystemExit(f"admin_create_employee pattern n={n2}")

path.write_text(text3, encoding="utf-8")
print("ok", n, n2)
