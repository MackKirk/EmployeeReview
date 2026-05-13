"""One-off: fix admin_page try/finally orphan in director.py after session migration."""
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "app" / "routes" / "director.py"
text = path.read_text(encoding="utf-8")
old = '''@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    current_user = get_current_user(request, db)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)
    try:
        _ensure_safety_ack_columns(db)
        _ensure_deleted_at_column(db)
        from sqlalchemy.orm import joinedload
        employees = db.query(Employee).filter(Employee.deleted_at.is_(None)).order_by(Employee.name).all()
        # Check if schedule column exists to avoid 500 before migration runs
        col_exists = False
        try:
            exists_sql = text("SELECT 1 FROM information_schema.columns WHERE table_name='reviews' AND column_name='employee_scheduled_at'")
            col_exists = db.execute(exists_sql).first() is not None
        except Exception:
            col_exists = False
        # Auto-migrate if missing
        if not col_exists:
            try:
                db.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS employee_scheduled_at TIMESTAMP NULL"))
                db.commit()
                col_exists = True
            except Exception:
                db.rollback()
        rows = []
        for emp in employees:
            r = db.query(Review).options(
                load_only(
                    Review.id,
                    Review.employee_id,
                    Review.supervisor_id,
                    Review.employee_answers,
                    Review.supervisor_answers,
                    Review.director_comments,
                    Review.status,
                    Review.created_at,
                    Review.updated_at,
                ),
                joinedload(Review.employee),
            ).filter_by(employee_id=emp.id).first()
            employee_done = bool(r and r.employee_answers)
            supervisor_done = bool(r and r.supervisor_answers)
            director_done = bool(r and r.director_comments)
            # Email tracking
            has_sent = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="sent").first() is not None
            has_clicked = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="clicked").first() is not None
            sched_display = None
            sched_value = ""
            if col_exists and r:
                try:
                    # Load schedule lazily via direct SQL to avoid selecting missing column elsewhere
                    srow = db.execute(
                        text("SELECT employee_scheduled_at FROM reviews WHERE id = CAST(:id AS uuid)"),
                        {"id": str(r.id)},
                    ).first()
                    if srow and srow[0]:
                        sched_display = srow[0].strftime("%Y-%m-%d %H:%M")
                        sched_value = srow[0].strftime("%Y-%m-%dT%H:%M")
                except Exception:
                    pass
            rows.append({
                "employee": emp,
                "employee_done": employee_done,
                "supervisor_done": supervisor_done,
                "director_done": director_done,
                "has_sent": has_sent,
                "has_clicked": has_clicked,
                "self_scheduled_at_display": sched_display,
                "self_scheduled_at_value": sched_value,
            })
        all_names = [e.name for e in employees]
        
        # Calculate pending counts
        employee_pending = 0
        supervisor_pending = 0
        director_pending = 0
        
        for emp in employees:
            r = db.query(Review).options(
                load_only(
                    Review.employee_id,
                    Review.employee_answers,
                    Review.supervisor_answers,
                    Review.director_comments,
                )
            ).filter_by(employee_id=emp.id).first()
            
            # Employee pending: no employee_answers
            if not r or not r.employee_answers:
                employee_pending += 1
            
            # Supervisor pending: has employee_answers but no supervisor_answers
            # Only count if employee has a supervisor assigned
            if r and r.employee_answers and not r.supervisor_answers and emp.supervisor_email:
                supervisor_pending += 1
            
            # Director pending: has employee_answers and supervisor_answers but no director_comments
            if r and r.employee_answers and r.supervisor_answers and not r.director_comments:
                director_pending += 1
    finally:
    return templates.TemplateResponse(request, "admin.html", {
        "rows": rows,
        "names": all_names,
        "allowed_roles": ["employee", "supervisor", "administration", "director"],
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
        "employee_pending": employee_pending,
        "supervisor_pending": supervisor_pending,
        "director_pending": director_pending,
    })'''

