from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    admin,
    auth,
    chat,
    checkout,
    conferences,
    curate,
    events,
    health,
    me,
    webhooks,
)

settings = get_settings()

app = FastAPI(title="sidequest-api", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(conferences.router)
app.include_router(curate.router)
app.include_router(auth.router)
app.include_router(checkout.router)
app.include_router(me.router)
app.include_router(events.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(webhooks.router)
