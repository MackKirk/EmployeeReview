from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from starlette.middleware.sessions import SessionMiddleware
import os
from app.routes import auth, employee, supervisor, director, home

app = FastAPI()
SESSION_SECRET = os.getenv("SESSION_SECRET", "changeme")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Garante que a pasta está montada corretamente
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(supervisor.router)
app.include_router(director.router)
app.include_router(home.router)
