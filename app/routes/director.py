from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Employee, Review
from app.utils.auth_utils import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/director/review/{employee_id}", response_class=HTMLResponse)
async def director_view_review(request: Request, employee_id: str):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    review = db.query(Review).filter_by(employee_id=employee_id).first()
    if not current_user or current_user.role != "director":
        db.close()
        return HTMLResponse("Acesso restrito", status_code=403)
    if not employee or not review:
        db.close()
        return HTMLResponse("Funcionário ou avaliação não encontrada.", status_code=404)

    return templates.TemplateResponse("director_review.html", {
        "request": request,
        "employee": employee,
        "review": review
    })

@router.post("/director/review/{employee_id}/submit")
async def save_director_comments(
    request: Request, employee_id: str, director_comments: str = Form(...)
):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    review = db.query(Review).filter_by(employee_id=employee_id).first()
    if not current_user or current_user.role != "director":
        db.close()
        return HTMLResponse("Acesso restrito", status_code=403)
    if not review:
        db.close()
        return HTMLResponse("Avaliação não encontrada.", status_code=404)

    review.director_comments = director_comments
    db.commit()
    db.close()

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "message": "✅ Avaliação salva com sucesso!",
            "redirect_url": "/home",
            "seconds": 5,
        },
    )


@router.get("/director/dashboard", response_class=HTMLResponse)
async def director_dashboard(request: Request):
    current_user = get_current_user(request)
    db: Session = SessionLocal()
    if not current_user or current_user.role != "director":
        db.close()
        return HTMLResponse("Acesso restrito", status_code=403)

    from sqlalchemy.orm import joinedload
    reviews = db.query(Review).options(joinedload(Review.employee)).all()
    db.close()

    return templates.TemplateResponse("director_dashboard.html", {
        "request": request,
        "reviews": reviews
    })