new = '''@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    is_admin = bool(request.session.get("is_admin"))
    if not ((current_user and current_user.role == "director") or is_admin):
        return HTMLResponse("Access restricted", status_code=403)

    _ensure_safety_ack_columns(db)
    _ensure_deleted_at_column(db)
    from sqlalchemy.orm import joinedload
    employees = db.query(Employee).filter(Employee.deleted_at.is_(None)).order_by(Employee.name).all()
    # Check if schedule column exists to avoid 500 before migration runs
    col_exists = False
    try:
        exists_sql = text("SELECT 1 FROM information_schema.columns WHERE table_name='reviews' AND column_name='employee_scheduled_at'")
        col_exists = db.execute(exists_sql).first() is not None
    except Exception:
        col_exists = False
    # Auto-migrate if missing
    if not col_exists:
        try:
            db.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS employee_scheduled_at TIMESTAMP NULL"))
            db.commit()
            col_exists = True
        except Exception:
            db.rollback()
    rows = []
    for emp in employees:
        r = db.query(Review).options(
            load_only(
                Review.id,
                Review.employee_id,
                Review.supervisor_id,
                Review.employee_answers,
                Review.supervisor_answers,
                Review.director_comments,
                Review.status,
                Review.created_at,
                Review.updated_at,
            ),
            joinedload(Review.employee),
        ).filter_by(employee_id=emp.id).first()
        employee_done = bool(r and r.employee_answers)
        supervisor_done = bool(r and r.supervisor_answers)
        director_done = bool(r and r.director_comments)
        # Email tracking
        has_sent = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="sent").first() is not None
        has_clicked = db.query(EmailEvent).filter_by(employee_id=emp.id, event_type="clicked").first() is not None
        sched_display = None
        sched_value = ""
        if col_exists and r:
            try:
                # Load schedule lazily via direct SQL to avoid selecting missing column elsewhere
                srow = db.execute(
                    text("SELECT employee_scheduled_at FROM reviews WHERE id = CAST(:id AS uuid)"),
                    {"id": str(r.id)},
                ).first()
                if srow and srow[0]:
                    sched_display = srow[0].strftime("%Y-%m-%d %H:%M")
                    sched_value = srow[0].strftime("%Y-%m-%dT%H:%M")
            except Exception:
                pass
        rows.append({
            "employee": emp,
            "employee_done": employee_done,
            "supervisor_done": supervisor_done,
            "director_done": director_done,
            "has_sent": has_sent,
            "has_clicked": has_clicked,
            "self_scheduled_at_display": sched_display,
            "self_scheduled_at_value": sched_value,
        })
    all_names = [e.name for e in employees]

    # Calculate pending counts
    employee_pending = 0
    supervisor_pending = 0
    director_pending = 0

    for emp in employees:
        r = db.query(Review).options(
            load_only(
                Review.employee_id,
                Review.employee_answers,
                Review.supervisor_answers,
                Review.director_comments,
            )
        ).filter_by(employee_id=emp.id).first()

        # Employee pending: no employee_answers
        if not r or not r.employee_answers:
            employee_pending += 1

        # Supervisor pending: has employee_answers but no supervisor_answers
        # Only count if employee has a supervisor assigned
        if r and r.employee_answers and not r.supervisor_answers and emp.supervisor_email:
            supervisor_pending += 1

        # Director pending: has employee_answers and supervisor_answers but no director_comments
        if r and r.employee_answers and r.supervisor_answers and not r.director_comments:
            director_pending += 1

    return templates.TemplateResponse(request, "admin.html", {
        "rows": rows,
        "names": all_names,
        "allowed_roles": ["employee", "supervisor", "administration", "director"],
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
        "employee_pending": employee_pending,
        "supervisor_pending": supervisor_pending,
        "director_pending": director_pending,
    })'''

if old not in text:
    raise SystemExit("admin_page block not found")
path.write_text(text.replace(old, new), encoding="utf-8")
print("fixed admin_page")
