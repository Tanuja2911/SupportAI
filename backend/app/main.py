import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.routes import auth, knowledge, chat, conversations, analytics, widget, team, faq, ai_settings, knowledge_gaps

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(analytics.router)
app.include_router(widget.router)
app.include_router(team.router)
app.include_router(faq.router)
app.include_router(ai_settings.router)
app.include_router(knowledge_gaps.router)

app.mount("/widget", StaticFiles(directory="widget"), name="widget")

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}
