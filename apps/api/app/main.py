from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, curate, events

settings = get_settings()

app = FastAPI(title="SideQuest API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(curate.router, prefix="/api", tags=["curate"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
