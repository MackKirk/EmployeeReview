from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.routes import auth, employee, supervisor, director, home

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="changeme")

app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(supervisor.router)
app.include_router(director.router)
app.include_router(home.router)
