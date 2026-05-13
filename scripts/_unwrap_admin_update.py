"""Unwrap outer try in admin_update_employee and add db Depends."""
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "app" / "routes" / "director.py"
lines = path.read_text(encoding="utf-8").splitlines(True)

sig_old = "    safety_infraction_description: str = Form(None),\n):\n"
sig_new = (
    "    safety_infraction_description: str = Form(None),\n"
    "    db: Session = Depends(get_db),\n):\n"
)
text = path.read_text(encoding="utf-8")
if sig_old not in text:
    raise SystemExit("signature block not found")
text = text.replace(sig_old, sig_new, 1)

lines = text.splitlines(True)
out = []
i = 0
while i < len(lines):
    line = lines[i]
    # Remove single outer try after "Invalid role" check in admin_update
    if (
        line == "    try:\n"
        and i > 0
        and "Invalid role" in lines[i - 1]
        and i + 1 < len(lines)
        and lines[i + 1].startswith("        emp = db.query(Employee)")
    ):
        i += 1
        continue
    # Dedented body lines that were inside that try (8 spaces base -> 4)
    if i > 598 and i < 720:  # fragile line numbers - skip
        pass
    out.append(line)
    i += 1

path.write_text("".join(out), encoding="utf-8")
print("phase1 ok")
