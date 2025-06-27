from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.routes import auth

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="changeme")

app.include_router(auth.router)
